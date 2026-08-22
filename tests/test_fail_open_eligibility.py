from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.agent.models import StudentIntent
from app.armoriq.test_shim import FakeArmorIQShim
from app.tools.scholarship_tools import ScholarshipMCPTools
from app.scholarship.service import ScholarshipService
import mock_portal.routes as portal_routes


def test_portal_unavailable_blocks_submission():
    # Arrange: ArmorIQ allows actions but portal eligibility checks raise
    arm = FakeArmorIQShim()

    # Use a base_url that will cause remote HTTP calls to fail
    svc = ScholarshipService(base_url="http://127.0.0.1:59999")

    tools = ScholarshipMCPTools(service=svc, armoriq_client=arm)

    orchestrator = ScholarshipAgentOrchestrator(armoriq_client=arm, tools=tools)

    intent = StudentIntent(
        intent_id="intent-001",
        user_id="student-001",
        user_name="Test Student",
        raw_prompt="Apply to government scholarships in Punjab",
        scholarship_type="government",
        target_state="Punjab",
        target_field="Engineering",
        annual_income=300000,
        must_be_eligible_only=True,
        requires_human_approval_before_submit=False,
    )

    # Temporarily monkeypatch the portal check_eligibility to raise, simulating local mock portal unavailable
    original_check = getattr(portal_routes, "check_eligibility", None)

    def raising_check(req):
        raise Exception("mock portal DB unavailable")

    portal_routes.check_eligibility = raising_check

    try:
        # Act
        result = orchestrator.run_agent_workflow(intent=intent, simulate_out_of_scope_violation=False)

        # Assert: submit_application was never invoked
        assert tools.submit_invocation_count == 0

        blocked_steps = [s for s in result.step_results if s.action == "submit_application"]
        assert len(blocked_steps) == 1
        assert blocked_steps[0].status == "BLOCKED"
        assert blocked_steps[0].executed is False

    finally:
        # Restore original portal function
        if original_check is not None:
            portal_routes.check_eligibility = original_check