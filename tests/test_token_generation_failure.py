from app.agent.models import StudentIntent
from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.tools.scholarship_tools import ScholarshipMCPTools
from app.armoriq.errors import ArmorIQException


class FailingTokenClient:
    def capture_plan(self, llm=None, prompt=None, plan=None):
        # Return a dummy plan capture object; orchestrator will pass this
        # to get_intent_token_details which we implement to raise.
        return object()

    def get_intent_token_details(self, plan_capture, validity_seconds=300):
        raise ArmorIQException("Token minting failed: simulated backend error")


def test_token_mint_failure_blocks_execution():
    failing = FailingTokenClient()
    tools = ScholarshipMCPTools(armoriq_client=failing)
    orch = ScholarshipAgentOrchestrator(armoriq_client=failing, tools=tools)

    intent = StudentIntent(intent_id="i1", raw_prompt="Apply to scholarships")

    # Token minting fails — orchestrator should surface the ArmorIQException
    # and the protected tool must not be invoked.
    try:
        orch.run_agent_workflow(intent=intent)
        assert False, "Expected ArmorIQException due to token mint failure"
    except ArmorIQException:
        # Ensure protected submit_application was not called
        assert tools.submit_invocation_count == 0
