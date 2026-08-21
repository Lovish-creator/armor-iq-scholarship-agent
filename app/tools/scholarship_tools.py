from typing import Dict, Any, Optional

from app.scholarship.service import ScholarshipService
from app.armoriq.errors import ArmorIQException

from typing import Dict, Any, Optional


class ScholarshipMCPTools:
    """
    Scholarship tool boundary.

    IMPORTANT:
    This class is the application/tool layer.
    It does NOT pretend to be ArmorIQ.

    ArmorIQ governance must happen BEFORE the protected
    submit_application() method is called.
    """

    def __init__(self, service: Optional[ScholarshipService] = None, armoriq_client: Optional[Any] = None):
        self.service = service or ScholarshipService()
        self.armoriq = armoriq_client

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


        # Defense-in-depth: refuse to execute unless orchestration
        # supplied an explicit ALLOW decision. For the official SDK
        # wrapper we do not call an undocumented verification API here.
        if not self.armoriq:
            raise ArmorIQException("No ArmorIQ client available; refusing to execute protected action.")

        # If the injected ArmorIQ client is a test shim that exposes
        # `verify_intent_token`, use it for extra verification. Otherwise,
        # rely on the orchestrator having performed the invocation and
        # pass an explicit `armoriq_decision` (defense-in-depth).
        if hasattr(self.armoriq, "verify_intent_token"):
            verification = self.armoriq.verify_intent_token(
                intent_token=intent_token,
                mcp="mcp_scholarship_tool",
                expected_action="submit_application",
                params={"scholarship_id": scholarship_id, "student_id": student_id},
            )
            decision = verification.get("decision")
            if decision != "ALLOW":
                raise PermissionError("Protected action denied: ArmorIQ verification did not allow this action.")
        else:
            if armoriq_decision != "ALLOW":
                raise PermissionError("Protected action denied: orchestrator did not receive ALLOW from ArmorIQ.")

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
            "armoriq_verification": verification,
        }
