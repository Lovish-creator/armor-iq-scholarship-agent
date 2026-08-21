from typing import Any, Dict
from app.armoriq.errors import IntentMismatchException


class FakeArmorIQShim:
    """A simple, explicit test double for ArmorIQ used only in unit tests.

    This shim is NOT a substitute for the real SDK. It implements a
    minimal, deterministic behavior for ALLOW vs BLOCK decisions so
    tests can verify control-flow without contacting external services.
    """

    def __init__(self):
        self.plan_counter = 0

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]):
        self.plan_counter += 1
        return type("Plan", (), {"raw_sdk_obj": object(), "plan_id": f"plan_test_{self.plan_counter}"})()

    def get_intent_token(self, plan_capture: Any):
        return f"armoriq_intent_test_{getattr(plan_capture, 'plan_id', 'x')}"

    def invoke(self, mcp: str = None, action: str = None, intent_token: str = None, params: Dict[str, Any] = None, user_email: str = None):
        # Simple policy: if scholarship_id contains 'PRV' or params indicate private, block
        scholarship_id = (params or {}).get("scholarship_id")
        scholarship_type = (params or {}).get("scholarship_type")

        if scholarship_type == "private" or (scholarship_id and "PRV" in scholarship_id):
            raise IntentMismatchException("ARMORIQ INTENT VIOLATION: out-of-scope target detected")

        return {"decision": "ALLOW"}

    def verify_intent_token(self, intent_token: str, mcp: str = None, expected_action: str = None, params: Dict[str, Any] = None):
        # If token contains 'test' it's valid. Otherwise, simulate failure.
        if not intent_token or "armoriq_intent_test" not in intent_token:
            raise IntentMismatchException("Invalid or unverifiable intent token")

        # Also check params for disallowed targets
        scholarship_id = (params or {}).get("scholarship_id")
        scholarship_type = (params or {}).get("scholarship_type")

        if scholarship_type == "private" or (scholarship_id and "PRV" in scholarship_id):
            raise IntentMismatchException("ARMORIQ INTENT VIOLATION: out-of-scope target detected")

        return {"decision": "ALLOW", "provider": "TEST_SHIM"}
