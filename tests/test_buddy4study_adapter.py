import pytest
from app.scholarship.models import ScholarshipItem, StudentProfile, EligibilityResult
from app.scholarship.sources.base import BaseScholarshipSource
from app.scholarship.sources.buddy4study import Buddy4StudySource
from app.scholarship.sources.portal import PortalScholarshipSource
from app.scholarship.service import ScholarshipService
from app.agent.models import StudentIntent
from app.agent.orchestrator import ScholarshipAgentOrchestrator
from app.armoriq.client import ArmorIQWrapperClient
from app.tools.scholarship_tools import ScholarshipMCPTools

def test_buddy4study_source_initialization():
    b4s = Buddy4StudySource()
    assert b4s.source_name == "Buddy4Study"
    assert "buddy4study.com" in b4s.source_base_url
    assert b4s.is_available() is True

def test_buddy4study_search_and_normalization():
    b4s = Buddy4StudySource()
    results = b4s.search_scholarships(scholarship_type="private")
    assert len(results) >= 3

    for item in results:
        assert isinstance(item, ScholarshipItem)
        assert item.source == "Buddy4Study"
        assert item.source_url is not None
        assert "buddy4study.com" in item.source_url
        assert item.provider is not None
        assert item.scholarship_type == "private"
        assert item.amount > 0

def test_buddy4study_specific_filter():
    b4s = Buddy4StudySource()
    # Search for engineering specifically
    results = b4s.search_scholarships(field="Engineering")
    assert len(results) >= 1
    tata_scholarship = next((s for s in results if "Tata" in s.name), None)
    assert tata_scholarship is not None
    assert tata_scholarship.source == "Buddy4Study"
    assert "tata-capital-pankh" in tata_scholarship.source_url

def test_buddy4study_eligibility_evaluation():
    b4s = Buddy4StudySource()
    tata_item = b4s.get_scholarship_details("B4S-TATA-PANKH-2026")
    assert tata_item is not None

    eligible_student = StudentProfile(
        student_id="student-demo-001",
        name="Gurpreet Singh",
        education="B.Tech Computer Science",
        state="Punjab",
        annual_income=300000,
        cgpa=8.5
    )
    res = b4s.check_eligibility(eligible_student, tata_item)
    assert res.is_eligible is True
    assert len(res.rejection_reasons) == 0

    # Ineligible student due to income
    ineligible_student = StudentProfile(
        student_id="student-high-income",
        name="High Income Student",
        education="B.Tech Computer Science",
        state="Punjab",
        annual_income=800000,
        cgpa=8.5
    )
    res_ineligible = b4s.check_eligibility(ineligible_student, tata_item)
    assert res_ineligible.is_eligible is False
    assert any("Income limit exceeded" in r for r in res_ineligible.rejection_reasons)

def test_scholarship_service_multi_source_aggregation():
    service = ScholarshipService()
    # Ensure both portal and buddy4study are active
    assert any(s.source_name == "Buddy4Study" for s in service.sources)
    assert any("Portal" in s.source_name for s in service.sources)

    # Aggregated query returns both govt and private with source attribution
    all_items = service.search_scholarships(scholarship_type="all")
    assert len(all_items) >= 5
    sources_present = {item.source for item in all_items}
    assert "Buddy4Study" in sources_present

def test_armoriq_governance_blocks_unauthorized_buddy4study_action():
    """
    CRITICAL INVARIANT TEST:
    When user declared intent is 'government', any out-of-scope attempt
    to apply for a private Buddy4Study grant MUST be blocked by ArmorIQ.
    """
    armoriq = ArmorIQWrapperClient()
    service = ScholarshipService()
    tools = ScholarshipMCPTools(service=service, armoriq_client=armoriq)
    orchestrator = ScholarshipAgentOrchestrator(armoriq_client=armoriq, tools=tools)

    # Student intent strictly declared as 'government'
    govt_intent = StudentIntent(
        intent_id="intent-test-b4s-001",
        user_id="student-demo-001",
        user_name="Gurpreet Singh",
        raw_prompt="Find and apply for government scholarships only",
        target_state="Punjab",
        target_field="Engineering",
        scholarship_type="government",
        annual_income=450000
    )

    # Run workflow with simulated out-of-scope drift targeting private scholarship
    summary = orchestrator.run_agent_workflow(
        intent=govt_intent,
        simulate_out_of_scope_violation=True
    )

    # Assert ArmorIQ intercepted and blocked the action
    assert summary.blocked_steps > 0 or summary.status in ("PARTIALLY_BLOCKED", "BLOCKED", "FAILED")
    # Assert Proof of Non-Execution: 0 submits executed on the tools boundary
    assert tools.submit_invocation_count == 0
