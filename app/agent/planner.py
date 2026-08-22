import os
import logging
from typing import Optional

from app.agent.models import (
    StudentIntent,
    ExecutionPlan,
    PlanStep,
)

logger = logging.getLogger("agent_planner")


class AgentPlanner:

    def __init__(self):
        self.gemini_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

    def create_execution_plan(
        self,
        intent: StudentIntent,
        force_out_of_scope_target: bool = False,
        scholarship_id: Optional[str] = None,
        scholarship_type: Optional[str] = None,
        scholarship_state: Optional[str] = None,
    ) -> ExecutionPlan:

        """
        Create the FINAL execution plan.

        IMPORTANT:
        scholarship_id must be selected BEFORE this plan is
        captured by ArmorIQ.

        After ArmorIQ signs this plan, the orchestrator must
        execute these exact inputs without changing them.
        """

        final_scholarship_id = (
            scholarship_id
            or f"SCH-GOV-{intent.target_state[:2].upper()}-01"
        )

        final_scholarship_type = (
            scholarship_type
            or intent.scholarship_type
        )

        final_state = (
            scholarship_state
            or intent.target_state
        )

        constraints = {
            "scholarship_type": final_scholarship_type,
            "target_state": final_state,
            "target_field": intent.target_field,
            "must_be_eligible_only": intent.must_be_eligible_only,
        }

        gemini_reasoning_text = None

        # =====================================================
        # GEMINI REASONING
        # =====================================================

        if self.gemini_key:

            try:

                from google import genai

                client = genai.Client(
                    api_key=self.gemini_key
                )

                reasoning_prompt = (
                    "You are the Gemini planning engine for "
                    "ScholarShield.\n\n"

                    "Analyze the student's scholarship request.\n\n"

                    f"- Student Name: {intent.user_name}\n"
                    f"- Domicile State: {intent.target_state}\n"
                    f"- Field of Study: {intent.target_field}\n"
                    f"- Annual Income: ₹{intent.annual_income}\n"
                    f"- Scholarship Type: {final_scholarship_type}\n"
                    f"- Selected Scholarship ID: "
                    f"{final_scholarship_id}\n"
                    f"- User Command: '{intent.raw_prompt}'\n\n"

                    "Explain the authorized workflow in natural "
                    "language, including scholarship discovery, "
                    "eligibility verification, document checks, "
                    "application preparation, and submission."
                )

                reasoning_resp = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=reasoning_prompt,
                )

                gemini_reasoning_text = (
                    reasoning_resp.text
                    if reasoning_resp
                    else None
                )

                if gemini_reasoning_text:
                    logger.info(
                        "Gemini reasoning generated: %s...",
                        gemini_reasoning_text[:100],
                    )

            except Exception as exc:

                logger.warning(
                    "Live Gemini reasoning failed: %s",
                    exc,
                )

                gemini_reasoning_text = None

        # =====================================================
        # STEP 1 — SEARCH
        # =====================================================

        steps = [

            PlanStep(
                step_id=1,
                action="search_scholarships",
                tool="mcp_scholarship_tool",
                description=(
                    f"Search for {final_scholarship_type} "
                    f"scholarships in {final_state} "
                    f"for {intent.target_field}"
                ),
                inputs={
                    "scholarship_type": final_scholarship_type,
                    "state": final_state,
                },
            ),

            # =================================================
            # STEP 2 — ELIGIBILITY
            # =================================================

            PlanStep(
                step_id=2,
                action="check_eligibility",
                tool="mcp_scholarship_tool",
                description=(
                    f"Check eligibility of student "
                    f"{intent.user_name} for "
                    f"{final_scholarship_id}"
                ),
                inputs={
                    "student_id": intent.user_id,
                    "scholarship_id": final_scholarship_id,
                },
            ),

            # =================================================
            # STEP 3 — PREPARE
            # =================================================

            PlanStep(
                step_id=3,
                action="prepare_application",
                tool="mcp_scholarship_tool",
                description=(
                    f"Prepare application for "
                    f"{final_scholarship_id}"
                ),
                inputs={
                    "student_id": intent.user_id,
                    "scholarship_id": final_scholarship_id,
                },
            ),
        ]

        # =====================================================
        # STEP 4 — SUBMISSION
        # =====================================================

        if force_out_of_scope_target:

            # -------------------------------------------------
            # DEMO: INTENT DRIFT
            #
            # This is intentionally unauthorized.
            # ArmorIQ SHOULD block this scenario.
            # -------------------------------------------------

            steps.append(
                PlanStep(
                    step_id=4,
                    action="submit_application",
                    tool="mcp_scholarship_tool",
                    description=(
                        "Attempt to submit an "
                        "out-of-scope private scholarship"
                    ),
                    inputs={
                        "student_id": intent.user_id,
                        "scholarship_id": "SCH-PRV-GLOBAL-03",
                        "scholarship_type": "private",
                        "state": "All India",
                    },
                )
            )

        else:

            steps.append(
                PlanStep(
                    step_id=4,
                    action="submit_application",
                    tool="mcp_scholarship_tool",
                    description=(
                        f"Submit application for "
                        f"{final_scholarship_id}"
                    ),
                    inputs={
                        "student_id": intent.user_id,
                        "scholarship_id": final_scholarship_id,
                        "scholarship_type": final_scholarship_type,
                        "state": final_state,
                    },
                )
            )

        # =====================================================
        # FINAL EXECUTION PLAN
        # =====================================================

        logger.info(
            "FINAL ARMORIQ PLAN: scholarship_id=%s",
            final_scholarship_id,
        )

        return ExecutionPlan(
            goal=(
                f"Apply for {final_scholarship_type} "
                f"scholarships in {final_state} "
                f"for {intent.user_name}"
            ),
            prompt=intent.raw_prompt,
            user_id=intent.user_id,
            user_name=intent.user_name,
            gemini_reasoning=gemini_reasoning_text,
            constraints=constraints,
            steps=steps,
        )