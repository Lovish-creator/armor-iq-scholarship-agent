from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import datetime
from mock_portal.database import get_db_connection

router = APIRouter()

class EligibilityCheckRequest(BaseModel):
    student_id: str
    scholarship_id: str

class ApplicationDraftRequest(BaseModel):
    student_id: str
    scholarship_id: str

class ApplicationSubmitRequest(BaseModel):
    application_id: str
    student_id: str
    scholarship_id: str
    intent_token: Optional[str] = None
    armoriq_decision: str = "ALLOW" # "ALLOW", "BLOCK", "HOLD"

@router.get("/api/student/{student_id}")
def get_student(student_id: str):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    conn.close()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    res = dict(student)
    res["documents"] = json.loads(res["documents_json"])
    del res["documents_json"]
    return res

@router.get("/api/scholarships")
def list_scholarships(scholarship_type: Optional[str] = None, state: Optional[str] = None):
    conn = get_db_connection()
    query = "SELECT * FROM scholarships WHERE 1=1"
    params = []
    
    if scholarship_type:
        query += " AND scholarship_type = ?"
        params.append(scholarship_type)
        
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    results = []
    for r in rows:
        item = dict(r)
        item["eligible_states"] = json.loads(item["eligible_states_json"])
        item["eligible_fields"] = json.loads(item["eligible_fields_json"])
        item["required_documents"] = json.loads(item["required_documents_json"])
        
        # Apply state filter if provided
        if state:
            if "All India" not in item["eligible_states"] and state not in item["eligible_states"]:
                continue
                
        results.append(item)
    return results

@router.get("/api/scholarships/{scholarship_id}")
def get_scholarship_details(scholarship_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM scholarships WHERE scholarship_id = ?", (scholarship_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Scholarship not found")
        
    item = dict(row)
    item["eligible_states"] = json.loads(item["eligible_states_json"])
    item["eligible_fields"] = json.loads(item["eligible_fields_json"])
    item["required_documents"] = json.loads(item["required_documents_json"])
    return item

@router.post("/api/eligibility/check")
def check_eligibility(req: EligibilityCheckRequest):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (req.student_id,)).fetchone()
    scholarship = conn.execute("SELECT * FROM scholarships WHERE scholarship_id = ?", (req.scholarship_id,)).fetchone()
    conn.close()
    
    if not student or not scholarship:
        raise HTTPException(status_code=404, detail="Student or Scholarship not found")
        
    st = dict(student)
    sc = dict(scholarship)
    eligible_states = json.loads(sc["eligible_states_json"])
    eligible_fields = json.loads(sc["eligible_fields_json"])
    
    reasons = []
    is_eligible = True
    
    # Check state
    if "All India" not in eligible_states and st["state"] not in eligible_states:
        is_eligible = False
        reasons.append(f"State mismatch: Student is from {st['state']}, scholarship requires {eligible_states}")
        
    # Check income
    if st["annual_income"] > sc["income_limit"]:
        is_eligible = False
        reasons.append(f"Income limit exceeded: Student income ₹{st['annual_income']} > Limit ₹{sc['income_limit']}")
        
    # Check field
    student_field_match = any(field.lower() in st["education"].lower() for field in eligible_fields)
    if not student_field_match:
        is_eligible = False
        reasons.append(f"Field mismatch: Student education '{st['education']}' does not match required fields {eligible_fields}")
        
    # Check CGPA
    if st["cgpa"] < sc["min_cgpa"]:
        is_eligible = False
        reasons.append(f"CGPA below limit: Student CGPA {st['cgpa']} < Required {sc['min_cgpa']}")
        
    return {
        "student_id": req.student_id,
        "scholarship_id": req.scholarship_id,
        "scholarship_name": sc["name"],
        "scholarship_type": sc["scholarship_type"],
        "is_eligible": is_eligible,
        "rejection_reasons": reasons
    }

@router.post("/api/applications/draft")
def prepare_application_draft(req: ApplicationDraftRequest):
    conn = get_db_connection()
    app_id = f"APP-{req.student_id}-{req.scholarship_id}"
    
    conn.execute("""
        INSERT OR REPLACE INTO applications (application_id, student_id, scholarship_id, status, applied_at)
        VALUES (?, ?, ?, ?, ?)
    """, (app_id, req.student_id, req.scholarship_id, "PREPARED", datetime.datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {
        "application_id": app_id,
        "student_id": req.student_id,
        "scholarship_id": req.scholarship_id,
        "status": "PREPARED",
        "message": "Application draft prepared and ready for governance verification."
    }

@router.post("/api/applications/submit")
def submit_application(req: ApplicationSubmitRequest):
    conn = get_db_connection()
    now_str = datetime.datetime.now().isoformat()
    
    # Check if ArmorIQ blocked the request
    if req.armoriq_decision != "ALLOW":
        # Log non-execution attempt!
        conn.execute("""
            INSERT INTO tool_execution_logs (timestamp, action, tool, target_scholarship_id, intent_token, armoriq_decision, executed, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, "submit_application", "mcp_scholarship_tool", req.scholarship_id, req.intent_token or "NONE", req.armoriq_decision, 0, f"Aborted: ArmorIQ governance decision was {req.armoriq_decision}"))
        conn.commit()
        conn.close()
        
        raise HTTPException(
            status_code=403, 
            detail=f"ArmorIQ Governance Violation: Submission aborted. Decision was {req.armoriq_decision}. Tool execution was BLOCKED and NOT executed."
        )

    # If ALLOWED, execute submission
    app_id = f"APP-{req.student_id}-{req.scholarship_id}"
    conn.execute("""
        INSERT OR REPLACE INTO applications (application_id, student_id, scholarship_id, status, intent_token, applied_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (app_id, req.student_id, req.scholarship_id, "SUBMITTED", req.intent_token or "TOKEN-APPROVED", now_str))
    
    # Log successful execution
    conn.execute("""
        INSERT INTO tool_execution_logs (timestamp, action, tool, target_scholarship_id, intent_token, armoriq_decision, executed, detail)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_str, "submit_application", "mcp_scholarship_tool", req.scholarship_id, req.intent_token or "TOKEN-APPROVED", "ALLOW", 1, "Application successfully submitted following intent token verification."))
    
    conn.commit()
    conn.close()
    
    return {
        "application_id": app_id,
        "status": "SUBMITTED",
        "armoriq_decision": "ALLOW",
        "executed": True,
        "message": "Application submitted successfully through ArmorIQ intent token governance."
    }

@router.get("/api/applications/{application_id}")
def get_application_status(application_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)

@router.get("/api/audit-logs")
def get_audit_logs():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tool_execution_logs ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/api/proof-of-non-execution")
def get_proof_of_non_execution():
    conn = get_db_connection()
    total_submissions = conn.execute("SELECT COUNT(*) FROM applications WHERE status = 'SUBMITTED'").fetchone()[0]
    blocked_attempts = conn.execute("SELECT COUNT(*) FROM tool_execution_logs WHERE armoriq_decision != 'ALLOW' AND executed = 0").fetchone()[0]
    executed_submissions = conn.execute("SELECT COUNT(*) FROM tool_execution_logs WHERE action = 'submit_application' AND executed = 1").fetchone()[0]
    conn.close()
    
    return {
        "total_portal_submitted_applications": total_submissions,
        "executed_tool_submissions": executed_submissions,
        "blocked_non_executed_attempts": blocked_attempts,
        "proof_valid": (total_submissions == executed_submissions)
    }
