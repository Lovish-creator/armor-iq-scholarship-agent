import os
import uvicorn
import httpx
from dotenv import load_dotenv

# Load environment variables before any other module initializations
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.agent.models import StudentIntent, AgentRunSummary
from app.agent.orchestrator import ScholarshipAgentOrchestrator
import os
# Optional test shim for local development without the official ArmorIQ SDK
TEST_SHIM_ENABLED = os.getenv("ARMORIQ_TEST_SHIM", "false").lower() in ("1", "true", "yes")
if TEST_SHIM_ENABLED:
    from app.armoriq.test_shim import FakeArmorIQShim  # type: ignore
from app.scholarship.service import ScholarshipService

# Single-port local mode: optionally mount the mock portal into the main app
SINGLE_PORT = os.getenv("SINGLE_PORT", "true").lower() in ("1", "true", "yes")
if SINGLE_PORT:
    try:
        from mock_portal.routes import router as mock_router
        from mock_portal.database import init_db as mock_init_db
    except Exception:
        mock_router = None
        mock_init_db = None

app = FastAPI(
    title="Intent-Governed Scholarship Agent Service",
    description="Main Backend orchestrating student intent, ArmorIQ governance, and MCP tool execution",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if TEST_SHIM_ENABLED:
    orchestrator = ScholarshipAgentOrchestrator(armoriq_client=FakeArmorIQShim())
else:
    orchestrator = ScholarshipAgentOrchestrator()

# Determine portal base URL. When running single-port locally, the portal
# endpoints are mounted on the same process at port 8000.
portal_base = os.getenv("PORTAL_BASE_URL", "http://127.0.0.1:8001")
if SINGLE_PORT:
    portal_base = os.getenv("SINGLE_PORT_BASE_URL", "http://127.0.0.1:8080")
service = ScholarshipService(base_url=portal_base)

# If single-port mode is enabled and the mock router is available, mount it
if SINGLE_PORT and mock_router is not None:
    app.include_router(mock_router)

    if mock_init_db is not None:
        @app.on_event("startup")
        def _init_mock_db():
            mock_init_db()

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
    return FileResponse(
        "frontend/index.html",
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.get("/styles.css")
def serve_styles():
    return FileResponse(
        "frontend/styles.css",
        media_type="text/css",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.get("/app.js")
def serve_app_js():
    return FileResponse(
        "frontend/app.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

@app.post("/api/agent/run", response_model=AgentRunSummary)
def run_agent_workflow(req: WorkflowRunRequest):
    try:
        if SINGLE_PORT and mock_router is not None:
            from mock_portal.routes import register_or_update_student as local_register, StudentRegisterRequest
            local_register(StudentRegisterRequest(
                student_id="student-demo-001",
                name=req.student_name,
                education=req.target_field,
                state=req.target_state,
                annual_income=req.annual_income,
                category="General"
            ))
        else:
            with httpx.Client(timeout=5.0) as http_client:
                http_client.post(
                    f"{portal_base}/api/student/register",
                    json={
                        "student_id": "student-demo-001",
                        "name": req.student_name,
                        "education": req.target_field,
                        "state": req.target_state,
                        "annual_income": req.annual_income,
                        "category": "General"
                    }
                )
    except Exception:
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
    
    try:
        summary = orchestrator.run_agent_workflow(
            intent=intent,
            simulate_out_of_scope_violation=req.simulate_out_of_scope_violation,
            simulate_missing_document=req.simulate_missing_document
        )
        return summary
    except HTTPException:
        raise
    except Exception as exc:
        err_msg = str(exc)
        exc_name = type(exc).__name__
        err_msg_lower = err_msg.lower()
        if (
            "invalid api key" in err_msg_lower
            or "invalid or expired api key" in err_msg_lower
            or "token issuance failed" in err_msg_lower
            or "invalidtokenexception" in exc_name.lower()
            or "configurationexception" in exc_name.lower()
        ):
            raise HTTPException(
                status_code=401,
                detail=f"ArmorIQ Authentication / Key Configuration Error: {err_msg}. Please check ARMORIQ_API_KEY in .env."
            )
        if "intentmismatchexception" in exc_name.lower():
            raise HTTPException(status_code=403, detail=f"ArmorIQ Intent Violation: {err_msg}")
        if "policyblockedexception" in exc_name.lower():
            raise HTTPException(status_code=403, detail=f"ArmorIQ Policy Blocked: {err_msg}")
        if "mcpinvocationexception" in exc_name.lower():
            raise HTTPException(status_code=502, detail=f"Scholarship MCP Server Unavailable or Failed: {err_msg}")
        raise HTTPException(status_code=500, detail=f"Agent Workflow Execution Error: {err_msg}")

@app.get("/api/scholarships")
def list_scholarships(scholarship_type: Optional[str] = None, state: Optional[str] = None):
    try:
        items = service.search_scholarships(scholarship_type=scholarship_type, state=state)
        return [i.dict() for i in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
@app.get("/healthz")
@app.get("/ping")
def health_check():
    return {"status": "ok", "service": "scholarshield", "armoriq": "active"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
