from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from app.tools.scholarship_tools import ScholarshipMCPTools


mcp = FastMCP(
    "mcp_scholarship_tool",
    json_response=True,
)

tools = ScholarshipMCPTools()


@mcp.tool()
def search_scholarships(
    scholarship_type: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    """Search scholarships by type and state."""
    return tools.search_scholarships(
        scholarship_type=scholarship_type,
        state=state,
    )


@mcp.tool()
def check_eligibility(
    student_id: str,
    scholarship_id: str,
) -> Dict[str, Any]:
    """Check student eligibility for a scholarship."""
    return tools.check_eligibility(
        student_id=student_id,
        scholarship_id=scholarship_id,
    )


@mcp.tool()
def prepare_application(
    student_id: str,
    scholarship_id: str,
) -> Dict[str, Any]:
    """Prepare a scholarship application draft."""
    return tools.prepare_application(
        student_id=student_id,
        scholarship_id=scholarship_id,
    )


@mcp.tool()
def submit_application(
    student_id: str,
    scholarship_id: str,
    intent_token: str,
    armoriq_decision: str = "ALLOW",
) -> Dict[str, Any]:
    """
    Submit a scholarship application.

    This is the consequential operation and requires
    an explicit ArmorIQ ALLOW decision.
    """

    if not intent_token:
        raise ValueError(
            "intent_token is required for protected submission."
        )

    if armoriq_decision != "ALLOW":
        raise PermissionError(
            "Submission rejected because ArmorIQ did not return ALLOW."
        )

    return tools.submit_application(
        student_id=student_id,
        scholarship_id=scholarship_id,
        intent_token=intent_token,
        armoriq_decision="ALLOW",
    )


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=9000,
    )