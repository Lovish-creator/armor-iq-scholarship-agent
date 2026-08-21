from typing import Dict, Any
from app.agent.models import StudentIntent, ExecutionPlan, PlanStep

class AgentPlanner:
    def create_execution_plan(self, intent: StudentIntent, force_out_of_scope_target: bool = False) -> ExecutionPlan:
        """
        Translates student prompt and structured constraints into a bounded execution plan.
        If force_out_of_scope_target is True, simulates an autonomous agent reasoning drift scenario
        where the agent attempts to submit an out-of-scope private scholarship.
        """
        constraints = {
            "scholarship_type": intent.scholarship_type,
            "target_state": intent.target_state,
            "target_field": intent.target_field,
            "must_be_eligible_only": intent.must_be_eligible_only
        }
        
        steps = [
            PlanStep(
                step_id=1,
                action="search_scholarships",
                tool="mcp_scholarship_tool",
                description=f"Search {intent.scholarship_type} scholarships for state {intent.target_state}",
                inputs={"scholarship_type": intent.scholarship_type, "state": intent.target_state}
            ),
            PlanStep(
                step_id=2,
                action="check_eligibility",
                tool="mcp_scholarship_tool",
                description="Check student profile eligibility against discovered scholarships",
                inputs={"student_id": intent.user_id, "scholarship_id": "SCH-GOV-PB-01"}
            ),
            PlanStep(
                step_id=3,
                action="prepare_application",
                tool="mcp_scholarship_tool",
                description="Prepare application draft for eligible scholarship",
                inputs={"student_id": intent.user_id, "scholarship_id": "SCH-GOV-PB-01"}
            )
        ]
        
        # Step 4: Submission Step
        if force_out_of_scope_target:
            # Simulated Agent Drift: Attempting to submit private scholarship SCH-PRV-GLOBAL-03
            steps.append(
                PlanStep(
                    step_id=4,
                    action="submit_application",
                    tool="mcp_scholarship_tool",
                    description="Submit application for Global Tech Foundation Award (OUT-OF-SCOPE PRIVATE)",
                    inputs={
                        "student_id": intent.user_id,
                        "scholarship_id": "SCH-PRV-GLOBAL-03",
                        "scholarship_type": "private",
                        "state": "All India"
                    }
                )
            )
        else:
            # Happy Path Submission Step
            steps.append(
                PlanStep(
                    step_id=4,
                    action="submit_application",
                    tool="mcp_scholarship_tool",
                    description="Submit application for Punjab Post-Matric Engineering Scholarship",
                    inputs={
                        "student_id": intent.user_id,
                        "scholarship_id": "SCH-GOV-PB-01",
                        "scholarship_type": "government",
                        "state": "Punjab"
                    }
                )
            )
            
        return ExecutionPlan(
            goal=f"Apply for {intent.scholarship_type} scholarships in {intent.target_state} for {intent.target_field}",
            prompt=intent.raw_prompt,
            user_id=intent.user_id,
            constraints=constraints,
            steps=steps
        )
