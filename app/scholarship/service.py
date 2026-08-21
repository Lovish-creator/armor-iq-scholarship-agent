import httpx
import logging
from typing import List, Optional, Dict, Any
from app.scholarship.models import StudentProfile, ScholarshipItem, EligibilityResult, ApplicationRecord

logger = logging.getLogger("scholarship_service")

class ScholarshipService:
    """
    Scholarship Domain Service connecting to Portal Backend API
    and live external scholarship data feeds.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        self.base_url = base_url

    def search_scholarships(self, scholarship_type: Optional[str] = None, state: Optional[str] = None) -> List[ScholarshipItem]:
        params = {}
        if scholarship_type:
            params["scholarship_type"] = scholarship_type
        if state:
            params["state"] = state
            
        local_results = []
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/scholarships", params=params)
                resp.raise_for_status()
                local_results = [ScholarshipItem(**item) for item in resp.json()]
        except Exception as e:
            logger.warning(f"Local portal query error: {e}")

        # Live external fetch integration fallback/enrichment
        live_external_items = self._fetch_live_external_scholarships(scholarship_type, state)
        
        # Merge results, avoiding duplicates
        existing_ids = {r.scholarship_id for r in local_results}
        for ext in live_external_items:
            if ext.scholarship_id not in existing_ids:
                local_results.append(ext)

        return local_results

    def _fetch_live_external_scholarships(self, scholarship_type: Optional[str], state: Optional[str]) -> List[ScholarshipItem]:
        """Fetches live public scholarship listings from open government APIs / feeds if reachable."""
        results = []
        try:
            # Example query to public education data endpoint
            with httpx.Client(timeout=5.0) as client:
                resp = client.get("https://scholarships.gov.in/public/api/open_scholarships", params={"state": state or "Punjab"})
                if resp.status_code == 200:
                    data = resp.json()
                    for idx, item in enumerate(data.get("scholarships", [])):
                        results.append(ScholarshipItem(
                            scholarship_id=f"SCH-LIVE-{idx+100}",
                            name=item.get("title", "Live State Post-Matric Scheme"),
                            scholarship_type=scholarship_type or "government",
                            eligible_states=[state or "Punjab"],
                            eligible_fields=["Engineering", "Computer Science"],
                            income_limit=item.get("income_limit", 800000),
                            min_cgpa=6.0,
                            amount=item.get("amount", 50000),
                            deadline=item.get("deadline", "2026-12-31"),
                            required_documents=["marksheet_12th.pdf", "income_certificate.pdf"]
                        ))
        except Exception as e:
            logger.debug(f"Live external fetch note: {e}")
            
        return results

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
