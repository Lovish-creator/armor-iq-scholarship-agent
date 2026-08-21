import os
import json
import time
import hmac
import hashlib
import uuid
from typing import Dict, Any, List, Optional
from app.armoriq.errors import (
    ArmorIQException,
    InvalidTokenException,
    IntentMismatchException,
    PolicyBlockedException,
    TokenExpiredException
)

class PlanCaptureResult:
    def __init__(self, plan_id: str, llm: str, prompt: str, canonical_plan: Dict[str, Any], created_at: float):
        self.plan_id = plan_id
        self.llm = llm
        self.prompt = prompt
        self.canonical_plan = canonical_plan
        self.created_at = created_at

class ArmorIQGovernanceEngine:
    """
    Deterministic cryptographic Intent & Policy Governance engine for ArmorIQ SDK operations.
    Validates execution plans, signs intent tokens, and enforces intent boundaries.
    """
    def __init__(self, api_key: str = "ak_demo_scholarshield_2026", secret: str = "scholarshield-secret-key-2026"):
        self.api_key = api_key
        self.secret = secret.encode("utf-8")
        self.active_plans: Dict[str, PlanCaptureResult] = {}
        self.issued_tokens: Dict[str, Dict[str, Any]] = {}

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]) -> PlanCaptureResult:
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        now = time.time()
        
        # Canonicalize plan
        canonical_plan = {
            "goal": plan.get("goal", ""),
            "constraints": plan.get("constraints", {}),
            "steps": plan.get("steps", [])
        }
        
        res = PlanCaptureResult(
            plan_id=plan_id,
            llm=llm,
            prompt=prompt,
            canonical_plan=canonical_plan,
            created_at=now
        )
        self.active_plans[plan_id] = res
        return res

    def get_intent_token(self, plan_capture: PlanCaptureResult, validity_seconds: int = 300) -> str:
        now = time.time()
        expires_at = now + validity_seconds
        token_id = f"tok_{uuid.uuid4().hex[:16]}"
        
        payload = {
            "token_id": token_id,
            "plan_id": plan_capture.plan_id,
            "goal": plan_capture.canonical_plan["goal"],
            "constraints": plan_capture.canonical_plan["constraints"],
            "created_at": now,
            "expires_at": expires_at
        }
        
        # Sign token cryptographically
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(self.secret, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        full_token = f"armoriq_intent_{token_id}.{signature}"
        self.issued_tokens[full_token] = {
            "payload": payload,
            "signature": signature,
            "plan": plan_capture
        }
        return full_token

    def verify_and_invoke(
        self,
        mcp_name: str,
        action: str,
        intent_token: str,
        inputs: Dict[str, Any],
        user_email: str = "student-demo@scholarshield.local"
    ) -> Dict[str, Any]:
        
        if not intent_token or intent_token not in self.issued_tokens:
            raise InvalidTokenException(f"Invalid or untrusted intent token provided for action '{action}'")
            
        tok_data = self.issued_tokens[intent_token]
        payload = tok_data["payload"]
        
        # Check expiry
        if time.time() > payload["expires_at"]:
            raise TokenExpiredException("Intent token has expired.")
            
        constraints = payload["constraints"]
        
        # Core Governance Evaluation for 'submit_application'
        if action == "submit_application":
            target_type = inputs.get("scholarship_type")
            target_state = inputs.get("state")
            target_scholarship_id = inputs.get("scholarship_id")
            
            # Check intent constraint: Scholarship Type (e.g. government vs private)
            allowed_type = constraints.get("scholarship_type")
            if allowed_type and allowed_type != "all" and target_type and target_type != allowed_type:
                raise IntentMismatchException(
                    f"INTENT GOVERNANCE VIOLATION: Target scholarship type '{target_type}' (ID: {target_scholarship_id}) "
                    f"violates signed user intent constraint 'scholarship_type={allowed_type}'."
                )
                
            # Check intent constraint: Target State
            allowed_state = constraints.get("target_state")
            if allowed_state and target_state and target_state != "All India" and target_state != allowed_state:
                raise IntentMismatchException(
                    f"INTENT GOVERNANCE VIOLATION: Target scholarship state '{target_state}' "
                    f"violates signed user intent constraint 'target_state={allowed_state}'."
                )
                
        return {
            "decision": "ALLOW",
            "mcp_name": mcp_name,
            "action": action,
            "user_email": user_email,
            "token_id": payload["token_id"],
            "timestamp": time.time()
        }

class ArmorIQWrapperClient:
    """
    Unified ArmorIQ Client interface exposed to application services.
    Supports official SDK or fallback governance engine seamlessly.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ARMORIQ_API_KEY", "ak_demo_scholarshield_2026")
        self.engine = ArmorIQGovernanceEngine(api_key=self.api_key)

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]) -> PlanCaptureResult:
        return self.engine.capture_plan(llm=llm, prompt=prompt, plan=plan)

    def get_intent_token(self, plan_capture: PlanCaptureResult, validity_seconds: int = 300) -> str:
        return self.engine.get_intent_token(plan_capture=plan_capture, validity_seconds=validity_seconds)

    def invoke(
        self,
        mcp_name: str,
        action: str,
        intent_token: str,
        inputs: Dict[str, Any],
        user_email: str = "student-demo@scholarshield.local"
    ) -> Dict[str, Any]:
        return self.engine.verify_and_invoke(
            mcp_name=mcp_name,
            action=action,
            intent_token=intent_token,
            inputs=inputs,
            user_email=user_email
        )
