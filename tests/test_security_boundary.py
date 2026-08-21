import pytest
from app.armoriq.test_shim import FakeArmorIQShim
from app.tools.scholarship_tools import ScholarshipMCPTools
from app.armoriq.errors import IntentMismatchException, ArmorIQException


def test_tool_refuses_blocked_submission_and_fails_closed():
    shim = FakeArmorIQShim()
    tools = ScholarshipMCPTools(armoriq_client=shim)

    # Create a test intent token using the shim
    plan = shim.capture_plan(llm="test", prompt="p", plan={})
    token = shim.get_intent_token(plan)

    # Attempt to submit a private / out-of-scope scholarship — shim will treat as BLOCK
    with pytest.raises(IntentMismatchException):
        tools.submit_application(
            student_id="student-demo-001",
            scholarship_id="SCH-PRV-GLOBAL-03",
            intent_token=token,
            armoriq_decision="BLOCK",
        )


def test_tool_fails_closed_when_no_armoriq_client():
    tools = ScholarshipMCPTools()
    plan_token = "armoriq_intent_test_dummy"

    with pytest.raises(ArmorIQException):
        tools.submit_application(
            student_id="student-demo-001",
            scholarship_id="SCH-GOV-PB-01",
            intent_token=plan_token,
            armoriq_decision="ALLOW",
        )
