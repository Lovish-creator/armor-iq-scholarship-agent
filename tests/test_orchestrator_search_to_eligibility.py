from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.agent.models import StudentIntent


class StubSearchTool:
    def search_live_web(self, query=None, state=None, field=None, scholarship_type=None):
        return [
            {
                "scholarship_id": "SCH-LIVE-999",
                "name": "Live State Scholarship",
                "scholarship_type": scholarship_type or "government",
                "eligible_states": [state],
                "eligible_fields": [field],
            }
        ]


class StubTools:
    def __init__(self):
        self.checked = []
        self.prepared = []
        self.submitted = []

    def check_eligibility(self, student_id, scholarship_id):
        self.checked.append(scholarship_id)
        return {"tool": "check_eligibility", "result": {"scholarship_id": scholarship_id, "is_eligible": True}}

    def prepare_application(self, student_id, scholarship_id):
        self.prepared.append(scholarship_id)
        return {"draft_id": f"DRAFT-{scholarship_id}"}

    def submit_application(self, student_id, scholarship_id, intent_token, armoriq_decision="ALLOW"):
        self.submitted.append(scholarship_id)
        return {"success": True, "application_id": f"APP-{student_id}-{scholarship_id}"}


def test_orchestrator_uses_discovered_scholarship():
    # Inject a harmless ArmorIQ stub that allows execution
    class AllowArmorIQStub:
        def capture_plan(self, **kwargs):
            return type("Plan", (), {"raw_sdk_obj": object(), "plan_id": "p"})()

        def get_intent_token_details(self, plan, validity_seconds=300):
            return {"token_string": "t", "token_id": "tid", "api_key_used": False, "provider": "TEST"}

        def invoke(self, mcp, action, intent_token, params, user_email):
            return {"decision": "ALLOW"}

    arm = AllowArmorIQStub()
    tools = StubTools()
    orchestrator = ScholarshipAgentOrchestrator(armoriq_client=arm, tools=tools)
    orchestrator.web_search_tool = StubSearchTool()

    intent = StudentIntent(intent_id="i1", raw_prompt="Find scholarships", target_state="Punjab")

    # Run workflow — expect orchestrator to pick SCH-LIVE-999 from discovery
    res = orchestrator.run_agent_workflow(intent=intent, simulate_out_of_scope_violation=False)

    # Verify that the tools saw the discovered scholarship id
    assert "SCH-LIVE-999" in tools.checked
    assert "SCH-LIVE-999" in tools.prepared
    assert "SCH-LIVE-999" in tools.submitted
