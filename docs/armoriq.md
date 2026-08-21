# ArmorIQ Integration Reference

## Overview
ScholarShield utilizes the official `armoriq-sdk` Python client pattern to bind user intent to autonomous agent execution plans.

## SDK Core Methods Used

### 1. Plan Capture
```python
captured_plan = client.capture_plan(
    llm="gemini-3.6-flash",
    prompt="Find government engineering scholarships in Punjab I am eligible for and apply.",
    plan={
        "goal": "Apply for government scholarships in Punjab",
        "constraints": {
            "scholarship_type": "government",
            "target_state": "Punjab"
        },
        "steps": [...]
    }
)
```

### 2. Intent Token Minting
```python
intent_token = client.get_intent_token(captured_plan, validity_seconds=300)
```

### 3. Governed Action Invocation
```python
res = client.invoke(
    mcp_name="mcp_scholarship_tool",
    action="submit_application",
    intent_token=intent_token,
    inputs={
        "student_id": "student-demo-001",
        "scholarship_id": "SCH-GOV-PB-01",
        "scholarship_type": "government",
        "state": "Punjab"
    },
    user_email="student-demo-001@scholarshield.local"
)
```

## Exception Handling & Fail-Closed Guarantee
- `IntentMismatchException`: Raised when target action parameters violate intent constraints.
- `InvalidTokenException`: Raised when token signature is untrusted or missing.
- When an exception is caught, the application service invokes the tool with `armoriq_decision = BLOCK`, causing the portal API to abort execution and log non-execution.
