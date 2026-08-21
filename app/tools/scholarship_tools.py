from typing import Dict, Any, Optional

from app.scholarship.service import ScholarshipService


class ScholarshipMCPTools:
    """
    Scholarship tool boundary.

    IMPORTANT:
    This class is the application/tool layer.
    It does NOT pretend to be ArmorIQ.

    ArmorIQ governance must happen BEFORE the protected
    submit_application() method is called.
    """

    def __init__(self, service: Optional[ScholarshipService] = None):
        self.service = service or ScholarshipService()

        # Runtime instrumentation.
        # This is used to prove whether the protected tool
        # was actually invoked.
        self.submit_invocation_count = 0

    def search_scholarships(
        self,
        scholarship_type: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:

        results = self.service.search_scholarships(
            scholarship_type=scholarship_type,
            state=state,
        )

        return {
            "tool": "search_scholarships",
            "count": len(results),
            "scholarships": [r.dict() for r in results],
        }

    def get_scholarship_details(
        self,
        scholarship_id: str,
    ) -> Dict[str, Any]:

        item = self.service.get_scholarship_details(
            scholarship_id=scholarship_id
        )

        return {
            "tool": "get_scholarship_details",
            "scholarship": item.dict(),
        }

    def check_eligibility(
        self,
        student_id: str,
        scholarship_id: str,
    ) -> Dict[str, Any]:

        result = self.service.check_eligibility(
            student_id=student_id,
            scholarship_id=scholarship_id,
        )

        return {
            "tool": "check_eligibility",
            "result": result.dict(),
        }

    def prepare_application(
        self,
        student_id: str,
        scholarship_id: str,
    ) -> Dict[str, Any]:

        result = self.service.prepare_application_draft(
            student_id=student_id,
            scholarship_id=scholarship_id,
        )

        return {
            "tool": "prepare_application",
            "draft": result,
        }

    def submit_application(
        self,
        student_id: str,
        scholarship_id: str,
        intent_token: str,
        armoriq_decision: str = "ALLOW",
    ) -> Dict[str, Any]:
        """
        CONSEQUENTAL / PROTECTED ACTION.

        This method must only be called after the ArmorIQ
        governance layer has authorized the action.

        Defense-in-depth:
        even if this method is accidentally called with BLOCK,
        it refuses to execute the downstream portal request.
        """

        self.submit_invocation_count += 1

        if armoriq_decision != "ALLOW":
            raise PermissionError(
                "Protected action denied: ArmorIQ decision is not ALLOW."
            )

        result = self.service.submit_application(
            student_id=student_id,
            scholarship_id=scholarship_id,
            intent_token=intent_token,
            armoriq_decision="ALLOW",
        )

        return {
            "tool": "submit_application",
            "execution_result": result,
            "mcp_invoked": True,
            "protected_action_executed": True,
        }
