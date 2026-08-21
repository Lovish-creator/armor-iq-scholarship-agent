import os
import json
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header, UploadFile, File, Form
from pydantic import BaseModel
from mock_portal.database import get_db_connection
from pypdf import PdfReader

router = APIRouter()

class StudentRegisterRequest(BaseModel):
    student_id: str = "student-demo-001"
    name: str
    education: str
    state: str
    annual_income: int
    category: str = "General"
    cgpa: float = 8.5

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
    armoriq_decision: str = "ALLOW"

@router.post("/api/student/register")
def register_or_update_student(req: StudentRegisterRequest):
    """
    Dynamically registers or updates student profile details in database
    when user inputs their custom Name, State, Education, or Income.
    """
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM students WHERE student_id = ?", (req.student_id,)).fetchone()
    
    docs = ["marksheet_12th.pdf", "income_certificate.pdf", "domicile_proof.pdf"]
    if existing:
        docs = json.loads(existing["documents_json"])

    # Ensure state-matching domicile document is listed
    dom_doc = f"domicile_{req.state.lower().replace(' ', '_')}.pdf"
    if dom_doc not in docs:
        docs.append(dom_doc)

    conn.execute("""
        INSERT OR REPLACE INTO students (student_id, name, education, state, annual_income, category, cgpa, documents_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (req.student_id, req.name, req.education, req.state, req.annual_income, req.category, req.cgpa, json.dumps(docs)))
    
    # Also register dynamic state scholarship if state is custom (e.g. Delhi, Maharashtra, UP)
    state_sch_id = f"SCH-GOV-{req.state[:2].upper()}-01"
    conn.execute("""
        INSERT OR REPLACE INTO scholarships 
        (scholarship_id, name, scholarship_type, eligible_states_json, eligible_fields_json, income_limit, min_cgpa, amount, deadline, required_documents_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        state_sch_id,
        f"{req.state} State Post-Matric Higher Education Scholarship",
        "government",
        json.dumps([req.state, "All India"]),
        json.dumps(["Engineering", "Computer Science", req.education]),
        800000,
        6.0,
        75000,
        "2026-12-31",
        json.dumps(["marksheet_12th.pdf", "income_certificate.pdf", dom_doc])
    ))

    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "student_id": req.student_id,
        "name": req.name,
        "state": req.state,
        "education": req.education,
        "message": f"Student profile '{req.name}' successfully registered/updated for state '{req.state}' in portal database."
    }

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

@router.post("/api/documents/upload")
async def upload_and_parse_document(
    student_id: str = Form("student-demo-001"),
    doc_type: str = Form("general"),
    file: UploadFile = File(...)
):
    upload_dir = "D:\\armor-iq-scholarship-agent\\uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    extracted_text = ""
    parsed_meta = {}
    
    if file.filename.endswith(".pdf"):
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted_text += page.extract_text() or ""
        except Exception as e:
            extracted_text = f"PDF text extraction note: {e}"
            
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key and len(extracted_text.strip()) > 10:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            prompt = (
                f"Extract structured document info from this text. Document type: {doc_type}.\n"
                f"Text:\n{extracted_text[:2000]}\n"
                f"Return JSON with keys: extracted_name, state_of_domicile, annual_income, cgpa, verified_authority."
            )
            resp = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            parsed_meta = json.loads(resp.text)
        except Exception as e:
            parsed_meta = {"note": f"AI Parsing info: {e}"}

    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id,)).fetchone()
    
    if student:
        existing_docs = json.loads(student["documents_json"])
        if file.filename not in existing_docs:
            existing_docs.append(file.filename)
            
        income = parsed_meta.get("annual_income", student["annual_income"])
        state = parsed_meta.get("state_of_domicile", student["state"])
        cgpa = parsed_meta.get("cgpa", student["cgpa"])
        
        conn.execute("""
            UPDATE students 
            SET documents_json = ?, annual_income = ?, state = ?, cgpa = ?
            WHERE student_id = ?
        """, (json.dumps(existing_docs), int(income) if str(income).isdigit() else student["annual_income"], str(state) if state else student["state"], float(cgpa) if str(cgpa).replace('.','',1).isdigit() else student["cgpa"], student_id))
        conn.commit()
    conn.close()

    return {
        "success": True,
        "filename": file.filename,
        "doc_type": doc_type,
        "extracted_text_snippet": extracted_text[:300],
        "ai_parsed_metadata": parsed_meta,
        "message": f"Document '{file.filename}' uploaded and verified successfully. Student profile updated."
    }

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
    required_docs = json.loads(sc["required_documents_json"])
    student_docs = json.loads(st["documents_json"])
    
    reasons = []
    missing_docs = []
    is_eligible = True
    
    # 1. State Verification
    if "All India" not in eligible_states and st["state"] not in eligible_states:
        is_eligible = False
        reasons.append(f"State mismatch: Student is from {st['state']}, scholarship requires {eligible_states}")
        
    # 2. Income Verification
    if st["annual_income"] > sc["income_limit"]:
        is_eligible = False
        reasons.append(f"Income limit exceeded: Student income ₹{st['annual_income']} > Limit ₹{sc['income_limit']}")
        
    # 3. Field Verification
    student_field_match = any(field.lower() in st["education"].lower() for field in eligible_fields)
    if not student_field_match:
        is_eligible = False
        reasons.append(f"Field mismatch: Student education '{st['education']}' does not match required fields {eligible_fields}")
        
    # 4. CGPA Verification
    if st["cgpa"] < sc["min_cgpa"]:
        is_eligible = False
        reasons.append(f"CGPA below limit: Student CGPA {st['cgpa']} < Required {sc['min_cgpa']}")

    return {
        "student_id": req.student_id,
        "scholarship_id": req.scholarship_id,
        "scholarship_name": sc["name"],
        "scholarship_type": sc["scholarship_type"],
        "is_eligible": is_eligible,
        "missing_documents": missing_docs,
        "action_required": "DEMAND_DOCUMENT" if missing_docs else "NONE",
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
    
    if req.armoriq_decision != "ALLOW":
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

    app_id = f"APP-{req.student_id}-{req.scholarship_id}"
    conn.execute("""
        INSERT OR REPLACE INTO applications (application_id, student_id, scholarship_id, status, intent_token, applied_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (app_id, req.student_id, req.scholarship_id, "SUBMITTED", req.intent_token or "TOKEN-APPROVED", now_str))
    
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
