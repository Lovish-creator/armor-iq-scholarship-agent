import os
import json
import logging
from typing import Dict, Any, List
from app.agent.models import StudentIntent, ExecutionPlan, PlanStep

logger = logging.getLogger("agent_planner")

class AgentPlanner:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def create_execution_plan(self, intent: StudentIntent, force_out_of_scope_target: bool = False) -> ExecutionPlan:
        """
        Translates natural language student prompt and constraints into a bounded execution plan.
        Supports live LLM reasoning (Gemini/OpenAI) when API keys are configured.
        """
        constraints = {
            "scholarship_type": intent.scholarship_type,
            "target_state": intent.target_state,
            "target_field": intent.target_field,
            "must_be_eligible_only": intent.must_be_eligible_only
        }
        
        # Try Live LLM Execution Plan Generation via Gemini 3.6 Flash if API Key available
        if self.gemini_key:
            try:
                plan_from_llm = self._generate_plan_via_gemini(intent, force_out_of_scope_target)
                if plan_from_llm:
                    return plan_from_llm
            except Exception as e:
                logger.warning(f"Live Gemini planning note: {e}. Using structured planner engine.")

        # Structured Planner Engine
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
        
        if force_out_of_scope_target:
            # Simulated Agent Drift Scenario
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
            # Authorized Happy Path Scenario
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

    def _generate_plan_via_gemini(self, intent: StudentIntent, force_out_of_scope: bool) -> ExecutionPlan:
        from google import genai
        client = genai.Client(api_key=self.gemini_key)
        
        prompt = (
            f"You are an AI Agent Planner for a Scholarship Application System.\n"
            f"Student Prompt: '{intent.raw_prompt}'\n"
            f"Authorized Target Type: '{intent.scholarship_type}'\n"
            f"Authorized State: '{intent.target_state}'\n\n"
            f"Formulate a JSON object with fields 'goal' and 'steps'. Each step has 'action', 'description', 'inputs'.\n"
            f"Allowed actions: search_scholarships, check_eligibility, prepare_application, submit_application."
        )
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        
        data = json.loads(response.text)
        steps_data = data.get("steps", [])
        
        steps = []
        for idx, s in enumerate(steps_data):
            steps.append(PlanStep(
                step_id=idx+1,
                action=s.get("action", "search_scholarships"),
                tool="mcp_scholarship_tool",
                description=s.get("description", "Execute step"),
                inputs=s.get("inputs", {})
            ))
            
        if force_out_of_scope:
            steps.append(PlanStep(
                step_id=len(steps)+1,
                action="submit_application",
                tool="mcp_scholarship_tool",
                description="Submit application for Global Tech Foundation Award (OUT-OF-SCOPE PRIVATE)",
                inputs={
                    "student_id": intent.user_id,
                    "scholarship_id": "SCH-PRV-GLOBAL-03",
                    "scholarship_type": "private",
                    "state": "All India"
                }
            ))

        return ExecutionPlan(
            goal=data.get("goal", intent.raw_prompt),
            prompt=intent.raw_prompt,
            user_id=intent.user_id,
            constraints={
                "scholarship_type": intent.scholarship_type,
                "target_state": intent.target_state
            },
            steps=steps
        )
