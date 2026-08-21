from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StudentProfile(BaseModel):
    student_id: str
    name: str
    education: str
    state: str
    annual_income: int
    category: str
    cgpa: float
    documents: List[str]

class ScholarshipItem(BaseModel):
    scholarship_id: str
    name: str
    scholarship_type: str
    eligible_states: List[str]
    eligible_fields: List[str]
    income_limit: int
    min_cgpa: float
    amount: int
    deadline: str
    required_documents: List[str]

class EligibilityResult(BaseModel):
    student_id: str
    scholarship_id: str
    scholarship_name: str
    scholarship_type: str
    is_eligible: bool
    rejection_reasons: List[str]

class ApplicationRecord(BaseModel):
    application_id: str
    student_id: str
    scholarship_id: str
    status: str
    intent_token: Optional[str] = None
    applied_at: str
    rejection_reason: Optional[str] = None
