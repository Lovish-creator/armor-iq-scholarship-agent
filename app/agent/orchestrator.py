from typing import List, Optional

import httpx

from app.agent.models import (
    StudentIntent,
    WorkflowStepResult,
    AgentRunSummary,
)

from app.agent.planner import AgentPlanner

from app.armoriq.client import ArmorIQWrapperClient

from app.armoriq.errors import (
    IntentMismatchException,
    ArmorIQException,
)

from app.tools.scholarship_tools import ScholarshipMCPTools

from app.tools.live_web_search import LiveWebScholarshipSearchTool


class ScholarshipAgentOrchestrator:

    def __init__(
        self,
        armoriq_client: Optional[ArmorIQWrapperClient] = None,
        tools: Optional[ScholarshipMCPTools] = None,
    ):

        self.armoriq = (
            armoriq_client
            or ArmorIQWrapperClient()
        )

        # Inject ArmorIQ client into the MCP tools so they can perform
        # authoritative verification (defense-in-depth) before executing
        # consequential protected actions.
        self.tools = (
            tools
            or ScholarshipMCPTools(armoriq_client=self.armoriq)
        )

        self.planner = AgentPlanner()

        self.web_search_tool = LiveWebScholarshipSearchTool()

    def run_agent_workflow(
        self,
        intent: StudentIntent,
        simulate_out_of_scope_violation: bool = False,
        simulate_missing_document: bool = False,
    ) -> AgentRunSummary:

        # ---------------------------------------------------------
        # 1. Create execution plan
        # ---------------------------------------------------------

        plan = self.planner.create_execution_plan(
            intent,
            force_out_of_scope_target=simulate_out_of_scope_violation,
        )

        # ---------------------------------------------------------
        # 2. Capture plan through ArmorIQ
        # ---------------------------------------------------------

        captured_plan = self.armoriq.capture_plan(
            llm="gemini-3.6-flash",
            prompt=intent.raw_prompt,
            plan=plan.dict(),
        )

        # ---------------------------------------------------------
        # 3. Obtain REAL ArmorIQ intent token
        # ---------------------------------------------------------

        telemetry = self.armoriq.get_intent_token_details(
            captured_plan,
            validity_seconds=300,
        )

        intent_token = telemetry["token_string"]

        # ---------------------------------------------------------
        # 4. Execute workflow
        # ---------------------------------------------------------

        step_results: List[WorkflowStepResult] = []

        completed_count = 0
        blocked_count = 0

        for step in plan.steps:

            action = step.action
            inputs = step.inputs

            try:

                # -------------------------------------------------
                # ARMORIQ GOVERNANCE
                # -------------------------------------------------

                governance_res = self.armoriq.invoke(
                    mcp=step.tool,
                    action=action,
                    intent_token=intent_token,
                    params=inputs,
                    user_email=f"{intent.user_id}@scholarshield.local",
                )

                armoriq_decision = governance_res.get(
                    "decision",
                    "ALLOW",
                )

                # -------------------------------------------------
                # HARD SECURITY BOUNDARY
                # -------------------------------------------------

                if armoriq_decision != "ALLOW":

                    blocked_count += 1

                    step_results.append(
                        WorkflowStepResult(
                            step_id=step.step_id,
                            action=action,
                            status="BLOCKED",
                            armoriq_decision=armoriq_decision,
                            executed=False,
                            details={
                                "mcp_invoked": False,
                                "protected_action_executed": False,
                                "reason": (
                                    "ArmorIQ did not authorize "
                                    "this action."
                                ),
                            },
                            error_message=(
                                "ArmorIQ denied the action."
                            ),
                        )
                    )

                    # VERY IMPORTANT:
                    # NEVER call the protected tool here.

                    continue

                # -------------------------------------------------
                # ALLOWED ACTIONS
                # -------------------------------------------------

                if action == "search_scholarships":

                    live_web_results = (
                        self.web_search_tool.search_live_web(
                            query=intent.raw_prompt,
                            state=intent.target_state,
                            field=intent.target_field,
                            scholarship_type=intent.scholarship_type,
                        )
                    )

                    tool_out = {
                        "tool": "search_scholarships",
                        "search_type": "LIVE_INTERNET_SEARCH",
                        "discovered_count": len(
                            live_web_results
                        ),
                        "scholarships": live_web_results,
                    }

                elif action == "check_eligibility":

                    eligibility_res = (
                        self.tools.check_eligibility(
                            student_id=inputs["student_id"],
                            scholarship_id=inputs["scholarship_id"],
                        )
                    )

                    tool_out = eligibility_res

                    if (
                        simulate_missing_document
                        and not eligibility_res["result"].get(
                            "missing_documents"
                        )
                    ):

                        eligibility_res["result"][
                            "missing_documents"
                        ] = [
                            "income_certificate.pdf"
                        ]

                        eligibility_res["result"][
                            "action_required"
                        ] = "DEMAND_DOCUMENT"

                elif action == "prepare_application":

                    tool_out = (
                        self.tools.prepare_application(
                            student_id=inputs["student_id"],
                            scholarship_id=inputs["scholarship_id"],
                        )
                    )

                elif action == "submit_application":

                    # -------------------------------------------------
                    # CRITICAL:
                    # This code can only be reached after ArmorIQ
                    # returned ALLOW.
                    # -------------------------------------------------

                    tool_out = (
                        self.tools.submit_application(
                            student_id=inputs["student_id"],
                            scholarship_id=inputs["scholarship_id"],
                            intent_token=intent_token,
                            armoriq_decision="ALLOW",
                        )
                    )

                else:

                    tool_out = {
                        "status": "unknown_action"
                    }

                # -------------------------------------------------
                # SUCCESS
                # -------------------------------------------------

                step_results.append(
                    WorkflowStepResult(
                        step_id=step.step_id,
                        action=action,
                        status="SUCCESS",
                        armoriq_decision="ALLOW",
                        executed=True,
                        details=tool_out,
                    )
                )

                completed_count += 1

            # -----------------------------------------------------
            # ARMORIQ INTENT MISMATCH
            # -----------------------------------------------------

            except IntentMismatchException as e:

                blocked_count += 1

                # CRITICAL:
                # DO NOT CALL submit_application HERE.
                #
                # ArmorIQ denied the action.
                # Therefore the protected MCP/tool must not execute.

                step_results.append(
                    WorkflowStepResult(
                        step_id=step.step_id,
                        action=action,
                        status="BLOCKED",
                        armoriq_decision="BLOCK",
                        executed=False,
                        details={
                            "error": str(e),
                            "inputs": inputs,
                            "mcp_invoked": False,
                            "protected_action_executed": False,
                        },
                        error_message=str(e),
                    )
                )

            # -----------------------------------------------------
            # ARMORIQ ERROR
            # -----------------------------------------------------

            except ArmorIQException as e:

                blocked_count += 1

                step_results.append(
                    WorkflowStepResult(
                        step_id=step.step_id,
                        action=action,
                        status="BLOCKED",
                        armoriq_decision="BLOCK",
                        executed=False,
                        details={
                            "error": str(e),
                            "inputs": inputs,
                            "mcp_invoked": False,
                            "protected_action_executed": False,
                        },
                        error_message=str(e),
                    )
                )

        # ---------------------------------------------------------
        # 5. Verify non-execution
        # ---------------------------------------------------------

        proof_res = {
            "proof_valid": False,
            "note": "Unable to verify proof endpoint.",
        }

        try:

            with httpx.Client(timeout=5.0) as http_client:

                response = http_client.get(
                    "http://127.0.0.1:8001/api/proof-of-non-execution"
                )

                if response.status_code == 200:
                    proof_res = response.json()

        except Exception as exc:

            proof_res = {
                "proof_valid": False,
                "note": (
                    "Proof endpoint unavailable."
                ),
                "error": str(exc),
            }

        # ---------------------------------------------------------
        # 6. Final status
        # ---------------------------------------------------------

        run_status = (
            "COMPLETED"
            if blocked_count == 0
            else "PARTIAL_BLOCKED"
        )

        return AgentRunSummary(
            intent_id=intent.intent_id,
            user_id=intent.user_id,
            user_name=intent.user_name,
            status=run_status,
            total_steps=len(plan.steps),
            completed_steps=completed_count,
            blocked_steps=blocked_count,
            intent_token=intent_token,
            gemini_reasoning=plan.gemini_reasoning,
            armoriq_telemetry=telemetry,
            step_results=step_results,
            proof_of_non_execution=proof_res,
        )
