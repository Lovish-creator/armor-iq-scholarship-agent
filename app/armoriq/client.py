import os
import logging
from typing import Dict, Any, Optional


from app.armoriq.errors import (
    ArmorIQException,
    InvalidTokenException,
    IntentMismatchException,
    PolicyBlockedException,
    TokenExpiredException,
)


logger = logging.getLogger("armoriq_client")


try:
    from armoriq_sdk import ArmorIQClient

    HAS_OFFICIAL_SDK = True

except Exception:
    ArmorIQClient = None
    HAS_OFFICIAL_SDK = False


class PlanCaptureResult:
    def __init__(self, raw_sdk_obj: Any):
        self.raw_sdk_obj = raw_sdk_obj
        self.plan = getattr(raw_sdk_obj, "plan", None)
        self.plan_id = getattr(raw_sdk_obj, "plan_id", None) or getattr(raw_sdk_obj, "id", None)


class ArmorIQWrapperClient:
    """
    Minimal, strict wrapper around the official ArmorIQ Python SDK.

    This wrapper only calls the documented SDK methods and avoids
    speculative fallbacks. All failures are fail-closed: if the SDK is
    unavailable or an operation cannot be completed, an exception is
    raised so the application can refuse consequential actions.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ARMORIQ_API_KEY")

        if not self.api_key:
            raise ArmorIQException("ARMORIQ_API_KEY is required. Live ArmorIQ mode cannot run without credentials.")

        if not HAS_OFFICIAL_SDK:
            raise ArmorIQException("armoriq-sdk is not installed. Install the official ArmorIQ SDK.")

        try:
            # Initialize the official client using documented constructor
            self.client = ArmorIQClient(api_key=self.api_key)
        except Exception as exc:
            raise ArmorIQException(f"Failed to initialize ArmorIQ SDK: {exc}") from exc

        # Hold the last captured plan for token issuance
        self._last_plan = None

    def capture_plan(self, llm: str, prompt: str, plan: Dict[str, Any]) -> PlanCaptureResult:
        """Capture and validate an explicit execution plan via the SDK.

        The SDK expects a `plan` dict with `goal` and `steps`, where each
        step contains `action`, `mcp`, and optional `params`.
        """
        try:
            # Normalize plan into SDK shape
            sdk_plan = {
                "goal": plan.get("goal") if isinstance(plan, dict) else getattr(plan, "goal", prompt),
                "steps": [],
            }

            # Include constraints as a policy object expected by the SDK
            sdk_plan["policy"] = plan.get("constraints") if isinstance(plan, dict) else getattr(plan, "constraints", {})

            steps = plan.get("steps") if isinstance(plan, dict) else getattr(plan, "steps", [])
            for s in steps:
                if isinstance(s, dict):
                    action = s.get("action")
                    mcp = s.get("tool") or s.get("mcp")
                    params = s.get("inputs") or s.get("params") or {}
                else:
                    action = getattr(s, "action", None)
                    mcp = getattr(s, "tool", None) or getattr(s, "mcp", None)
                    params = getattr(s, "inputs", None) or getattr(s, "params", None) or {}

                sdk_plan["steps"].append({"action": action, "mcp": mcp, "params": params})

            logger.info("SDK plan being sent to ArmorIQ: %s", sdk_plan)
            captured = self.client.capture_plan(llm=llm, prompt=prompt, plan=sdk_plan)
            self._last_plan = captured
            return PlanCaptureResult(raw_sdk_obj=captured)

        except Exception as exc:
            raise ArmorIQException(f"ArmorIQ capture_plan failed: {exc}") from exc

    def get_intent_token_details(self, plan_capture: PlanCaptureResult, validity_seconds: int = 300) -> Dict[str, Any]:
        """Request a signed intent token for a captured plan using the SDK.

        Returns a dict containing the token string under `token_string` and
        raw SDK response under `raw`.
        """
        try:
            get_token = getattr(self.client, "get_intent_token", None)
            if not callable(get_token):
                raise ArmorIQException("ArmorIQ SDK get_intent_token API not available")

            # Call SDK correctly: `policy` is the second positional arg, so pass
            # `validity_seconds` as a keyword to avoid accidentally sending an
            # integer where a policy object is expected.
            # Extract policy from the captured plan (SDK expects a policy object)
            captured_policy = None
            try:
                captured_policy = getattr(plan_capture.raw_sdk_obj, "plan", {}).get("policy")
            except Exception:
                captured_policy = None

            token_resp = get_token(
                plan_capture.raw_sdk_obj,
                policy=captured_policy,
                validity_seconds=validity_seconds,
            )

            # SDK returns an `IntentToken` pydantic model instance on success.
            if not token_resp:
                raise InvalidTokenException("ArmorIQ issued no intent token")

            # Normalize response: keep the SDK object under `raw` and also
            # return the object itself as `token_string` so callers can pass
            # it directly into `invoke()` (the SDK accepts an IntentToken).
            token_id = getattr(token_resp, "token_id", None) or getattr(token_resp, "plan_id", None)
            return {
                "token_string": token_resp,
                "token_id": token_id,
                "api_key_used": True,
                "provider": "ArmorIQ SDK",
                "raw": token_resp,
            }

        except (InvalidTokenException, TokenExpiredException, IntentMismatchException, PolicyBlockedException):
            raise
        except Exception as exc:
            raise ArmorIQException(f"ArmorIQ get_intent_token failed: {exc}") from exc

    def get_intent_token(self, plan_capture: PlanCaptureResult, validity_seconds: int = 300) -> str:
        details = self.get_intent_token_details(plan_capture, validity_seconds)
        return details["token_string"]

    def invoke(self, mcp: str, action: str, intent_token: str, params: Optional[Dict[str, Any]] = None, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Invoke a protected MCP action via the SDK using the issued intent token.

        The SDK raises domain-specific exceptions for token/verification failures
        (e.g., InvalidTokenException, IntentMismatchException, PolicyBlockedException).
        """
        if not intent_token:
            raise InvalidTokenException("No ArmorIQ intent token supplied.")

        invoke_fn = getattr(self.client, "invoke", None)
        if not callable(invoke_fn):
            raise ArmorIQException("ArmorIQ SDK invoke API not available")

        try:
            result = invoke_fn(mcp=mcp, action=action, intent_token=intent_token, params=params or {}, user_email=user_email)
            # Successful invocation means the action was authorized and executed.
            return {"decision": "ALLOW", "raw": result}

        except Exception:
            # Propagate SDK exceptions for the orchestrator to handle
            raise
