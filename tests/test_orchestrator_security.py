from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.agent.models import StudentIntent
from app.armoriq.errors import IntentMismatchException
from app.tools.scholarship_tools import ScholarshipMCPTools


class FakeArmorIQDenied:

    def capture_plan(self, **kwargs):

        return type(
            "Plan",
            (),
            {
                "raw_sdk_obj": object(),
                "plan_id": "test-plan",
            },
        )()

    def get_intent_token_details(
        self,
        plan,
        validity_seconds=300,
    ):

        return {
            "token_string": "test-token",
            "token_id": "test-token-id",
            "api_key_used": False,
            "provider": "TEST_ONLY",
        }

    def invoke(
        self,
        mcp,
        action,
        intent_token,
        params,
        user_email,
    ):

        if action == "submit_application":

            raise IntentMismatchException(
                "Test: ArmorIQ denied unauthorized action"
            )

        return {
            "decision": "ALLOW"
        }


def test_denied_submission_is_never_invoked():

    tools = ScholarshipMCPTools()

    armor = FakeArmorIQDenied()

    orchestrator = ScholarshipAgentOrchestrator(
        armoriq_client=armor,
        tools=tools,
    )

    intent = StudentIntent(
        intent_id="test-intent",
        user_id="test-student",
        user_name="Test Student",
        raw_prompt=(
            "Find government engineering scholarships "
            "in Punjab and apply only to eligible ones."
        ),
        scholarship_type="government",
        target_state="Punjab",
        target_field="Engineering",
        annual_income=450000,
        must_be_eligible_only=True,
        requires_human_approval_before_submit=True,
    )

    result = orchestrator.run_agent_workflow(
        intent=intent,
        simulate_out_of_scope_violation=True,
    )

    assert tools.submit_invocation_count == 0

    blocked_steps = [
        step
        for step in result.step_results
        if step.action == "submit_application"
    ]

    assert len(blocked_steps) == 1

    assert blocked_steps[0].status == "BLOCKED"

    assert blocked_steps[0].executed is False
