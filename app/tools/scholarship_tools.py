from typing import Dict, Any, List, Optional
from app.scholarship.service import ScholarshipService

class ScholarshipMCPTools:
    def __init__(self, service: Optional[ScholarshipService] = None):
        self.service = service or ScholarshipService()

    def search_scholarships(self, scholarship_type: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """Search available scholarships matching type and state parameters."""
        results = self.service.search_scholarships(scholarship_type=scholarship_type, state=state)
        return {
            "tool": "search_scholarships",
            "count": len(results),
            "scholarships": [r.dict() for r in results]
        }

    def get_scholarship_details(self, scholarship_id: str) -> Dict[str, Any]:
        """Fetch complete criteria and document requirements for a given scholarship."""
        item = self.service.get_scholarship_details(scholarship_id=scholarship_id)
        return {
            "tool": "get_scholarship_details",
            "scholarship": item.dict()
        }

    def check_eligibility(self, student_id: str, scholarship_id: str) -> Dict[str, Any]:
        """Verify student criteria against scholarship requirements."""
        res = self.service.check_eligibility(student_id=student_id, scholarship_id=scholarship_id)
        return {
            "tool": "check_eligibility",
            "result": res.dict()
        }

    def prepare_application(self, student_id: str, scholarship_id: str) -> Dict[str, Any]:
        """Prepare draft application and verify document readiness."""
        res = self.service.prepare_application_draft(student_id=student_id, scholarship_id=scholarship_id)
        return {
            "tool": "prepare_application",
            "draft": res
        }

    def submit_application(self, student_id: str, scholarship_id: str, intent_token: str, armoriq_decision: str = "ALLOW") -> Dict[str, Any]:
        """Governed execution step: Submit scholarship application with signed intent token."""
        res = self.service.submit_application(
            student_id=student_id,
            scholarship_id=scholarship_id,
            intent_token=intent_token,
            armoriq_decision=armoriq_decision
        )
        return {
            "tool": "submit_application",
            "execution_result": res
        }
