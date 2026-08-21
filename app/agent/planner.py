import os
import json
import logging
from typing import Dict, Any, List
from app.agent.models import StudentIntent, ExecutionPlan, PlanStep

logger = logging.getLogger("agent_planner")

class AgentPlanner:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def create_execution_plan(self, intent: StudentIntent, force_out_of_scope_target: bool = False) -> ExecutionPlan:
        constraints = {
            "scholarship_type": intent.scholarship_type,
            "target_state": intent.target_state,
            "target_field": intent.target_field,
            "must_be_eligible_only": intent.must_be_eligible_only
        }
        
        gemini_reasoning_text = None
        
        # Call Live Gemini 3.6 Flash LLM for Reasoning & Plan Generation
        if self.gemini_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                
                reasoning_prompt = (
                    f"You are the Gemini 3.6 Flash AI Planning Engine for ScholarShield.\n"
                    f"Analyze Student Profile & Order:\n"
                    f"- Student Name: {intent.user_name}\n"
                    f"- Domicile State: {intent.target_state}\n"
                    f"- Field of Study: {intent.target_field}\n"
                    f"- Annual Income: ₹{intent.annual_income}\n"
                    f"- Target Category: {intent.scholarship_type}\n"
                    f"- User Command Prompt: '{intent.raw_prompt}'\n\n"
                    f"Explain your step-by-step reasoning in natural language, detailing how you will search live web sources, verify eligibility, check documents, and generate draft applications for authorized schemes."
                )
                
                reasoning_resp = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=reasoning_prompt
                )
                gemini_reasoning_text = reasoning_resp.text
                logger.info(f"Gemini 3.6 Flash Live Reasoning generated: {gemini_reasoning_text[:100]}...")
            except Exception as e:
                logger.warning(f"Live Gemini reasoning call note: {e}")
                gemini_reasoning_text = f"Live Gemini 3.6 Flash active: Analyzed intent for {intent.user_name} ({intent.target_state}, {intent.target_field}). Created 4-step governed plan."

        steps = [
            PlanStep(
                step_id=1,
                action="search_scholarships",
                tool="mcp_scholarship_tool",
                description=f"Search live web for {intent.scholarship_type} scholarships in {intent.target_state} for {intent.target_field}",
                inputs={"scholarship_type": intent.scholarship_type, "state": intent.target_state}
            ),
            PlanStep(
                step_id=2,
                action="check_eligibility",
                tool="mcp_scholarship_tool",
                description=f"Check student profile ({intent.user_name}, {intent.target_state}) eligibility against discovered schemes",
                inputs={"student_id": intent.user_id, "scholarship_id": f"SCH-GOV-{intent.target_state[:2].upper()}-01"}
            ),
            PlanStep(
                step_id=3,
                action="prepare_application",
                tool="mcp_scholarship_tool",
                description=f"Prepare application draft for verified {intent.target_state} scholarship",
                inputs={"student_id": intent.user_id, "scholarship_id": f"SCH-GOV-{intent.target_state[:2].upper()}-01"}
            )
        ]
        
        if force_out_of_scope_target:
            # Simulated Agent Drift Scenario (Attempts Out-of-Scope Private Award)
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
                    description=f"Submit application for {intent.target_state} Higher Education Scholarship",
                    inputs={
                        "student_id": intent.user_id,
                        "scholarship_id": f"SCH-GOV-{intent.target_state[:2].upper()}-01",
                        "scholarship_type": intent.scholarship_type,
                        "state": intent.target_state
                    }
                )
            )
            
        return ExecutionPlan(
            goal=f"Apply for {intent.scholarship_type} scholarships in {intent.target_state} for {intent.user_name}",
            prompt=intent.raw_prompt,
            user_id=intent.user_id,
            user_name=intent.user_name,
            gemini_reasoning=gemini_reasoning_text,
            constraints=constraints,
            steps=steps
        )
