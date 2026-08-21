import httpx
from typing import List, Optional, Dict, Any
from app.scholarship.models import StudentProfile, ScholarshipItem, EligibilityResult, ApplicationRecord

class ScholarshipService:
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url

    def search_scholarships(self, scholarship_type: Optional[str] = None, state: Optional[str] = None) -> List[ScholarshipItem]:
        params = {}
        if scholarship_type:
            params["scholarship_type"] = scholarship_type
        if state:
            params["state"] = state
            
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/api/scholarships", params=params)
            resp.raise_for_status()
            return [ScholarshipItem(**item) for item in resp.json()]

    def get_scholarship_details(self, scholarship_id: str) -> ScholarshipItem:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/api/scholarships/{scholarship_id}")
            resp.raise_for_status()
            return ScholarshipItem(**resp.json())

    def check_eligibility(self, student_id: str, scholarship_id: str) -> EligibilityResult:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.base_url}/api/eligibility/check",
                json={"student_id": student_id, "scholarship_id": scholarship_id}
            )
            resp.raise_for_status()
            return EligibilityResult(**resp.json())

    def prepare_application_draft(self, student_id: str, scholarship_id: str) -> Dict[str, Any]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.base_url}/api/applications/draft",
                json={"student_id": student_id, "scholarship_id": scholarship_id}
            )
            resp.raise_for_status()
            return resp.json()

    def submit_application(self, student_id: str, scholarship_id: str, intent_token: str, armoriq_decision: str = "ALLOW") -> Dict[str, Any]:
        app_id = f"APP-{student_id}-{scholarship_id}"
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.base_url}/api/applications/submit",
                json={
                    "application_id": app_id,
                    "student_id": student_id,
                    "scholarship_id": scholarship_id,
                    "intent_token": intent_token,
                    "armoriq_decision": armoriq_decision
                }
            )
            if resp.status_code >= 400:
                return {
                    "success": False,
                    "status_code": resp.status_code,
                    "detail": resp.json().get("detail", resp.text)
                }
            return resp.json()

    def track_application(self, application_id: str) -> ApplicationRecord:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.base_url}/api/applications/{application_id}")
            resp.raise_for_status()
            return ApplicationRecord(**resp.json())
