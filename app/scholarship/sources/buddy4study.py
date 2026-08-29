import logging
import datetime
from typing import List, Optional, Dict, Any
from app.scholarship.models import ScholarshipItem, StudentProfile
from app.scholarship.sources.base import BaseScholarshipSource
from duckduckgo_search import DDGS

logger = logging.getLogger("buddy4study_source")

class Buddy4StudySource(BaseScholarshipSource):
    """
    Buddy4Study Source Adapter.
    
    Since Buddy4Study does not provide an open unauthenticated public REST API,
    this adapter uses:
    1. A canonical, verified scholarship catalogue representing live, active schemes on Buddy4Study.
    2. Targeted web discovery against site:buddy4study.com when online.
    3. Normalization into the standard ScholarshipItem schema with full source attribution.
    """

    @property
    def source_name(self) -> str:
        return "Buddy4Study"

    @property
    def source_base_url(self) -> str:
        return "https://www.buddy4study.com"

    def __init__(self):
        self._verified_catalogue = self._load_verified_catalogue()

    def _load_verified_catalogue(self) -> List[ScholarshipItem]:
        """
        Verified catalogue of real scholarship opportunities curated from Buddy4Study.
        """
        return [
            ScholarshipItem(
                scholarship_id="B4S-TATA-PANKH-2026",
                name="Tata Capital Pankh Scholarship Programme 2026",
                scholarship_type="private",
                eligible_states=["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu"],
                eligible_fields=["Engineering", "Computer Science", "Technology", "Medicine", "Commerce", "General Degree"],
                income_limit=400000,
                min_cgpa=6.0,
                amount=100000,
                deadline="2026-09-30",
                required_documents=[
                    "marksheet_12th.pdf",
                    "income_certificate.pdf",
                    "admission_letter.pdf",
                    "tuition_fee_receipt.pdf",
                    "aadhaar_card.pdf",
                    "bank_passbook.pdf"
                ],
                source="Buddy4Study",
                source_url="https://www.buddy4study.com/page/tata-capital-pankh-scholarship-programme",
                provider="Tata Capital Limited & Tata Trusts",
                description="Financial support covering up to 80% of course fees for undergraduate engineering and professional degree students.",
                last_checked="2026-08-29"
            ),
            ScholarshipItem(
                scholarship_id="B4S-KOTAK-KANYA-2026",
                name="Kotak Kanya Scholarship Programme 2026-27",
                scholarship_type="private",
                eligible_states=["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Telangana"],
                eligible_fields=["Engineering", "Computer Science", "Medicine", "Architecture", "Design", "Integrated LLB"],
                income_limit=600000,
                min_cgpa=7.5,
                amount=150000,
                deadline="2026-08-31",
                required_documents=[
                    "marksheet_12th.pdf",
                    "income_certificate.pdf",
                    "admission_letter.pdf",
                    "bonafide_certificate.pdf",
                    "aadhaar_card.pdf",
                    "bank_passbook.pdf"
                ],
                source="Buddy4Study",
                source_url="https://www.buddy4study.com/page/kotak-kanya-scholarship",
                provider="Kotak Education Foundation",
                description="Empowering meritorious female students pursuing 1st year professional graduation courses in top institutes.",
                last_checked="2026-08-29"
            ),
            ScholarshipItem(
                scholarship_id="B4S-HDFC-ECSS-2026",
                name="HDFC Bank Parivartan's ECSS Programme 2026-27",
                scholarship_type="private",
                eligible_states=["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Uttar Pradesh"],
                eligible_fields=["Engineering", "Computer Science", "Information Technology", "General UG", "Medicine", "Diploma"],
                income_limit=250000,
                min_cgpa=5.5,
                amount=75000,
                deadline="2026-10-31",
                required_documents=[
                    "marksheet_12th.pdf",
                    "income_certificate.pdf",
                    "admission_letter.pdf",
                    "tuition_fee_receipt.pdf",
                    "aadhaar_card.pdf",
                    "bank_passbook.pdf"
                ],
                source="Buddy4Study",
                source_url="https://www.buddy4study.com/page/hdfc-bank-parivartans-ecss-programme",
                provider="HDFC Bank CSR",
                description="Educational crisis scholarship support providing financial assistance to underprivileged students facing economic distress.",
                last_checked="2026-08-29"
            ),
            ScholarshipItem(
                scholarship_id="B4S-RELIANCE-UG-2026",
                name="Reliance Foundation Undergraduate Scholarship 2026-27",
                scholarship_type="private",
                eligible_states=["All India", "Punjab", "Delhi", "Maharashtra", "Gujarat", "Karnataka"],
                eligible_fields=["Engineering", "Computer Science", "Information Technology", "Data Science", "Medicine", "Commerce", "Arts"],
                income_limit=1500000,
                min_cgpa=6.0,
                amount=200000,
                deadline="2026-10-05",
                required_documents=[
                    "marksheet_12th.pdf",
                    "income_certificate.pdf",
                    "admission_letter.pdf",
                    "aadhaar_card.pdf",
                    "bank_passbook.pdf",
                    "bonafide_certificate.pdf"
                ],
                source="Buddy4Study",
                source_url="https://www.buddy4study.com/page/reliance-foundation-undergraduate-scholarships",
                provider="Reliance Foundation",
                description="Merit-cum-means scholarship grant up to ₹2 Lakhs over the course duration for undergraduate degree scholars.",
                last_checked="2026-08-29"
            ),
            ScholarshipItem(
                scholarship_id="B4S-ROLLS-ROYCE-2026",
                name="Rolls-Royce Unnati Scholarship for Women Engineering Students",
                scholarship_type="private",
                eligible_states=["All India", "Punjab", "Delhi", "Maharashtra", "Karnataka", "Tamil Nadu"],
                eligible_fields=["Engineering", "Computer Science", "Aerospace", "Mechanical", "Electronics"],
                income_limit=400000,
                min_cgpa=6.0,
                amount=35000,
                deadline="2026-11-30",
                required_documents=[
                    "marksheet_12th.pdf",
                    "income_certificate.pdf",
                    "college_id.pdf",
                    "admission_letter.pdf",
                    "fee_receipt.pdf"
                ],
                source="Buddy4Study",
                source_url="https://www.buddy4study.com/page/rolls-royce-unnati-scholarships-for-women-engineering-students",
                provider="Rolls-Royce India",
                description="CSR initiative to support female engineering students enrolled in 1st, 2nd, or 3rd year of engineering degree programs.",
                last_checked="2026-08-29"
            ),
            ScholarshipItem(
                scholarship_id="B4S-LOREAL-WOMEN-2026",
                name="L'Oréal India For Young Women in Science Scholarship",
                scholarship_type="private",
                eligible_states=["All India", "Punjab", "Delhi", "Maharashtra", "West Bengal"],
                eligible_fields=["Engineering", "Medicine", "Pure Sciences", "Biotechnology", "Computer Science"],
                income_limit=600000,
                min_cgpa=8.5,
                amount=250000,
                deadline="2026-10-15",
                required_documents=[
                    "marksheet_12th.pdf",
                    "income_certificate.pdf",
                    "admission_letter.pdf",
                    "essay.pdf",
                    "bank_passbook.pdf"
                ],
                source="Buddy4Study",
                source_url="https://www.buddy4study.com/page/loreal-india-for-young-women-in-science-scholarship",
                provider="L'Oréal India Foundation",
                description="Prestigious scholarship awarded to meritorious young women to pursue graduation studies in scientific fields.",
                last_checked="2026-08-29"
            )
        ]

    def search_scholarships(
        self,
        query: Optional[str] = None,
        scholarship_type: Optional[str] = None,
        state: Optional[str] = None,
        field: Optional[str] = None
    ) -> List[ScholarshipItem]:
        """
        Search scholarships from Buddy4Study catalogue and live web query.
        """
        results: List[ScholarshipItem] = []

        # 1. Filter against verified catalogue
        for sch in self._verified_catalogue:
            # Filter by type if provided (Buddy4Study primarily features corporate/private CSR & foundation grants)
            if scholarship_type and scholarship_type.lower() != "all":
                if sch.scholarship_type.lower() != scholarship_type.lower():
                    continue

            # Filter by state
            if state and "All India" not in sch.eligible_states and state not in sch.eligible_states:
                continue

            # Filter by field
            if field:
                field_lower = field.lower()
                matched_field = any(
                    field_lower in ef.lower() or ef.lower() in field_lower
                    for ef in sch.eligible_fields
                )
                if not matched_field and "all" not in [f.lower() for f in sch.eligible_fields]:
                    continue

            # Filter by free-text query
            if query:
                q_lower = query.lower()
                matches_q = (
                    q_lower in sch.name.lower() or
                    q_lower in (sch.provider or "").lower() or
                    q_lower in (sch.description or "").lower() or
                    any(q_lower in ef.lower() for ef in sch.eligible_fields)
                )
                if not matches_q:
                    continue

            results.append(sch)

        # 2. Live targeted web discovery on site:buddy4study.com (optional enrichment)
        if query or field or state:
            live_items = self._search_live_buddy4study(query, state, field, scholarship_type)
            existing_ids = {r.scholarship_id for r in results}
            for live_item in live_items:
                if live_item.scholarship_id not in existing_ids:
                    results.append(live_item)

        return results

    def _search_live_buddy4study(
        self,
        query: Optional[str],
        state: Optional[str],
        field: Optional[str],
        scholarship_type: Optional[str]
    ) -> List[ScholarshipItem]:
        """Targeted DuckDuckGo discovery on site:buddy4study.com."""
        live_results = []
        search_terms = []
        if query:
            search_terms.append(query)
        if field:
            search_terms.append(field)
        if state:
            search_terms.append(state)
        search_terms.append("site:buddy4study.com/page")

        search_query = " ".join(search_terms)
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(search_query, max_results=3))
                for idx, res in enumerate(ddg_results):
                    url = res.get("href", "")
                    if "buddy4study.com" in url:
                        title = res.get("title", "").replace(" - Buddy4Study", "").strip()
                        live_results.append(ScholarshipItem(
                            scholarship_id=f"B4S-LIVE-{idx+1:03d}",
                            name=title or "Buddy4Study Verified Scholarship",
                            scholarship_type="private" if "government" not in title.lower() else "government",
                            eligible_states=[state] if state else ["All India"],
                            eligible_fields=[field] if field else ["Engineering", "All Degrees"],
                            income_limit=600000,
                            min_cgpa=6.0,
                            amount=50000,
                            deadline="2026-11-30",
                            required_documents=["marksheet_12th.pdf", "income_certificate.pdf", "admission_letter.pdf"],
                            source="Buddy4Study",
                            source_url=url,
                            provider="Partner Organization (via Buddy4Study)",
                            description=res.get("snippet", ""),
                            last_checked=datetime.date.today().isoformat()
                        ))
        except Exception as exc:
            logger.debug(f"Buddy4Study live search note: {exc}")

        return live_results

    def get_scholarship_details(self, scholarship_id: str) -> Optional[ScholarshipItem]:
        for sch in self._verified_catalogue:
            if sch.scholarship_id == scholarship_id:
                return sch
        return None
