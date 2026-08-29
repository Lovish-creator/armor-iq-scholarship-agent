import os
import sys
import json
import httpx

# Ensure proper utf-8 output encoding on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ZOP_PAT_TOKEN = os.getenv("ZOP_PAT_TOKEN", "zn_pat_b3967e9aaad9a7639ef12b976795cf384ebb557fbd8cdf19f5454fad42cb61f8")
ORG_ID = "a6fd7bda-ad5c-4a54-8d47-7aaaa57ef871"
SERVICE_ID = "d827c572-4af7-4069-9c56-fcc621ea2147"
MCP_URL = "https://api.zop.dev/mcp-server"

def call_zop_mcp_tool(tool_name: str, arguments: dict):
    headers = {
        "Authorization": f"Bearer {ZOP_PAT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    try:
        res = httpx.post(MCP_URL, json=payload, headers=headers, timeout=20.0)
        res.raise_for_status()
        return res.json()
    except Exception as exc:
        print(f"[Zop Error] Failed to call {tool_name}: {exc}")
        return None

def main():
    print(f"=== Querying Zop Service Status ({SERVICE_ID}) ===")
    res = call_zop_mcp_tool("get_service_overview", {
        "org_id": ORG_ID,
        "service_id": SERVICE_ID
    })
    if res and "result" in res:
        for item in res["result"].get("content", []):
            try:
                parsed = json.loads(item.get("text", "{}"))
                data = parsed.get("data", parsed)
                service = data.get("service", {})
                print(f"Service Name: {service.get('name')}")
                print(f"Status:       {service.get('status')} ({service.get('statusBucket')})")
                print(f"Repo:         {service.get('repoUrl')}")
                print(f"Branch:       {service.get('branch')}")
                print(f"Auto Deploy:  {service.get('autoDeploy')}")
                print(f"URL:          {data.get('url')}")
            except Exception:
                print(item.get("text", "")[:300])

    print("\n=== Querying Zop Deploy History ===")
    deploys = call_zop_mcp_tool("list_deploys", {
        "org_id": ORG_ID,
        "service_id": SERVICE_ID
    })
    if deploys and "result" in deploys:
        for item in deploys["result"].get("content", []):
            try:
                parsed = json.loads(item.get("text", "{}"))
                for d in parsed.get("data", []):
                    print(f"Revision {d.get('revision')} | Status: {d.get('status')} | Commit: {d.get('commit')[:8]} | Created: {d.get('createdAt')}")
            except Exception:
                print(item.get("text", "")[:300])

if __name__ == "__main__":
    main()
