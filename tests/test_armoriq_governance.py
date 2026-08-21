import pytest
from app.armoriq.client import ArmorIQWrapperClient
from app.armoriq.errors import IntentMismatchException, InvalidTokenException

def test_armoriq_plan_capture_and_token_minting():
    client = ArmorIQWrapperClient()
    plan_data = {
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {"scholarship_type": "government", "target_state": "Punjab"},
        "steps": []
    }
    
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Test Prompt", plan=plan_data)
    assert captured.plan_id.startswith("plan_")
    
    token = client.get_intent_token(captured, validity_seconds=300)
    assert token.startswith("armoriq_intent_") or len(token) > 20

def test_armoriq_authorized_action_allow():
    client = ArmorIQWrapperClient()
    plan_data = {
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {"scholarship_type": "government", "target_state": "Punjab"},
        "steps": []
    }
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Test Prompt", plan=plan_data)
    token = client.get_intent_token(captured)
    
    res = client.invoke(
        mcp_name="mcp_scholarship_tool",
        action="submit_application",
        intent_token=token,
        inputs={"scholarship_id": "SCH-GOV-PB-01", "scholarship_type": "government", "state": "Punjab"}
    )
    assert res["decision"] == "ALLOW"

def test_armoriq_out_of_scope_action_block():
    client = ArmorIQWrapperClient()
    plan_data = {
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {"scholarship_type": "government", "target_state": "Punjab"},
        "steps": []
    }
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Test Prompt", plan=plan_data)
    token = client.get_intent_token(captured)
    
    with pytest.raises(IntentMismatchException) as exc_info:
        client.invoke(
            mcp_name="mcp_scholarship_tool",
            action="submit_application",
            intent_token=token,
            inputs={"scholarship_id": "SCH-PRV-GLOBAL-03", "scholarship_type": "private", "state": "All India"}
        )
    
    assert "ARMORIQ INTENT VIOLATION" in str(exc_info.value)
