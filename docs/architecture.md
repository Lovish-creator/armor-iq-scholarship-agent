# System Architecture

## Overview Architecture

```mermaid
flowchart TD
    A[Student Intent Input] --> B[AI Agent Orchestrator]
    B --> C[Execution Planner]
    C --> D[ArmorIQ Client]
    
    D -->|capture_plan & get_intent_token| E[ArmorIQ Intent Proxy]
    E -->|Signed Intent Token| B

    B -->|Invoke MCP Tool with Intent Token| F{ArmorIQ Policy Check}

    F -->|ALLOW: Intent Matched| G[MCP Tool Layer]
    F -->|BLOCK: Out-of-Scope Action| H[Security Governance Event]

    G -->|Execute Tool Call| I[Mock Scholarship Portal API]
    I -->|Database Update| J[(SQLite Portal DB)]

    H -->|Aborts Consequential Tool| K[Proof of Non-Execution Counter: 0]
```

## Component Boundaries & Trust Model
1. **User Identity & Intent Boundary**: Student inputs natural language prompt + structured constraints (`scholarship_type: government`, `state: Punjab`).
2. **Planning & Token Boundary**: Planner creates step-by-step actions. ArmorIQ `capture_plan` and `get_intent_token` lock constraints into a signed cryptographic token.
3. **Governance Proxy Boundary**: Prior to invoking any MCP tool, `ArmorIQClient.invoke` checks the target action and parameters against the token's constraints.
4. **Tool Execution Boundary**: Consequential actions like `submit_application` check ArmorIQ decision. If `BLOCK`, execution is aborted and non-execution is logged in audit records.
