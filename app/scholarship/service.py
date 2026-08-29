import os
import httpx
import logging
from typing import List, Optional, Dict, Any
from app.scholarship.models import StudentProfile, ScholarshipItem, EligibilityResult, ApplicationRecord

logger = logging.getLogger("scholarship_service")

class ScholarshipService:
    """
    Scholarship Domain Service connecting to Portal Backend API
    and live external scholarship data feeds.
    """
    def __init__(self, base_url: Optional[str] = None):
        # Allow overriding the portal base URL via environment for real integration.
        self.base_url = base_url or os.getenv("PORTAL_BASE_URL", "http://127.0.0.1:8001")
        # Allow tests and demo mode to use the in-process mock portal as a
        # fallback. Production deployments SHOULD set
        # `ALLOW_MOCK_PORTAL_FALLBACK=false` to avoid accidentally using the
        # mock portal when the real portal is unreachable.
        self.allow_mock_portal_fallback = os.getenv("ALLOW_MOCK_PORTAL_FALLBACK", "true").lower() in ("1", "true", "yes")
        self.single_port = os.getenv("SINGLE_PORT", "false").lower() in ("1", "true", "yes")

    def search_scholarships(self, scholarship_type: Optional[str] = None, state: Optional[str] = None) -> List[ScholarshipItem]:
        params = {}
        if scholarship_type:
            params["scholarship_type"] = scholarship_type
        if state:
            params["state"] = state
            
        local_results = []
        if self.single_port:
            try:
                from mock_portal.routes import list_scholarships as local_list
                items = local_list(scholarship_type, state)
                local_results = [ScholarshipItem(**item) for item in items]
            except Exception as e:
                logger.warning(f"Single port local list error: {e}")
        else:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(f"{self.base_url}/api/scholarships", params=params)
                    resp.raise_for_status()
                    local_results = [ScholarshipItem(**item) for item in resp.json()]
            except Exception as e:
                logger.warning(f"Local portal query error: {e}")
                if self.allow_mock_portal_fallback:
                    try:
                        from mock_portal.routes import list_scholarships as local_list
                        items = local_list(scholarship_type, state)
                        local_results = [ScholarshipItem(**item) for item in items]
                    except Exception:
                        pass

        # Live external fetch integration fallback/enrichment
        live_external_items = self._fetch_live_external_scholarships(scholarship_type, state)
        
        # Merge results, avoiding duplicates
        existing_ids = {r.scholarship_id for r in local_results}
        for ext in live_external_items:
            if ext.scholarship_id not in existing_ids:
                local_results.append(ext)

        return local_results

    def _fetch_live_external_scholarships(self, scholarship_type: Optional[str], state: Optional[str]) -> List[ScholarshipItem]:
        """Fetches live public scholarship listings from open government APIs / feeds if reachable."""
        results = []
        try:
            # Example query to public education data endpoint
            with httpx.Client(timeout=5.0) as client:
                resp = client.get("https://scholarships.gov.in/public/api/open_scholarships", params={"state": state or "Punjab"})
                if resp.status_code == 200:
                    data = resp.json()
                    for idx, item in enumerate(data.get("scholarships", [])):
                        results.append(ScholarshipItem(
                            scholarship_id=f"SCH-LIVE-{idx+100}",
                            name=item.get("title", "Live State Post-Matric Scheme"),
                            scholarship_type=scholarship_type or "government",
                            eligible_states=[state or "Punjab"],
                            eligible_fields=["Engineering", "Computer Science"],
                            income_limit=item.get("income_limit", 800000),
                            min_cgpa=6.0,
                            amount=item.get("amount", 50000),
                            deadline=item.get("deadline", "2026-12-31"),
                            required_documents=["marksheet_12th.pdf", "income_certificate.pdf"]
                        ))
        except Exception as e:
            logger.debug(f"Live external fetch note: {e}")
            
        return results

    def get_scholarship_details(self, scholarship_id: str) -> ScholarshipItem:
        if self.single_port:
            from mock_portal.routes import get_scholarship_details as local_get
            return ScholarshipItem(**local_get(scholarship_id))
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/scholarships/{scholarship_id}")
                resp.raise_for_status()
                return ScholarshipItem(**resp.json())
        except Exception:
            if self.allow_mock_portal_fallback:
                from mock_portal.routes import get_scholarship_details as local_get
                return ScholarshipItem(**local_get(scholarship_id))
            else:
                raise RuntimeError("Remote portal unavailable and mock fallback disabled")

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
