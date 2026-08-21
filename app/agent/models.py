from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class StudentIntent(BaseModel):
    intent_id: str
    user_id: str = "student-demo-001"
    raw_prompt: str
    scholarship_type: str = "government"  # "government", "private", "all"
    target_state: str = "Punjab"
    target_field: str = "Engineering"
    must_be_eligible_only: bool = True
    requires_human_approval_before_submit: bool = True

class PlanStep(BaseModel):
    step_id: int
    action: str
    tool: str
    description: str
    inputs: Dict[str, Any]

class ExecutionPlan(BaseModel):
    goal: str
    prompt: str
    user_id: str
    constraints: Dict[str, Any]
    steps: List[PlanStep]

class WorkflowStepResult(BaseModel):
    step_id: int
    action: str
    status: str  # "SUCCESS", "BLOCKED", "FAILED"
    armoriq_decision: str  # "ALLOW", "BLOCK", "HOLD"
    executed: bool
    details: Dict[str, Any]
    error_message: Optional[str] = None

class AgentRunSummary(BaseModel):
    intent_id: str
    user_id: str
    status: str  # "COMPLETED", "PARTIAL_BLOCKED", "FAILED"
    total_steps: int
    completed_steps: int
    blocked_steps: int
    intent_token: Optional[str] = None
    step_results: List[WorkflowStepResult]
    proof_of_non_execution: Dict[str, Any]
