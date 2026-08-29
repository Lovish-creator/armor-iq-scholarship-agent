from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.scholarship.models import ScholarshipItem, StudentProfile, EligibilityResult

class BaseScholarshipSource(ABC):
    """
    Abstract interface for scholarship data sources (e.g., Buddy4Study,
    National Scholarship Portal (NSP), State Portals, Vidyasaarathi).
    
    Ensures any new provider can be cleanly plugged in or swapped without
    modifying the core agent or ArmorIQ governance layer.
    """
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the source (e.g. 'Buddy4Study')."""
        pass

    @property
    @abstractmethod
    def source_base_url(self) -> str:
        """Root URL for source attribution."""
        pass

    @abstractmethod
    def search_scholarships(
        self,
        query: Optional[str] = None,
        scholarship_type: Optional[str] = None,
        state: Optional[str] = None,
        field: Optional[str] = None
    ) -> List[ScholarshipItem]:
        """
        Search for scholarships normalized to the standard ScholarshipItem schema.
        """
        pass

    @abstractmethod
    def get_scholarship_details(self, scholarship_id: str) -> Optional[ScholarshipItem]:
        """
        Fetch details for a specific scholarship identifier.
        """
        pass

    def check_eligibility(self, student: StudentProfile, scholarship: ScholarshipItem) -> EligibilityResult:
        """
        Default standard eligibility evaluation against student profile.
        """
        rejection_reasons = []

        # 1. State matching
        if scholarship.eligible_states and "All India" not in scholarship.eligible_states:
            if student.state not in scholarship.eligible_states:
                rejection_reasons.append(f"State mismatch: Requires {', '.join(scholarship.eligible_states)} (student is in {student.state})")

        # 2. Field matching
        if scholarship.eligible_fields:
            student_field_lower = student.education.lower()
            field_matched = any(
                ef.lower() in student_field_lower or student_field_lower in ef.lower()
                for ef in scholarship.eligible_fields
            )
            if not field_matched and "all" not in [f.lower() for f in scholarship.eligible_fields]:
                rejection_reasons.append(f"Field of study mismatch: Requires {', '.join(scholarship.eligible_fields)}")

        # 3. Income ceiling
        if scholarship.income_limit and scholarship.income_limit > 0:
            if student.annual_income > scholarship.income_limit:
                rejection_reasons.append(f"Income limit exceeded: ₹{student.annual_income:,} exceeds limit of ₹{scholarship.income_limit:,}")

        # 4. Academic CGPA
        if scholarship.min_cgpa and scholarship.min_cgpa > 0:
            if student.cgpa < scholarship.min_cgpa:
                rejection_reasons.append(f"Academic requirement not met: {student.cgpa} CGPA is below {scholarship.min_cgpa} minimum")

        return EligibilityResult(
            student_id=student.student_id,
            scholarship_id=scholarship.scholarship_id,
            scholarship_name=scholarship.name,
            scholarship_type=scholarship.scholarship_type,
            is_eligible=len(rejection_reasons) == 0,
            rejection_reasons=rejection_reasons
        )

    def is_available(self) -> bool:
        """Health check / availability probe."""
        return True
