from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StudentProfile(BaseModel):
    student_id: str
    name: str
    education: str
    state: str
    annual_income: int
    category: str = "General"
    cgpa: float = 8.0
    documents: List[str] = Field(default_factory=list)

class ScholarshipItem(BaseModel):
    scholarship_id: str
    name: str
    scholarship_type: str  # "government" or "private"
    eligible_states: List[str] = Field(default_factory=list)
    eligible_fields: List[str] = Field(default_factory=list)
    income_limit: int = 800000
    min_cgpa: float = 6.0
    amount: int = 50000
    deadline: str = "2026-12-31"
    required_documents: List[str] = Field(default_factory=list)
    
    # Source attribution fields
    source: str = "Government Portal"  # e.g., "Buddy4Study", "National Scholarship Portal (NSP)", "State Portal"
    source_url: Optional[str] = None   # e.g., "https://www.buddy4study.com/page/tata-capital-pankh-scholarship-programme"
    provider: Optional[str] = None     # e.g., "Tata Capital Limited & Tata Trusts"
    description: Optional[str] = None
    last_checked: Optional[str] = None

class EligibilityResult(BaseModel):
    student_id: str
    scholarship_id: str
    scholarship_name: str
    scholarship_type: str
    is_eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)

class ApplicationRecord(BaseModel):
    application_id: str
    student_id: str
    scholarship_id: str
    status: str
    intent_token: Optional[str] = None
    applied_at: str
    rejection_reason: Optional[str] = None
