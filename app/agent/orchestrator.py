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

from app.tools.live_web_search import (
    LiveWebScholarshipSearchTool,
)


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

        self.tools = (
            tools
            or ScholarshipMCPTools(
                armoriq_client=self.armoriq
            )
        )

        self.planner = AgentPlanner()

        self.web_search_tool = (
            LiveWebScholarshipSearchTool()
        )


    def run_agent_workflow(
        self,
        intent: StudentIntent,
        simulate_out_of_scope_violation: bool = False,
        simulate_missing_document: bool = False,
    ) -> AgentRunSummary:

        # =====================================================
        # 1. LIVE SCHOLARSHIP DISCOVERY
        #
        # IMPORTANT:
        # This happens BEFORE ArmorIQ capture_plan().
        # =====================================================

        discovered_scholarships = []

        try:

            discovered_scholarships = (
                self.web_search_tool.search_live_web(
                    query=intent.raw_prompt,
                    state=intent.target_state,
                    field=intent.target_field,
                    scholarship_type=intent.scholarship_type,
                )
            )

        except Exception as exc:

            discovered_scholarships = []

            print(
                f"Live scholarship search failed: {exc}"
            )


        # =====================================================
        # 2. SELECT FINAL SCHOLARSHIP
        # =====================================================

        selected_scholarship = None

        if discovered_scholarships:

            for scholarship in discovered_scholarships:

                if not isinstance(
                    scholarship,
                    dict,
                ):
                    continue

                # ---------------------------------------------
                # Match scholarship type
                # ---------------------------------------------

                if (
                    scholarship.get(
                        "scholarship_type"
                    )
                    != intent.scholarship_type
                ):
                    continue

                # ---------------------------------------------
                # Match state
                # ---------------------------------------------

                eligible_states = (
                    scholarship.get(
                        "eligible_states"
                    )
                    or []
                )

                if eligible_states:

                    if (
                        intent.target_state
                        not in eligible_states
                        and "All India"
                        not in eligible_states
                    ):
                        continue

                selected_scholarship = scholarship

                break


        # -----------------------------------------------------
        # Fallback
        # -----------------------------------------------------

        if selected_scholarship is None:

            if discovered_scholarships:

                for scholarship in discovered_scholarships:

                    if isinstance(
                        scholarship,
                        dict,
                    ):

                        selected_scholarship = scholarship
                        break


        # =====================================================
        # 3. DETERMINE FINAL SCHOLARSHIP ID
        # =====================================================

        if selected_scholarship:

            selected_scholarship_id = (
                selected_scholarship.get(
                    "scholarship_id"
                )
            )

            selected_scholarship_type = (
                selected_scholarship.get(
                    "scholarship_type"
                )
                or intent.scholarship_type
            )

            selected_scholarship_state = (
                intent.target_state
            )

        else:

            selected_scholarship_id = (
                f"SCH-GOV-"
                f"{intent.target_state[:2].upper()}"
                f"-01"
            )

            selected_scholarship_type = (
                intent.scholarship_type
            )

            selected_scholarship_state = (
                intent.target_state
            )


        # =====================================================
        # 4. CREATE FINAL PLAN
        #
        # The selected scholarship ID is now embedded in the
        # plan BEFORE ArmorIQ sees it.
        # =====================================================

        plan = self.planner.create_execution_plan(
            intent,
            force_out_of_scope_target=(
                simulate_out_of_scope_violation
            ),
            scholarship_id=selected_scholarship_id,
            scholarship_type=selected_scholarship_type,
            scholarship_state=selected_scholarship_state,
        )


        # =====================================================
        # 5. CAPTURE FINAL PLAN WITH ARMORIQ
        # =====================================================

        captured_plan = self.armoriq.capture_plan(
            llm="gemini-3.6-flash",
            prompt=intent.raw_prompt,
            plan=plan.dict(),
        )


        # =====================================================
        # 6. GET REAL INTENT TOKEN
        # =====================================================

        intent_token = None
        telemetry = None

        get_token_fn = getattr(
            self.armoriq,
            "get_intent_token",
            None,
        )

        if callable(get_token_fn):

            try:

                intent_token = get_token_fn(
                    captured_plan,
                    validity_seconds=300,
                )

            except TypeError:

                intent_token = get_token_fn(
                    captured_plan
                )


        # -----------------------------------------------------
        # IMPORTANT:
        # Do NOT use token_string.
        # Your new client returns the actual token object.
        # -----------------------------------------------------

        if intent_token is None:

            telemetry = (
                self.armoriq.get_intent_token_details(
                    captured_plan,
                    validity_seconds=300,
                )
            )

            intent_token = telemetry.get(
                "token"
            )


        # -----------------------------------------------------
        # Get telemetry separately
        # -----------------------------------------------------

        if telemetry is None:

            try:

                telemetry = (
                    self.armoriq.get_intent_token_details(
                        captured_plan,
                        validity_seconds=300,
                    )
                )

            except Exception:

                telemetry = None


        # =====================================================
        # 7. EXECUTE EXACT SIGNED PLAN
        # =====================================================

        step_results: List[
            WorkflowStepResult
        ] = []

        completed_count = 0
        blocked_count = 0


        for step in plan.steps:

            action = step.action

            # -------------------------------------------------
            # CRITICAL:
            #
            # These inputs came from the FINAL PLAN.
            #
            # NEVER modify them after capture_plan().
            # -------------------------------------------------

            inputs = dict(
                step.inputs
            )


            try:

                # =================================================
                # ARMORIQ GOVERNANCE
                # =================================================

                governance_res = (
                    self.armoriq.invoke(
                        mcp=step.tool,
                        action=action,
                        intent_token=intent_token,
                        params=inputs,
                        user_email=(
                            f"{intent.user_id}"
                            "@scholarshield.local"
                        ),
                    )
                )


                armoriq_decision = (
                    governance_res.get(
                        "decision",
                        "BLOCK",
                    )
                )


                # =================================================
                # ARMORIQ BLOCK
                # =================================================

                if armoriq_decision != "ALLOW":

                    blocked_count += 1

                    step_results.append(
                        WorkflowStepResult(
                            step_id=step.step_id,
                            action=action,
                            status="BLOCKED",
                            armoriq_decision=(
                                armoriq_decision
                            ),
                            executed=False,
                            details={
                                "mcp_invoked": False,
                                "protected_action_executed": False,
                                "inputs": inputs,
                                "reason": (
                                    governance_res.get(
                                        "error"
                                    )
                                    or
                                    "ArmorIQ denied "
                                    "the action."
                                ),
                            },
                            error_message=(
                                governance_res.get(
                                    "error"
                                )
                                or
                                "ArmorIQ denied "
                                "the action."
                            ),
                        )
                    )

                    # SECURITY BOUNDARY:
                    #
                    # Never execute the protected action
                    # after ArmorIQ denies it.

                    continue


                # =================================================
                # STEP 1 — SEARCH
                # =================================================

                if action == "search_scholarships":

                    # We already performed live discovery before
                    # ArmorIQ plan capture.
                    #
                    # Do NOT perform a second discovery that could
                    # change the signed plan.

                    tool_out = {
                        "tool": "search_scholarships",
                        "search_type": (
                            "LIVE_INTERNET_SEARCH"
                        ),
                        "discovered_count": len(
                            discovered_scholarships
                        ),
                        "scholarships": (
                            discovered_scholarships
                        ),
                    }


                # =================================================
                # STEP 2 — ELIGIBILITY
                # =================================================

                elif action == "check_eligibility":

                    tool_out = (
                        self.tools.check_eligibility(
                            student_id=inputs[
                                "student_id"
                            ],
                            scholarship_id=inputs[
                                "scholarship_id"
                            ],
                        )
                    )


                    # ------------------------------------------------
                    # DEMO: missing document
                    # ------------------------------------------------

                    if (
                        simulate_missing_document
                        and not tool_out[
                            "result"
                        ].get(
                            "missing_documents"
                        )
                    ):

                        tool_out[
                            "result"
                        ][
                            "missing_documents"
                        ] = [
                            "income_certificate.pdf"
                        ]

                        tool_out[
                            "result"
                        ][
                            "action_required"
                        ] = (
                            "DEMAND_DOCUMENT"
                        )


                # =================================================
                # STEP 3 — PREPARE APPLICATION
                # =================================================

                elif action == "prepare_application":

                    tool_out = (
                        self.tools.prepare_application(
                            student_id=inputs[
                                "student_id"
                            ],
                            scholarship_id=inputs[
                                "scholarship_id"
                            ],
                        )
                    )


                # =================================================
                # STEP 4 — SUBMIT APPLICATION
                # =================================================

                elif action == "submit_application":

                    # ------------------------------------------------
                    # Defense-in-depth:
                    #
                    # submission must correspond to the SAME
                    # scholarship checked in step 2.
                    # ------------------------------------------------

                    scholarship_id = inputs[
                        "scholarship_id"
                    ]

                    eligible = False

                    for previous in step_results:

                        if (
                            previous.action
                            == "check_eligibility"
                        ):

                            result = (
                                previous.details.get(
                                    "result"
                                )
                            )

                            if not result:
                                continue

                            previous_id = (
                                result.get(
                                    "scholarship_id"
                                )
                            )

                            if (
                                previous_id
                                == scholarship_id
                            ):

                                eligible = bool(
                                    result.get(
                                        "is_eligible",
                                        False,
                                    )
                                )

                                break


                    if not eligible:

                        raise IntentMismatchException(
                            "Cannot submit application: "
                            "the exact scholarship in the "
                            "signed plan was not verified "
                            "as eligible."
                        )


                    tool_out = (
                        self.tools.submit_application(
                            student_id=inputs[
                                "student_id"
                            ],
                            scholarship_id=(
                                inputs[
                                    "scholarship_id"
                                ]
                            ),
                            intent_token=intent_token,
                            armoriq_decision="ALLOW",
                        )
                    )


                else:

                    tool_out = {
                        "status": "unknown_action"
                    }


                # =================================================
                # SUCCESS
                # =================================================

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


            # =====================================================
            # INTENT MISMATCH
            # =====================================================

            except IntentMismatchException as exc:

                blocked_count += 1

                step_results.append(
                    WorkflowStepResult(
                        step_id=step.step_id,
                        action=action,
                        status="BLOCKED",
                        armoriq_decision="BLOCK",
                        executed=False,
                        details={
                            "error": str(exc),
                            "inputs": inputs,
                            "mcp_invoked": False,
                            "protected_action_executed": False,
                        },
                        error_message=str(exc),
                    )
                )


            # =====================================================
            # ARMORIQ ERROR
            # =====================================================

            except ArmorIQException as exc:

                blocked_count += 1

                step_results.append(
                    WorkflowStepResult(
                        step_id=step.step_id,
                        action=action,
                        status="BLOCKED",
                        armoriq_decision="BLOCK",
                        executed=False,
                        details={
                            "error": str(exc),
                            "inputs": inputs,
                            "mcp_invoked": False,
                            "protected_action_executed": False,
                        },
                        error_message=str(exc),
                    )
                )


        # =====================================================
        # 8. PROOF OF NON-EXECUTION
        # =====================================================

        proof_res = {
            "proof_valid": False,
            "note": (
                "Unable to verify proof endpoint."
            ),
        }

        try:

            with httpx.Client(
                timeout=5.0
            ) as http_client:

                response = http_client.get(
                    "http://127.0.0.1:8001/"
                    "api/proof-of-non-execution"
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


        # =====================================================
        # 9. FINAL STATUS
        # =====================================================

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