import os
import json
import time
import hmac
import hashlib
import uuid
import logging
from typing import Dict, Any, List, Optional
from app.armoriq.errors import (
    ArmorIQException,
    InvalidTokenException,
    IntentMismatchException,
    PolicyBlockedException,
    TokenExpiredException
)

# Attempt official SDK import
try:
    from armoriq_sdk import ArmorIQClient as OfficialArmorIQClient
    HAS_OFFICIAL_SDK = True
except ImportError:
    HAS_OFFICIAL_SDK = False

logger = logging.getLogger("armoriq_client")

class PlanCaptureResult:
    def __init__(self, plan_id: str, llm: str, prompt: str, canonical_plan: Dict[str, Any], created_at: float, raw_sdk_obj: Any = None):
        self.plan_id = plan_id
        self.llm = llm
        self.prompt = prompt
        self.canonical_plan = canonical_plan
        self.created_at = created_at
        self.raw_sdk_obj = raw_sdk_obj

class ArmorIQWrapperClient:
    """
    Unified ArmorIQ Client interface supporting both live official ArmorIQ SDK 
    (via `armoriq_sdk.ArmorIQClient`) and local deterministic fallback governance engine.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("ARMORIQ_API_KEY", "ak_demo_scholarshield_2026")
        self.user_id = user_id or os.getenv("ARMORIQ_USER_ID", "student-demo-001")
        self.agent_id = agent_id or os.getenv("ARMORIQ_AGENT_ID", "scholarship-governed-agent-v1")
        
        self.official_client = None
        if HAS_OFFICIAL_SDK and self.api_key and not self.api_key.startswith("ak_demo_"):
            try:
                self.official_client = OfficialArmorIQClient(
                    api_key=self.api_key,
                    user_id=self.user_id,
                    agent_id=self.agent_id
                )
                logger.info("Initialized official ArmorIQ SDK client connected to live ArmorIQ platform.")
            except Exception as e:
                logger.warning(f"Official ArmorIQClient init error: {e}. Falling back to internal engine.")

        # Internal deterministic governance engine for offline/test/demo mode
        self.secret = self.api_key.encode("utf-8")
        self.active_plans: Dict[str, PlanCaptureResult] = {}
        self.issued_tokens: Dict[str, Dict[str, Any]] = {}

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]) -> PlanCaptureResult:
        if self.official_client:
            try:
                raw_cap = self.official_client.capture_plan(llm=llm, prompt=prompt, plan=plan)
                plan_id = getattr(raw_cap, "plan_id", f"plan_{uuid.uuid4().hex[:12]}")
                return PlanCaptureResult(
                    plan_id=plan_id,
                    llm=llm,
                    prompt=prompt,
                    canonical_plan=plan,
                    created_at=time.time(),
                    raw_sdk_obj=raw_cap
                )
            except Exception as e:
                logger.warning(f"Live ArmorIQ capture_plan failed ({e}). Using deterministic engine.")

        # Local Engine Capture
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        now = time.time()
        res = PlanCaptureResult(
            plan_id=plan_id,
            llm=llm,
            prompt=prompt,
            canonical_plan=plan,
            created_at=now
        )
        self.active_plans[plan_id] = res
        return res

    def get_intent_token(self, plan_capture: PlanCaptureResult, validity_seconds: int = 300) -> str:
        if self.official_client and plan_capture.raw_sdk_obj:
            try:
                tok = self.official_client.get_intent_token(plan_capture.raw_sdk_obj)
                if tok:
                    return str(tok)
            except Exception as e:
                logger.warning(f"Live ArmorIQ get_intent_token failed ({e}). Using deterministic engine.")

        # Local Engine Token Generation
        now = time.time()
        expires_at = now + validity_seconds
        token_id = f"tok_{uuid.uuid4().hex[:16]}"
        
        payload = {
            "token_id": token_id,
            "plan_id": plan_capture.plan_id,
            "goal": plan_capture.canonical_plan.get("goal", ""),
            "constraints": plan_capture.canonical_plan.get("constraints", {}),
            "created_at": now,
            "expires_at": expires_at
        }
        
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(self.secret, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        full_token = f"armoriq_intent_{token_id}.{signature}"
        self.issued_tokens[full_token] = {
            "payload": payload,
            "signature": signature,
            "plan": plan_capture
        }
        return full_token

    def invoke(
        self,
        mcp_name: str,
        action: str,
        intent_token: str,
        inputs: Dict[str, Any],
        user_email: str = "student-demo@scholarshield.local"
    ) -> Dict[str, Any]:
        if self.official_client and not intent_token.startswith("armoriq_intent_"):
            try:
                live_res = self.official_client.invoke(
                    mcp_name=mcp_name,
                    action=action,
                    intent_token=intent_token,
                    inputs=inputs,
                    user_email=user_email
                )
                return {"decision": "ALLOW", "raw": live_res}
            except Exception as e:
                logger.warning(f"Live ArmorIQ invoke check: {e}")
                # Raise appropriate ArmorIQ Exception if live platform blocks
                if "intent" in str(e).lower() or "scope" in str(e).lower() or "mismatch" in str(e).lower():
                    raise IntentMismatchException(f"Live ArmorIQ Intent Governance Block: {e}")
                raise ArmorIQException(f"ArmorIQ SDK Error: {e}")

        # Local Engine Verification & Intent Enforcement
        if not intent_token or intent_token not in self.issued_tokens:
            raise InvalidTokenException(f"Invalid or untrusted intent token provided for action '{action}'")
            
        tok_data = self.issued_tokens[intent_token]
        payload = tok_data["payload"]
        
        if time.time() > payload["expires_at"]:
            raise TokenExpiredException("Intent token has expired.")
            
        constraints = payload.get("constraints", {})
        
        # Core Intent Scope Check for Consequential Actions
        if action == "submit_application":
            target_type = inputs.get("scholarship_type")
            target_state = inputs.get("state")
            target_scholarship_id = inputs.get("scholarship_id")
            
            allowed_type = constraints.get("scholarship_type")
            if allowed_type and allowed_type != "all" and target_type and target_type != allowed_type:
                raise IntentMismatchException(
                    f"INTENT GOVERNANCE VIOLATION: Target scholarship type '{target_type}' (ID: {target_scholarship_id}) "
                    f"violates signed user intent constraint 'scholarship_type={allowed_type}'."
                )
                
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
