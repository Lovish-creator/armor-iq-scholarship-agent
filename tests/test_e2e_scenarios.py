import pytest
from app.agent.models import StudentIntent
from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.armoriq.client import ArmorIQWrapperClient
from app.armoriq.errors import InvalidTokenException, IntentMismatchException, PolicyBlockedException
from app.tools.scholarship_tools import ScholarshipMCPTools
from app.scholarship.service import ScholarshipService

def test_scenario_1_search_scholarships():
    """TEST 1: Legitimate search is allowed and executes."""
    service = ScholarshipService()
    results = service.search_scholarships(scholarship_type="government", state="Punjab")
    assert len(results) > 0
    assert any("Punjab" in s.eligible_states or "All India" in s.eligible_states for s in results)

def test_scenario_2_eligibility_check():
    """TEST 2: Eligibility check executed legitimately."""
    service = ScholarshipService()
    eligibility = service.check_eligibility(student_id="student-demo-001", scholarship_id="SCH-GOV-PB-01")
    assert eligibility.student_id == "student-demo-001"

def test_scenario_3_prepare_application():
    """TEST 3: Prepare application draft for valid student and scholarship."""
    service = ScholarshipService()
    draft = service.prepare_application_draft(student_id="student-demo-001", scholarship_id="SCH-GOV-PB-01")
    assert "application_id" in draft
    assert draft["status"] in ("PREPARED", "DRAFTED")

def test_scenario_4_submit_application_authorized():
    """TEST 4: Submission requires explicit ALLOW decision."""
    service = ScholarshipService()
    res = service.submit_application(
        student_id="student-demo-001",
        scholarship_id="SCH-GOV-PB-01",
        intent_token="test_token_123",
        armoriq_decision="ALLOW"
    )
    assert res.get("status") in ("SUBMITTED", "PENDING_VERIFICATION", "SUCCESS") or res.get("success") is True

def test_scenario_5_out_of_plan_tool_blocked():
    """TEST 5: Out of plan / out of scope intent drift is blocked by ArmorIQ."""
    client = ArmorIQWrapperClient()
    plan_dict = {
        "goal": "Search government scholarships",
        "steps": [
            {"action": "search_scholarships", "mcp": "scholarship", "params": {"state": "Punjab"}}
        ]
    }
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Search scholarships", plan=plan_dict)
    token = client.get_intent_token(captured)
    
    # Attempting to invoke an uncaptured/unauthorized action should fail or block
    try:
        res = client.invoke(mcp="scholarship", action="unauthorized_transfer", intent_token=token)
        assert res.get("decision") == "BLOCK"
    except (IntentMismatchException, PolicyBlockedException, InvalidTokenException):
        pass  # Blocked as expected

def test_scenario_6_policy_denied_tool():
    """TEST 6: Tool not in policy allow list is blocked."""
    client = ArmorIQWrapperClient()
    plan_dict = {
        "goal": "Admin deletion",
        "steps": [
            {"action": "delete_all_records", "mcp": "scholarship", "params": {}}
        ]
    }
    captured = client.capture_plan(llm="gemini-3.6-flash", prompt="Delete records", plan=plan_dict)
    token = client.get_intent_token(captured)
    try:
        res = client.invoke(mcp="scholarship", action="delete_all_records", intent_token=token)
        assert res.get("decision") == "BLOCK"
    except (IntentMismatchException, PolicyBlockedException, InvalidTokenException):
        pass  # Blocked as expected

def test_scenario_7_invalid_api_key():
    """TEST 7: Invalid API key handling."""
    bad_client = ArmorIQWrapperClient(api_key="ak_live_invalid_bad_key_0000000000000000")
    plan_dict = {
        "goal": "Search scholarships",
        "steps": [
            {"action": "search_scholarships", "mcp": "scholarship", "params": {"state": "Punjab"}}
        ]
    }
    bad_plan = bad_client.capture_plan(llm="gemini", prompt="test", plan=plan_dict)
    token = bad_client.get_intent_token(bad_plan)
    # When invoking with invalid API key against the proxy, it raises InvalidTokenException / 401
    with pytest.raises(Exception) as exc_info:
        res = bad_client.invoke(mcp="scholarship", action="search_scholarships", intent_token=token)
        if res.get("decision") == "BLOCK":
            raise InvalidTokenException("Blocked due to invalid key")
    assert exc_info.value is not None
