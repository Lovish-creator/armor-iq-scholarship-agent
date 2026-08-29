import os
import httpx
import logging
from typing import List, Optional, Dict, Any
from app.scholarship.models import StudentProfile, ScholarshipItem, EligibilityResult, ApplicationRecord
from app.scholarship.sources import BaseScholarshipSource, Buddy4StudySource, PortalScholarshipSource

logger = logging.getLogger("scholarship_service")

class ScholarshipService:
    """
    Scholarship Domain Service connecting to Portal Backend API
    and multi-source adapters including Buddy4Study and National Scholarship Feeds.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        sources: Optional[List[BaseScholarshipSource]] = None
    ):
        self.base_url = base_url or os.getenv("PORTAL_BASE_URL", "http://127.0.0.1:8001")
        self.allow_mock_portal_fallback = os.getenv("ALLOW_MOCK_PORTAL_FALLBACK", "true").lower() in ("1", "true", "yes")
        self.single_port = os.getenv("SINGLE_PORT", "true").lower() in ("1", "true", "yes")

        # Configurable & replaceable scholarship sources
        self.sources: List[BaseScholarshipSource] = sources or [
            PortalScholarshipSource(base_url=self.base_url),
            Buddy4StudySource(),
        ]

    def register_source(self, source: BaseScholarshipSource):
        """Allows dynamically plugging in additional scholarship sources."""
        self.sources.append(source)

    def search_scholarships(
        self,
        scholarship_type: Optional[str] = None,
        state: Optional[str] = None,
        query: Optional[str] = None,
        field: Optional[str] = None
    ) -> List[ScholarshipItem]:
        """
        Queries all registered scholarship sources (Portal, Buddy4Study, Open Feeds),
        normalizes results, and deduplicates by scholarship ID.
        """
        all_results: List[ScholarshipItem] = []
        seen_ids = set()

        for source in self.sources:
            try:
                source_results = source.search_scholarships(
                    query=query,
                    scholarship_type=scholarship_type,
                    state=state,
                    field=field
                )
                for item in source_results:
                    if item.scholarship_id not in seen_ids:
                        seen_ids.add(item.scholarship_id)
                        all_results.append(item)
            except Exception as exc:
                logger.warning(f"Error querying source '{source.source_name}': {exc}")

        return all_results

    def get_scholarship_details(self, scholarship_id: str) -> ScholarshipItem:
        """
        Fetches detailed scholarship metadata from registered sources.
        """
        for source in self.sources:
            try:
                item = source.get_scholarship_details(scholarship_id)
                if item:
                    return item
            except Exception as exc:
                logger.debug(f"Source '{source.source_name}' lookup note: {exc}")

        # Fallback to local mock portal direct check
        if self.single_port or self.allow_mock_portal_fallback:
            try:
                from mock_portal.routes import get_scholarship_details as local_get
                data = local_get(scholarship_id)
                if data:
                    return ScholarshipItem(**data)
            except Exception:
                pass

        raise RuntimeError(f"Scholarship '{scholarship_id}' not found across registered sources.")

    def check_eligibility(self, student_id: str, scholarship_id: str) -> EligibilityResult:
        try:
            if self.single_port:
                from mock_portal.routes import EligibilityCheckRequest, check_eligibility as local_check
                req = EligibilityCheckRequest(student_id=student_id, scholarship_id=scholarship_id)
                return EligibilityResult(**local_check(req))
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/eligibility/check",
                    json={"student_id": student_id, "scholarship_id": scholarship_id}
                )
                resp.raise_for_status()
                return EligibilityResult(**resp.json())
        except Exception:
            if self.allow_mock_portal_fallback and not self.single_port:
                try:
                    from mock_portal.routes import EligibilityCheckRequest, check_eligibility as local_check
                    req = EligibilityCheckRequest(student_id=student_id, scholarship_id=scholarship_id)
                    return EligibilityResult(**local_check(req))
                except Exception:
                    pass
            return EligibilityResult(
                student_id=student_id,
                scholarship_id=scholarship_id,
                scholarship_name="unknown",
                scholarship_type="government",
                is_eligible=False,
                rejection_reasons=["verification_unavailable"],
            )

    def prepare_application_draft(self, student_id: str, scholarship_id: str) -> Dict[str, Any]:
        if self.single_port:
            from mock_portal.routes import ApplicationDraftRequest, prepare_application_draft as local_prepare
            req = ApplicationDraftRequest(student_id=student_id, scholarship_id=scholarship_id)
            return local_prepare(req)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/applications/draft",
                    json={"student_id": student_id, "scholarship_id": scholarship_id}
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            if self.allow_mock_portal_fallback:
                from mock_portal.routes import ApplicationDraftRequest, prepare_application_draft as local_prepare
                req = ApplicationDraftRequest(student_id=student_id, scholarship_id=scholarship_id)
                return local_prepare(req)
            else:
                raise RuntimeError("Remote portal unavailable and mock fallback disabled for application draft")

    def submit_application(self, student_id: str, scholarship_id: str, intent_token: Any, armoriq_decision: str = "ALLOW") -> Dict[str, Any]:
        app_id = f"APP-{student_id}-{scholarship_id}"
        token_str = (
            intent_token
            if isinstance(intent_token, str)
            else getattr(intent_token, "token_id", None) or str(intent_token)
        )
        if self.single_port:
            from mock_portal.routes import ApplicationSubmitRequest, submit_application as local_submit
            req = ApplicationSubmitRequest(
                application_id=app_id,
                student_id=student_id,
                scholarship_id=scholarship_id,
                intent_token=token_str,
                armoriq_decision=armoriq_decision,
            )
            return local_submit(req)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/applications/submit",
                    json={
                        "application_id": app_id,
                        "student_id": student_id,
                        "scholarship_id": scholarship_id,
                        "intent_token": token_str,
                        "armoriq_decision": armoriq_decision
                    }
                )
                if resp.status_code >= 400:
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "detail": resp.json().get("detail", resp.text)
                    }
                return resp.json()
        except Exception:
            if self.allow_mock_portal_fallback:
                from mock_portal.routes import ApplicationSubmitRequest, submit_application as local_submit
                req = ApplicationSubmitRequest(
                    application_id=app_id,
                    student_id=student_id,
                    scholarship_id=scholarship_id,
                    intent_token=token_str,
                    armoriq_decision=armoriq_decision,
                )
                return local_submit(req)
            else:
                return {
                    "success": False,
                    "status_code": 503,
                    "detail": "Remote portal unavailable and mock fallback disabled",
                }

    def track_application(self, application_id: str) -> ApplicationRecord:
        if self.single_port:
            from mock_portal.routes import get_application_status as local_get
            return ApplicationRecord(**local_get(application_id))
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/applications/{application_id}")
                resp.raise_for_status()
                return ApplicationRecord(**resp.json())
        except Exception:
            if self.allow_mock_portal_fallback:
                from mock_portal.routes import get_application_status as local_get
                return ApplicationRecord(**local_get(application_id))
            else:
                raise RuntimeError("Remote portal unavailable and mock fallback disabled for tracking")
