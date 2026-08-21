import pytest

from app.tools.scholarship_tools import ScholarshipMCPTools


def test_blocked_submission_refuses_execution():
    """
    Security boundary test.

    A protected scholarship submission must never execute
    when ArmorIQ's decision is BLOCK.
    """

    tools = ScholarshipMCPTools()

    with pytest.raises(PermissionError):

        tools.submit_application(
            student_id="student-test",
            scholarship_id="SCH-TEST",
            intent_token="test-token",
            armoriq_decision="BLOCK",
        )

    # The tool may have been entered, but the downstream
    # scholarship service must NOT have been allowed to execute.
    assert tools.submit_invocation_count == 1
