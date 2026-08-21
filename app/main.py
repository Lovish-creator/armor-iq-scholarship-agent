import uvicorn
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.agent.models import StudentIntent, AgentRunSummary
from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.scholarship.service import ScholarshipService

app = FastAPI(
    title="Intent-Governed Scholarship Agent Service",
    description="Main Backend orchestrating student intent, ArmorIQ governance, and MCP tool execution",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ScholarshipAgentOrchestrator()
service = ScholarshipService()

class WorkflowRunRequest(BaseModel):
    student_name: str = "Gurpreet Singh"
    raw_prompt: str = "Find government engineering scholarships in Punjab I am eligible for and apply."
    scholarship_type: str = "government"
    target_state: str = "Punjab"
    target_field: str = "Engineering"
    annual_income: int = 450000
    simulate_out_of_scope_violation: bool = False
    simulate_missing_document: bool = False

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Intent-Governed Autonomous Scholarship Application Agent",
        "governance_engine": "ArmorIQ Intent Engine",
        "endpoints": {
            "run_workflow": "/api/agent/run",
            "audit_logs": "/api/audit-logs",
            "proof_of_non_execution": "/api/proof-of-non-execution"
        }
    }

@app.post("/api/agent/run", response_model=AgentRunSummary)
def run_agent_workflow(req: WorkflowRunRequest):
    # Dynamically register user identity in database for the entered state & name!
    try:
        with httpx.Client(timeout=5.0) as http_client:
            http_client.post(
                "http://127.0.0.1:8001/api/student/register",
                json={
                    "student_id": "student-demo-001",
                    "name": req.student_name,
                    "education": req.target_field,
                    "state": req.target_state,
                    "annual_income": req.annual_income,
                    "category": "General"
                }
            )
    except Exception as e:
        pass

    intent = StudentIntent(
        intent_id=f"intent-{req.target_state.lower().replace(' ', '-')}",
        user_id="student-demo-001",
        user_name=req.student_name,
        raw_prompt=req.raw_prompt,
        scholarship_type=req.scholarship_type,
        target_state=req.target_state,
        target_field=req.target_field,
        annual_income=req.annual_income
    )
    
    summary = orchestrator.run_agent_workflow(
        intent=intent,
        simulate_out_of_scope_violation=req.simulate_out_of_scope_violation,
        simulate_missing_document=req.simulate_missing_document
    )
    return summary

@app.get("/api/scholarships")
def list_scholarships(scholarship_type: Optional[str] = None, state: Optional[str] = None):
    try:
        items = service.search_scholarships(scholarship_type=scholarship_type, state=state)
        return [i.dict() for i in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
