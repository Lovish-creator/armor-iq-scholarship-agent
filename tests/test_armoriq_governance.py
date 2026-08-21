import pytest
from app.armoriq.test_shim import FakeArmorIQShim
from app.armoriq.errors import IntentMismatchException


def test_armoriq_plan_capture_and_token_minting_shim():
    client = FakeArmorIQShim()
    plan_data = {
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {"scholarship_type": "government", "target_state": "Punjab"},
        "steps": []
    }

    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Test Prompt", plan=plan_data)
    assert captured.plan_id.startswith("plan_test_")

    token = client.get_intent_token(captured)
    assert token.startswith("armoriq_intent_test_")


def test_armoriq_authorized_action_allow_shim():
    client = FakeArmorIQShim()
    plan_data = {
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {"scholarship_type": "government", "target_state": "Punjab"},
        "steps": []
    }
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Test Prompt", plan=plan_data)
    token = client.get_intent_token(captured)

    res = client.invoke(
        mcp="mcp_scholarship_tool",
        action="submit_application",
        intent_token=token,
        params={"scholarship_id": "SCH-GOV-PB-01", "scholarship_type": "government", "state": "Punjab"}
    )
    assert res["decision"] == "ALLOW"


def test_armoriq_out_of_scope_action_block_shim():
    client = FakeArmorIQShim()
    plan_data = {
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {"scholarship_type": "government", "target_state": "Punjab"},
        "steps": []
    }
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Test Prompt", plan=plan_data)
    token = client.get_intent_token(captured)

    with pytest.raises(IntentMismatchException):
        client.invoke(
            mcp="mcp_scholarship_tool",
            action="submit_application",
            intent_token=token,
            params={"scholarship_id": "SCH-PRV-GLOBAL-03", "scholarship_type": "private", "state": "All India"}
        )
