import pytest
from mock_portal.database import init_db, get_db_connection
from mock_portal.routes import submit_application, ApplicationSubmitRequest
from fastapi import HTTPException

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_proof_of_non_execution_when_blocked_by_armoriq():
    conn = get_db_connection()
    initial_count = conn.execute("SELECT COUNT(*) FROM applications WHERE scholarship_id = 'SCH-PRV-GLOBAL-03'").fetchone()[0]
    conn.close()
    assert initial_count == 0

    req = ApplicationSubmitRequest(
        application_id="APP-student-demo-001-SCH-PRV-GLOBAL-03",
        student_id="student-demo-001",
        scholarship_id="SCH-PRV-GLOBAL-03",
        intent_token="ARMORIQ-TOKEN-DENIED",
        armoriq_decision="BLOCK"
    )

    # Submission call should raise 403 Forbidden with ArmorIQ Governance detail
    with pytest.raises(HTTPException) as exc_info:
        submit_application(req)
        
    assert exc_info.value.status_code == 403
    assert "ArmorIQ Governance Violation" in exc_info.value.detail

    # VERIFICATION: Database application submission count must remain strictly 0
    conn = get_db_connection()
    post_count = conn.execute("SELECT COUNT(*) FROM applications WHERE scholarship_id = 'SCH-PRV-GLOBAL-03' AND status = 'SUBMITTED'").fetchone()[0]
    log_entry = conn.execute("SELECT * FROM tool_execution_logs WHERE target_scholarship_id = 'SCH-PRV-GLOBAL-03'").fetchone()
    conn.close()

    assert post_count == 0, "CRITICAL SECURITY FAILURE: Application was submitted despite ArmorIQ BLOCK decision!"
    assert log_entry is not None
    assert log_entry["armoriq_decision"] == "BLOCK"
    assert log_entry["executed"] == 0, "CRITICAL SECURITY FAILURE: Tool execution flag was not 0!"
