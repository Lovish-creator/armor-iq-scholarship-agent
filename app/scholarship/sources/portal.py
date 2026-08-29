import os
import httpx
import logging
from typing import List, Optional, Dict, Any
from app.scholarship.models import ScholarshipItem, StudentProfile, EligibilityResult
from app.scholarship.sources.base import BaseScholarshipSource

logger = logging.getLogger("portal_source")

class PortalScholarshipSource(BaseScholarshipSource):
    """
    Primary State & Central Government Portal Data Source.
    Queries the official State/Central Scholarship Portal API or internal DB.
    """

    @property
    def source_name(self) -> str:
        return "National & State Scholarship Portal"

    @property
    def source_base_url(self) -> str:
        return self.base_url

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("PORTAL_BASE_URL", "http://127.0.0.1:8001")
        self.single_port = os.getenv("SINGLE_PORT", "true").lower() in ("1", "true", "yes")
        self.allow_mock_portal_fallback = os.getenv("ALLOW_MOCK_PORTAL_FALLBACK", "true").lower() in ("1", "true", "yes")

    def search_scholarships(
        self,
        query: Optional[str] = None,
        scholarship_type: Optional[str] = None,
        state: Optional[str] = None,
        field: Optional[str] = None
    ) -> List[ScholarshipItem]:
        results: List[ScholarshipItem] = []

        if self.single_port:
            try:
                from mock_portal.routes import list_scholarships as local_list
                items = local_list(scholarship_type, state)
                for itm in items:
                    if "source" not in itm:
                        itm["source"] = "National & State Scholarship Portal"
                    results.append(ScholarshipItem(**itm))
                return results
            except Exception as exc:
                logger.warning(f"Single port query error: {exc}")

        params = {}
        if scholarship_type:
            params["scholarship_type"] = scholarship_type
        if state:
            params["state"] = state

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/scholarships", params=params)
                resp.raise_for_status()
                for itm in resp.json():
                    if "source" not in itm:
                        itm["source"] = "National & State Scholarship Portal"
                    results.append(ScholarshipItem(**itm))
                return results
        except Exception as exc:
            logger.warning(f"Remote portal query error: {exc}")
            if self.allow_mock_portal_fallback:
                try:
                    from mock_portal.routes import list_scholarships as local_list
                    items = local_list(scholarship_type, state)
                    for itm in items:
                        if "source" not in itm:
                            itm["source"] = "National & State Scholarship Portal"
                        results.append(ScholarshipItem(**itm))
                except Exception:
                    pass

        return results

    def get_scholarship_details(self, scholarship_id: str) -> Optional[ScholarshipItem]:
        if self.single_port:
            from mock_portal.routes import get_scholarship_details as local_get
            data = local_get(scholarship_id)
            if data:
                if "source" not in data:
                    data["source"] = "National & State Scholarship Portal"
                return ScholarshipItem(**data)
            return None

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}/api/scholarships/{scholarship_id}")
                resp.raise_for_status()
                data = resp.json()
                if "source" not in data:
                    data["source"] = "National & State Scholarship Portal"
                return ScholarshipItem(**data)
        except Exception:
            if self.allow_mock_portal_fallback:
                from mock_portal.routes import get_scholarship_details as local_get
                data = local_get(scholarship_id)
                if data:
                    if "source" not in data:
                        data["source"] = "National & State Scholarship Portal"
                    return ScholarshipItem(**data)
            return None
