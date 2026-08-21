import pytest
from mock_portal.database import init_db, get_db_connection
from mock_portal.routes import list_scholarships, check_eligibility, EligibilityCheckRequest

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

def test_scholarship_listing_and_filtering():
    items = list_scholarships(scholarship_type="government", state="Punjab")
    assert len(items) >= 1
    assert items[0]["scholarship_id"] == "SCH-GOV-PB-01"
    assert items[0]["scholarship_type"] == "government"

def test_student_eligibility_positive():
    req = EligibilityCheckRequest(student_id="student-demo-001", scholarship_id="SCH-GOV-PB-01")
    res = check_eligibility(req)
    assert res["is_eligible"] is True
    assert len(res["rejection_reasons"]) == 0

def test_student_eligibility_state_mismatch():
    req = EligibilityCheckRequest(student_id="student-demo-001", scholarship_id="SCH-GOV-MH-02")
    res = check_eligibility(req)
    assert res["is_eligible"] is False
    assert any("State mismatch" in r for r in res["rejection_reasons"])
