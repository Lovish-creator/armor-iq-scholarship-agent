import uvicorn
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
    raw_prompt: str = "Find government engineering scholarships in Punjab I am eligible for and apply."
    scholarship_type: str = "government"
    target_state: str = "Punjab"
    target_field: str = "Engineering"
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
    intent = StudentIntent(
        intent_id=f"intent-demo-{req.scholarship_type}-{req.target_state.lower()}",
        user_id="student-demo-001",
        raw_prompt=req.raw_prompt,
        scholarship_type=req.scholarship_type,
        target_state=req.target_state,
        target_field=req.target_field
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
