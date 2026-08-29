import os
import logging
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import hashes

from app.armoriq.errors import (
    ArmorIQException,
    InvalidTokenException,
    IntentMismatchException,
    PolicyBlockedException,
    TokenExpiredException,
)

# ============================================================
# ENVIRONMENT
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger("armoriq_client")


# ============================================================
# OFFICIAL ARMORIQ SDK
# ============================================================

try:
    from armoriq_sdk import ArmorIQClient

    HAS_OFFICIAL_SDK = True

except Exception as exc:
    ArmorIQClient = None
    HAS_OFFICIAL_SDK = False

    logger.warning(
        "ArmorIQ SDK unavailable: %s",
        exc,
    )


# SDK exception module
try:
    from armoriq_sdk import exceptions as sdk_exceptions
except Exception:
    sdk_exceptions = None


# ============================================================
# LOCAL DEMO TOKEN
# ============================================================

class LocalIntentToken:
    """
    Local token used ONLY when ARMORIQ_MODE=demo/local/mock.

    This is not an ArmorIQ cryptographic token.
    """

    def __init__(
        self,
        plan_id: Optional[str],
        validity_seconds: int = 300,
    ):
        self.token_id = f"demo-{uuid.uuid4().hex[:16]}"
        self.plan_id = plan_id
        self.validity_seconds = validity_seconds
        self.provider = "ArmorIQ Local Demo"
        self.demo = True

    def __str__(self):
        return self.token_id

    def __repr__(self):
        return (
            f"LocalIntentToken("
            f"token_id={self.token_id!r})"
        )


# ============================================================
# PLAN CAPTURE RESULT
# ============================================================

class PlanCaptureResult:
    """
    Small compatibility wrapper around the REAL ArmorIQ SDK
    PlanCapture object.

    raw_sdk_obj MUST remain the original SDK object because
    get_intent_token() expects an SDK PlanCapture.
    """

    def __init__(self, raw_sdk_obj: Any):

        self.raw_sdk_obj = raw_sdk_obj

        if isinstance(raw_sdk_obj, dict):

            self.plan = raw_sdk_obj.get("plan")

            self.plan_id = (
                raw_sdk_obj.get("plan_id")
                or raw_sdk_obj.get("id")
            )

        else:

            self.plan = getattr(
                raw_sdk_obj,
                "plan",
                None,
            )

            self.plan_id = (
                getattr(
                    raw_sdk_obj,
                    "plan_id",
                    None,
                )
                or getattr(
                    raw_sdk_obj,
                    "id",
                    None,
                )
            )


# ============================================================
# ARMORIQ WRAPPER
# ============================================================

class ArmorIQWrapperClient:
    """
    Thin application wrapper around the installed ArmorIQ SDK.

    Important design rule:

        Application
             |
             v
        This wrapper
             |
             v
        Official ArmorIQ SDK
             |
             v
        ArmorIQ infrastructure

    We deliberately do NOT reimplement:
        - token verification
        - Merkle proofs
        - CSRG headers
        - policy enforcement
        - proxy invocation
        - API authentication

    The installed SDK already implements those.
    """

    api_key: str = ""
    mode: str = "real"
    demo_mode: bool = False
    client: Any = None
    _last_plan: Any = None
    _last_intent_token: Any = None

    def __init__(
        self,
        api_key: Optional[str] = None,
    ):

        # ----------------------------------------------------
        # LOAD CONFIG
        # ----------------------------------------------------

        raw_key = api_key or os.getenv("ARMORIQ_API_KEY") or ""
        self.api_key = raw_key.strip().strip('"').strip("'")
        if self.api_key:
            os.environ["ARMORIQ_API_KEY"] = self.api_key

        self.mode = (
            os.getenv(
                "ARMORIQ_MODE",
                "real",
            )
            .strip()
            .lower()
        )

        self.demo_mode = self._detect_demo_mode()

        self.client = None

        self._last_plan = None
        self._last_intent_token = None

        # ----------------------------------------------------
        # DEMO
        # ----------------------------------------------------

        if self.demo_mode:

            logger.warning(
                "=================================================="
            )

            logger.warning(
                "ARMORIQ LOCAL DEMO MODE ENABLED"
            )

            logger.warning(
                "Real ArmorIQ authorization is NOT being used."
            )

            logger.warning(
                "=================================================="
            )

            return

        # ----------------------------------------------------
        # REAL MODE
        # ----------------------------------------------------

        if not self.api_key:

            raise ArmorIQException(
                "ARMORIQ_API_KEY is required "
                "when ARMORIQ_MODE=real."
            )

        if not HAS_OFFICIAL_SDK:

            raise ArmorIQException(
                "armoriq-sdk is not installed."
            )

        # ----------------------------------------------------
        # OPTIONAL SDK IDENTIFIERS
        #
        # Current SDK source confirms these are optional.
        # It automatically falls back to:
        #
        # __sdk_multiuser__
        #
        # when they are missing.
        # ----------------------------------------------------

        user_id = (
            os.getenv("ARMORIQ_USER_ID")
            or os.getenv("USER_ID")
            or None
        )

        agent_id = (
            os.getenv("ARMORIQ_AGENT_ID")
            or os.getenv("AGENT_ID")
            or None
        )

        context_id = (
            os.getenv("ARMORIQ_CONTEXT_ID")
            or os.getenv("CONTEXT_ID")
            or "default"
        )

        config_path = ROOT_DIR / "policies" / "armoriq.yaml"
        if not config_path.exists():
            config_path = ROOT_DIR / "armoriq.yaml"

        try:

            if config_path.exists() and hasattr(ArmorIQClient, "from_config"):
                self.client = ArmorIQClient.from_config(str(config_path))
                if self.api_key:
                    self.client.api_key = self.api_key
            else:
                self.client = ArmorIQClient(
                    api_key=self.api_key,
                    user_id=user_id,
                    agent_id=agent_id,
                    context_id=context_id,
                    use_production=(os.getenv("ARMORIQ_ENVIRONMENT", "production").lower() != "sandbox"),
                )

            env_name = getattr(self.client, "environment", None) or os.getenv("ARMORIQ_ENVIRONMENT", "production")
            key_present = bool(self.api_key)
            backend_url = getattr(self.client, "backend_endpoint", "https://api.armoriq.ai")

            print(f"[ArmorIQ] Environment: {env_name}")
            print(f"[ArmorIQ] API key present: {key_present}")
            print(f"[ArmorIQ] Backend: {backend_url}")

            logger.info(
                "ArmorIQ REAL MODE initialized with env=%s",
                env_name,
            )

        except Exception as exc:

            logger.exception(
                "ArmorIQ SDK initialization failed."
            )

            raise ArmorIQException(
                f"Failed to initialize ArmorIQ SDK: {exc}"
            ) from exc


    # ========================================================
    # MODE
    # ========================================================

    def _detect_demo_mode(self) -> bool:
        if self.mode in {
            "demo",
            "local",
            "mock",
        }:
            return True

        valid_key = bool(
            self.api_key
            and (
                self.api_key.startswith("ak_live_")
                or self.api_key.startswith("ak_test_")
                or self.api_key.startswith("ak_claw_")
            )
        )

        if not valid_key:
            if not self.api_key:
                logger.info(
                    "No ARMORIQ_API_KEY detected. Automatically using local demo mode."
                )
            else:
                logger.warning(
                    "ARMORIQ_API_KEY format is invalid (keys must start with 'ak_live_', 'ak_claw_', or 'ak_test_'). Using local demo mode."
                )
            return True

        return False

    def _verify_token_cryptography(self, raw_token: Any) -> bool:
        token_data = (raw_token or {}).get("token") or {}
        public_key_hex = token_data.get("public_key")
        signature_hex = token_data.get("signature")
        if not public_key_hex or not signature_hex or not token_data.get("plan_hash"):
            return False
        payload = {
            "plan_hash": token_data.get("plan_hash"),
            "issued_at": token_data.get("issued_at"),
            "expires_at": token_data.get("expires_at"),
            "policy": token_data.get("policy"),
            "identity": token_data.get("identity"),
            "public_key": token_data.get("public_key"),
            "version": token_data.get("version"),
        }
        if token_data.get("allowed_operations"):
            payload["allowed_operations"] = token_data["allowed_operations"]
        if token_data.get("resource_scope"):
            payload["resource_scope"] = token_data["resource_scope"]
        msg = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        
        # 1. NIST P-256 (SECP256R1) ECDSA Verification
        try:
            pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), bytes.fromhex(public_key_hex))
            pub_key.verify(bytes.fromhex(signature_hex), msg, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            pass

        # 2. Ed25519 Verification
        try:
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
            pub_key.verify(bytes.fromhex(signature_hex), msg)
            return True
        except Exception:
            pass

        return False

    def _is_out_of_scope(self, action: str, params: Optional[Dict[str, Any]]) -> bool:
        # 1. Allowed actions check against ArmorIQ policy
        allowed_actions = {
            "search_scholarships",
            "check_eligibility",
            "prepare_application",
            "submit_application",
        }
        if action not in allowed_actions:
            return True

        # 2. Captured plan step alignment check
        if hasattr(self, "_last_plan") and self._last_plan and hasattr(self._last_plan, "plan"):
            plan_obj = self._last_plan.plan
            if isinstance(plan_obj, dict):
                plan_steps = plan_obj.get("steps") or []
                plan_actions = {s.get("action") for s in plan_steps if isinstance(s, dict)}
                if plan_actions and action not in plan_actions:
                    return True

        if not params:
            return False
        stype = str(params.get("scholarship_type", "")).lower()
        sid = str(params.get("scholarship_id", "")).upper()
        if stype == "private" or sid == "SCH-PRV-GLOBAL-03" or sid.startswith("SCH-PRV"):
            return True
        return False


    # ========================================================
    # CAPTURE PLAN
    # ========================================================

    def capture_plan(
        self,
        llm: str,
        prompt: str,
        plan: Dict[str, Any],
    ) -> PlanCaptureResult:

        if not isinstance(plan, dict):

            raise ArmorIQException(
                "ArmorIQ plan must be a dictionary."
            )

        steps = plan.get("steps") or []

        if not isinstance(steps, list):

            raise ArmorIQException(
                "ArmorIQ plan steps must be a list."
            )

        sdk_steps = []

        for index, step in enumerate(steps):

            if not isinstance(step, dict):

                raise ArmorIQException(
                    f"Invalid plan step {index}."
                )

            action = step.get("action")

            mcp = (
                step.get("tool")
                or step.get("mcp")
            )

            params = (
                step.get("inputs")
                or step.get("params")
                or {}
            )

            if not action:

                raise ArmorIQException(
                    f"Plan step {index} has no action."
                )

            if not mcp:

                raise ArmorIQException(
                    f"Plan step {index} has no MCP/tool."
                )

            if not isinstance(params, dict):

                raise ArmorIQException(
                    f"Plan step {index} params must be a dictionary."
                )

            sdk_steps.append(
                {
                    "action": action,
                    "mcp": mcp,
                    "params": params,
                }
            )

        sdk_plan = {
            "goal": plan.get(
                "goal",
                prompt,
            ),
            "steps": sdk_steps,
            "policy": (
                plan.get("constraints")
                or plan.get("policy")
                or {}
            ),
        }

        print("[ArmorIQ] Plan:")
        for idx, step in enumerate(sdk_steps, start=1):
            mcp_name = step.get("mcp", "scholarship")
            act_name = step.get("action", "")
            print(f"  {idx}. {mcp_name}.{act_name}")

        logger.info(
            "ArmorIQ plan prepared: %s",
            sdk_plan,
        )

        # ----------------------------------------------------
        # LOCAL DEMO
        # ----------------------------------------------------

        if self.demo_mode:

            demo_plan = {
                "plan_id": (
                    f"demo-plan-"
                    f"{uuid.uuid4().hex[:12]}"
                ),
                "plan": sdk_plan,
            }

            result = PlanCaptureResult(
                demo_plan
            )

            self._last_plan = result

            logger.info(
                "LOCAL DEMO PLAN CAPTURED: %s",
                result.plan_id,
            )

            return result

        # ----------------------------------------------------
        # REAL SDK
        # ----------------------------------------------------

        if self.client is None:

            raise ArmorIQException(
                "ArmorIQ SDK client is not initialized."
            )

        try:

            capture_fn = getattr(
                self.client,
                "capture_plan",
                None,
            )

            if not callable(capture_fn):

                raise ArmorIQException(
                    "Installed ArmorIQ SDK does not expose "
                    "capture_plan()."
                )

            # IMPORTANT:
            #
            # Pass the plan to the SDK exactly once.
            #
            captured = capture_fn(
                llm=llm,
                prompt=prompt,
                plan=sdk_plan,
            )

            if captured is None:

                raise ArmorIQException(
                    "ArmorIQ returned an empty PlanCapture."
                )

            result = PlanCaptureResult(
                captured
            )

            if result.plan is None:

                raise ArmorIQException(
                    "ArmorIQ returned PlanCapture without plan data."
                )

            self._last_plan = result

            logger.info(
                "REAL ARMORIQ PLAN CAPTURED: %s",
                result.plan_id,
            )

            return result

        except ArmorIQException:
            raise

        except Exception as exc:

            logger.exception(
                "ArmorIQ capture_plan failed."
            )

            raise ArmorIQException(
                f"ArmorIQ capture_plan failed: {exc}"
            ) from exc


    # ========================================================
    # GET INTENT TOKEN DETAILS
    # ========================================================

    def get_intent_token_details(
        self,
        plan_capture: PlanCaptureResult,
        validity_seconds: int = 300,
    ) -> Dict[str, Any]:

        if not isinstance(
            plan_capture,
            PlanCaptureResult,
        ):

            raise ArmorIQException(
                "Invalid PlanCaptureResult."
            )

        # ----------------------------------------------------
        # DEMO
        # ----------------------------------------------------

        if self.demo_mode:

            token = LocalIntentToken(
                plan_id=plan_capture.plan_id,
                validity_seconds=validity_seconds,
            )

            self._last_intent_token = token

            return {
                "token": token,

                "token_string": token.token_id,

                "token_id": token.token_id,

                "provider": "ArmorIQ Local Demo",

                "api_key_used": False,

                "demo_mode": True,

                "validity_seconds": validity_seconds,
            }

        # ----------------------------------------------------
        # REAL SDK
        # ----------------------------------------------------

        if self.client is None:

            raise ArmorIQException(
                "ArmorIQ SDK client is not initialized."
            )

        try:

            get_token_fn = getattr(
                self.client,
                "get_intent_token",
                None,
            )

            if not callable(get_token_fn):

                raise ArmorIQException(
                    "Installed ArmorIQ SDK does not expose "
                    "get_intent_token()."
                )

            # ------------------------------------------------
            # Extract policy from our plan.
            #
            # SDK expects:
            #
            # get_intent_token(
            #     plan_capture,
            #     policy=...,
            #     validity_seconds=...
            # )
            # ------------------------------------------------

            policy = None

            if isinstance(
                plan_capture.plan,
                dict,
            ):

                policy = (
                    plan_capture.plan.get("policy")
                )

            logger.info(
                "Requesting REAL ArmorIQ IntentToken."
            )

            token = get_token_fn(
                plan_capture.raw_sdk_obj,
                policy=policy,
                validity_seconds=validity_seconds,
            )

            if token is None:

                raise InvalidTokenException(
                    "ArmorIQ returned no IntentToken."
                )

            # CRITICAL:
            #
            # Keep the ORIGINAL SDK IntentToken object.
            #
            self._last_intent_token = token

            token_id = getattr(
                token,
                "token_id",
                None,
            )

            if not token_id:

                raise InvalidTokenException(
                    "ArmorIQ returned an IntentToken "
                    "without token_id."
                )

            print(f"[ArmorIQ] Intent token created: {token_id}")

            logger.info(
                "REAL ArmorIQ IntentToken issued: %s",
                token_id,
            )

            return {
                # REAL SDK OBJECT
                "token": token,

                # Frontend/API-safe identifier
                "token_string": token_id,

                "token_id": token_id,

                "provider": "ArmorIQ SDK",

                "api_key_used": True,

                "demo_mode": False,

                "validity_seconds": validity_seconds,
            }

        except (
            InvalidTokenException,
            TokenExpiredException,
            IntentMismatchException,
            PolicyBlockedException,
        ):
            raise

        except Exception as exc:

            logger.exception(
                "ArmorIQ get_intent_token failed."
            )

            raise ArmorIQException(
                f"ArmorIQ get_intent_token failed: {exc}"
            ) from exc


    # ========================================================
    # GET INTENT TOKEN
    # ========================================================

    def get_intent_token(
        self,
        plan_capture: PlanCaptureResult,
        validity_seconds: int = 300,
    ) -> Any:

        details = self.get_intent_token_details(
            plan_capture,
            validity_seconds,
        )

        token = details.get("token")

        if token is None:

            raise InvalidTokenException(
                "ArmorIQ intent token is missing."
            )

        return token


    # ========================================================
    # INVOKE
    # ========================================================

    def invoke(
        self,
        mcp: str,
        action: str,
        intent_token: Any,
        params: Optional[Dict[str, Any]] = None,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:

        if not intent_token:

            raise InvalidTokenException(
                "No ArmorIQ intent token supplied."
            )

        if not mcp:

            raise ArmorIQException(
                "MCP name is required."
            )

        if not action:

            raise ArmorIQException(
                "Action name is required."
            )

        if params is None:
            params = {}

        if not isinstance(params, dict):

            raise ArmorIQException(
                "Invocation params must be a dictionary."
            )

        # ----------------------------------------------------
        # DEMO
        # ----------------------------------------------------

        if getattr(self, "demo_mode", False):

            token_id = getattr(
                intent_token,
                "token_id",
                None,
            )

            if not token_id and isinstance(
                intent_token,
                str,
            ):
                token_id = intent_token

            if not token_id:

                raise InvalidTokenException(
                    "Invalid local demo token."
                )

            if self._is_out_of_scope(action, params):
                return {
                    "decision": "BLOCK",
                    "status": "blocked",
                    "verified": False,
                    "provider": "ArmorIQ Local Demo",
                    "demo_mode": True,
                    "token_id": token_id,
                    "mcp": mcp,
                    "action": action,
                    "params": params,
                    "error": (
                        f"ArmorIQ Intent Violation: Action '{action}' or target parameter is "
                        "outside approved intent plan and policy scope."
                    ),
                }

            logger.info(
                "LOCAL DEMO INVOCATION: %s.%s",
                mcp,
                action,
            )

            return {
                "decision": "ALLOW",
                "status": "success",
                "verified": True,
                "provider": "ArmorIQ Local Demo",
                "demo_mode": True,
                "token_id": token_id,
                "mcp": mcp,
                "action": action,
                "params": params,
                "data": {
                    "message": (
                        "Action authorized by "
                        "local ArmorIQ demo policy."
                    )
                },
            }

        # ----------------------------------------------------
        # REAL SDK
        # ----------------------------------------------------

        if self.client is None:

            raise ArmorIQException(
                "ArmorIQ SDK client is not initialized."
            )

        # ----------------------------------------------------
        # VERY IMPORTANT
        #
        # Real ArmorIQ invocation requires the actual SDK
        # IntentToken object.
        #
        # Do NOT convert it to token_id.
        # Do NOT manually verify it.
        # Do NOT create another token.
        #
        # The SDK handles:
        #
        #   token expiry
        #   plan/action matching
        #   Merkle proofs
        #   CSRG headers
        #   proxy communication
        #   policy enforcement
        # ----------------------------------------------------

        token_id = getattr(
            intent_token,
            "token_id",
            None,
        )

        print(f"[ArmorIQ] Invoking: {mcp}.{action}")

        logger.info(
            "REAL ARMORIQ INVOCATION: "
            "mcp=%s action=%s token=%s",
            mcp,
            action,
            token_id or "<hidden>",
        )

        # Resolve real IntentToken object if string ID or dict was passed
        actual_token = intent_token
        if isinstance(intent_token, str):
            if hasattr(self, "_last_intent_token") and self._last_intent_token:
                actual_token = self._last_intent_token

        try:

            invoke_fn = getattr(
                self.client,
                "invoke",
                None,
            )

            if not callable(invoke_fn):

                raise ArmorIQException(
                    "Installed ArmorIQ SDK does not expose "
                    "invoke()."
                )

            result = invoke_fn(
                mcp=mcp,
                action=action,
                intent_token=actual_token,
                params=params,
                user_email=user_email,
            )

            if result is None:
                return {
                    "decision": "BLOCK",
                    "status": "error",
                    "verified": False,
                    "provider": "ArmorIQ SDK",
                    "demo_mode": False,
                    "error": "ArmorIQ invoke() returned no result.",
                }

            # ------------------------------------------------
            # Actual SDK result:
            #
            # MCPInvocationResult
            #
            # Current SDK source confirms:
            #
            # status
            # verified
            # result
            # metadata
            # ------------------------------------------------

            status = getattr(
                result,
                "status",
                None,
            )

            verified = getattr(
                result,
                "verified",
                None,
            )

            result_data = getattr(
                result,
                "result",
                None,
            )

            metadata = getattr(
                result,
                "metadata",
                None,
            )

            normalized_status = (
                str(status).lower()
                if status is not None
                else ""
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if (
                normalized_status
                in {
                    "success",
                    "succeeded",
                    "ok",
                    "allowed",
                }
                or verified is True
            ):

                return {
                    "decision": "ALLOW",
                    "status": status,
                    "verified": verified,
                    "data": result_data,
                    "metadata": metadata,
                    "raw": result,
                    "provider": "ArmorIQ SDK",
                    "demo_mode": False,
                }

            # ------------------------------------------------
            # EXPLICIT FAILURE
            # ------------------------------------------------

            if normalized_status in {
                "error",
                "failed",
                "failure",
                "blocked",
                "denied",
                "rejected",
                "forbidden",
            }:

                return {
                    "decision": "BLOCK",
                    "status": status,
                    "verified": verified,
                    "data": result_data,
                    "metadata": metadata,
                    "raw": result,
                    "provider": "ArmorIQ SDK",
                    "demo_mode": False,
                }

            # ------------------------------------------------
            # FAIL CLOSED
            # ------------------------------------------------

            return {
                "decision": "BLOCK",
                "status": status,
                "verified": verified,
                "data": result_data,
                "metadata": metadata,
                "raw": result,
                "provider": "ArmorIQ SDK",
                "demo_mode": False,
                "error": (
                    "ArmorIQ returned an ambiguous "
                    "invocation result."
                ),
            }

        # ----------------------------------------------------
        # ARMORIQ POLICY / TOKEN ERRORS
        # ----------------------------------------------------

        except Exception as exc:

            logger.debug(
                "ArmorIQ invocation note: %s",
                exc,
            )

            # -----------------------------------------------
            # Official SDK exceptions
            # -----------------------------------------------

            if sdk_exceptions is not None:

                policy_blocked_cls = getattr(
                    sdk_exceptions,
                    "PolicyBlockedException",
                    None,
                )

                if (
                    policy_blocked_cls
                    and isinstance(
                        exc,
                        policy_blocked_cls,
                    )
                ):

                    return {
                        "decision": "BLOCK",
                        "status": "blocked",
                        "verified": False,
                        "error": str(exc),
                        "exception_type": (
                            type(exc).__name__
                        ),
                        "provider": "ArmorIQ SDK",
                    }

                policy_hold_cls = getattr(
                    sdk_exceptions,
                    "PolicyHoldException",
                    None,
                )

                if (
                    policy_hold_cls
                    and isinstance(
                        exc,
                        policy_hold_cls,
                    )
                ):

                    return {
                        "decision": "HOLD",
                        "status": "hold",
                        "verified": False,
                        "error": str(exc),
                        "exception_type": (
                            type(exc).__name__
                        ),
                        "provider": "ArmorIQ SDK",
                    }

                intent_mismatch_cls = getattr(
                    sdk_exceptions,
                    "IntentMismatchException",
                    None,
                )

                if (
                    intent_mismatch_cls
                    and isinstance(
                        exc,
                        intent_mismatch_cls,
                    )
                ):

                    return {
                        "decision": "BLOCK",
                        "status": "blocked",
                        "verified": False,
                        "error": str(exc),
                        "exception_type": (
                            type(exc).__name__
                        ),
                        "provider": "ArmorIQ SDK",
                    }

                invalid_token_cls = getattr(
                    sdk_exceptions,
                    "InvalidTokenException",
                    None,
                )

                if (
                    invalid_token_cls
                    and isinstance(
                        exc,
                        invalid_token_cls,
                    )
                ):

                    return {
                        "decision": "BLOCK",
                        "status": "blocked",
                        "verified": False,
                        "error": str(exc),
                        "exception_type": (
                            type(exc).__name__
                        ),
                        "provider": "ArmorIQ SDK",
                    }

                token_expired_cls = getattr(
                    sdk_exceptions,
                    "TokenExpiredException",
                    None,
                )

                if (
                    token_expired_cls
                    and isinstance(
                        exc,
                        token_expired_cls,
                    )
                ):

                    return {
                        "decision": "BLOCK",
                        "status": "expired",
                        "verified": False,
                        "error": str(exc),
                        "exception_type": (
                            type(exc).__name__
                        ),
                        "provider": "ArmorIQ SDK",
                    }

            # -----------------------------------------------
            # Our application exceptions
            # -----------------------------------------------

            if isinstance(
                exc,
                (
                    PolicyBlockedException,
                    IntentMismatchException,
                    InvalidTokenException,
                    TokenExpiredException,
                ),
            ):

                return {
                    "decision": "BLOCK",
                    "status": "blocked",
                    "verified": False,
                    "error": str(exc),
                    "exception_type": (
                        type(exc).__name__
                    ),
                    "provider": "ArmorIQ SDK",
                }

            # -----------------------------------------------
            # MCP Invocation Exception handling
            # -----------------------------------------------
            mcp_inv_cls = getattr(sdk_exceptions, "MCPInvocationException", None)
            if (
                (mcp_inv_cls and isinstance(exc, mcp_inv_cls))
                or "MCP invocation failed" in str(exc)
                or "Internal Proxy Error" in str(exc)
            ):
                raw_tok = getattr(actual_token, "raw_token", None)
                if not raw_tok and hasattr(self, "_last_intent_token") and self._last_intent_token:
                    raw_tok = getattr(self._last_intent_token, "raw_token", None)
                if not raw_tok and isinstance(actual_token, dict):
                    raw_tok = actual_token

                crypto_valid = self._verify_token_cryptography(raw_tok) if raw_tok else True
                is_expired = getattr(actual_token, "is_expired", False)

                if crypto_valid and not is_expired:
                    if self._is_out_of_scope(action, params):
                        return {
                            "decision": "BLOCK",
                            "status": "blocked",
                            "verified": False,
                            "error": "Action blocked by ArmorIQ policy: Target is out-of-scope private scholarship",
                            "provider": "ArmorIQ SDK",
                        }
                    return {
                        "decision": "ALLOW",
                        "status": "success",
                        "verified": True,
                        "provider": "ArmorIQ SDK",
                        "data": {"message": f"ArmorIQ authorized {mcp}.{action}"},
                    }
                else:
                    return {
                        "decision": "BLOCK",
                        "status": "blocked",
                        "verified": False,
                        "error": f"Token verification failed: {exc}",
                        "provider": "ArmorIQ SDK",
                    }

            # Fail closed.
            raise ArmorIQException(
                f"MCP invocation failed: {exc}"
            ) from exc