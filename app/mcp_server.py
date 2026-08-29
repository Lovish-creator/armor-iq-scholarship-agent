import uvicorn
from fastapi import FastAPI, Request
from typing import Any, Dict, Optional, List
from app.tools.scholarship_tools import ScholarshipMCPTools

app = FastAPI(title="Scholarship MCP Server", version="1.0.0")
tools = ScholarshipMCPTools()

TOOL_DEFINITIONS = [
    {
        "name": "search_scholarships",
        "description": "Search scholarships by type and state",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scholarship_type": {"type": "string", "description": "Type of scholarship (government, private, all)"},
                "state": {"type": "string", "description": "Target state"}
            }
        }
    },
    {
        "name": "check_eligibility",
        "description": "Check student eligibility for a scholarship",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string"},
                "scholarship_id": {"type": "string"}
            },
            "required": ["student_id", "scholarship_id"]
        }
    },
    {
        "name": "prepare_application",
        "description": "Prepare a scholarship application draft",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string"},
                "scholarship_id": {"type": "string"}
            },
            "required": ["student_id", "scholarship_id"]
        }
    },
    {
        "name": "submit_application",
        "description": "Submit a scholarship application with ArmorIQ intent token",
        "inputSchema": {
            "type": "object",
            "properties": {
                "student_id": {"type": "string"},
                "scholarship_id": {"type": "string"},
                "intent_token": {"type": "string"},
                "armoriq_decision": {"type": "string", "default": "ALLOW"}
            },
            "required": ["student_id", "scholarship_id", "intent_token"]
        }
    }
]

@app.post("/mcp")
@app.post("/")
async def handle_mcp_jsonrpc(request: Request):
    data = await request.json()
    req_id = data.get("id", 1)
    method = data.get("method")
    params = data.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "scholarship", "version": "1.0.0"}
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOL_DEFINITIONS
            }
        }

    elif method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        action = name.replace("scholarship.", "")

        if action == "search_scholarships":
            res = tools.search_scholarships(**arguments)
        elif action == "check_eligibility":
            res = tools.check_eligibility(**arguments)
        elif action == "prepare_application":
            res = tools.prepare_application(**arguments)
        elif action == "submit_application":
            res = tools.submit_application(**arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method {name} not found"}
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": str(res)}],
                "isError": False
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {}
    }

if __name__ == "__main__":
    uvicorn.run("app.mcp_server:app", host="127.0.0.1", port=9000, log_level="info")