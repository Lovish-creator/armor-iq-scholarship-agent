import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

from app.armoriq.errors import (
    ArmorIQException,
    InvalidTokenException,
    IntentMismatchException,
    PolicyBlockedException,
    TokenExpiredException,
)


logger = logging.getLogger("armoriq_client")


# ============================================================
# OFFICIAL ARMORIQ SDK
# ============================================================

try:
    from armoriq_sdk import ArmorIQClient

    HAS_OFFICIAL_SDK = True

except Exception:
    ArmorIQClient = None
    HAS_OFFICIAL_SDK = False


if HAS_OFFICIAL_SDK:
    try:
        from armoriq_sdk import exceptions as sdk_exceptions
    except Exception:
        sdk_exceptions = None
else:
    sdk_exceptions = None


# ============================================================
# PLAN CAPTURE RESULT
# ============================================================

class PlanCaptureResult:
    """
    Small wrapper around the SDK's captured-plan object.

    IMPORTANT:
    We keep the original SDK object intact because the signed
    IntentToken is cryptographically associated with this plan.
    """

    def __init__(self, raw_sdk_obj: Any):
        self.raw_sdk_obj = raw_sdk_obj

        self.plan = getattr(
            raw_sdk_obj,
            "plan",
            None,
        )

        self.plan_id = (
            getattr(raw_sdk_obj, "plan_id", None)
            or getattr(raw_sdk_obj, "id", None)
        )


# ============================================================
# ARMORIQ CLIENT WRAPPER
# ============================================================

class ArmorIQWrapperClient:
    """
    Strict wrapper around the official ArmorIQ Python SDK.

    Security principles:

    1. Never replace an IntentToken object with only its token_id.
    2. Never invent a token.
    3. Never silently allow an ambiguous invocation result.
    4. Preserve the real ArmorIQ error for debugging.
    5. Fail closed when authorization cannot be verified.
    """

    def __init__(self, api_key: Optional[str] = None):

        self.api_key = (
            api_key
            or os.getenv("ARMORIQ_API_KEY")
        )

        if not self.api_key:
            raise ArmorIQException(
                "ARMORIQ_API_KEY is required. "
                "Live ArmorIQ mode cannot run without credentials."
            )

        if not HAS_OFFICIAL_SDK:
            raise ArmorIQException(
                "armoriq-sdk is not installed. "
                "Install the official ArmorIQ SDK."
            )

        try:
            config_path = ROOT_DIR / "policies" / "armoriq.yaml"

            if not config_path.exists():
                raise ArmorIQException(
                    f"ArmorIQ config not found: {config_path}"
                )

            self.client = ArmorIQClient.from_config(
                str(config_path)
            )

        except Exception as exc:
            logger.exception(
                "Failed to initialize ArmorIQ SDK"
            )

            raise ArmorIQException(
                f"Failed to initialize ArmorIQ SDK: {exc}"
            ) from exc

        self._last_plan = None
        self._last_intent_token = None


    def capture_plan(
        self,
        llm: str,
        prompt: str,
        plan: Dict[str, Any],
    ) -> PlanCaptureResult:

        """
        Capture and validate an explicit execution plan.

        The resulting captured-plan object is retained because
        the IntentToken generated from it must correspond to
        the exact signed plan.
        """

        try:

            if not isinstance(plan, dict):
                raise ArmorIQException(
                    "ArmorIQ plan must be a dictionary."
                )

            sdk_plan = {
                "goal": plan.get(
                    "goal",
                    prompt,
                ),
                "steps": [],
            }

            # Preserve constraints as policy information.
            sdk_plan["policy"] = (
                plan.get("constraints")
                or {}
            )

            steps = (
                plan.get("steps")
                or []
            )

            if not isinstance(steps, list):
                raise ArmorIQException(
                    "ArmorIQ plan 'steps' must be a list."
                )

            for index, step in enumerate(steps):

                if not isinstance(step, dict):
                    raise ArmorIQException(
                        f"Invalid plan step at index {index}."
                    )

                action = (
                    step.get("action")
                )

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

                sdk_plan["steps"].append(
                    {
                        "action": action,
                        "mcp": mcp,
                        "params": params,
                    }
                )

            logger.info(
                "================================================"
            )
            logger.info(
                "ARMORIQ CAPTURE PLAN"
            )
            logger.info(
                "LLM: %s",
                llm,
            )
            logger.info(
                "PROMPT: %s",
                prompt,
            )
            logger.info(
                "PLAN: %s",
                sdk_plan,
            )
            logger.info(
                "================================================"
            )

            captured = self.client.capture_plan(
                llm=llm,
                prompt=prompt,
                plan=sdk_plan,
            )

            if not captured:
                raise ArmorIQException(
                    "ArmorIQ returned an empty captured plan."
                )

            self._last_plan = captured

            result = PlanCaptureResult(
                raw_sdk_obj=captured
            )

            logger.info(
                "ArmorIQ plan captured successfully. "
                "plan_id=%s",
                result.plan_id,
            )

            return result

        except ArmorIQException:
            raise

        except Exception as exc:

            logger.exception(
                "ArmorIQ capture_plan failed"
            )

            raise ArmorIQException(
                f"ArmorIQ capture_plan failed: {exc}"
            ) from exc


    # ========================================================
    # GET INTENT TOKEN
    # ========================================================

    def get_intent_token_details(
        self,
        plan_capture: PlanCaptureResult,
        validity_seconds: int = 300,
    ) -> Dict[str, Any]:

        """
        Request a signed IntentToken.

        CRITICAL FIX:

        The actual SDK IntentToken object is preserved.

        Previously the code did:

            token_id = token_resp.token_id

        and then returned that ID as the token.

        That is wrong because invoke() needs the actual signed
        IntentToken object, not merely its identifier.
        """

        try:

            if not isinstance(
                plan_capture,
                PlanCaptureResult,
            ):
                raise ArmorIQException(
                    "Invalid PlanCaptureResult supplied."
                )

            get_token = getattr(
                self.client,
                "get_intent_token",
                None,
            )

            if not callable(get_token):
                raise ArmorIQException(
                    "ArmorIQ SDK get_intent_token API "
                    "not available."
                )

            raw_plan = (
                plan_capture.raw_sdk_obj
            )

            if raw_plan is None:
                raise ArmorIQException(
                    "Captured plan contains no SDK object."
                )

            # ------------------------------------------------
            # Extract policy if available.
            # ------------------------------------------------

            captured_policy = None

            try:

                captured_plan = getattr(
                    raw_plan,
                    "plan",
                    None,
                )

                if isinstance(
                    captured_plan,
                    dict,
                ):
                    captured_policy = (
                        captured_plan.get(
                            "policy"
                        )
                    )

            except Exception:
                captured_policy = None


            logger.info(
                "Requesting ArmorIQ IntentToken..."
            )

            logger.debug(
                "Captured policy: %s",
                captured_policy,
            )


            # ------------------------------------------------
            # Request actual signed token.
            # ------------------------------------------------

            token_resp = self.client.get_intent_token(
                raw_plan,
                policy=captured_policy,
                validity_seconds=validity_seconds,
            )


            if token_resp is None:
                raise InvalidTokenException(
                    "ArmorIQ issued no intent token."
                )


            # ------------------------------------------------
            # CRITICAL:
            #
            # Preserve the COMPLETE SDK token object.
            # ------------------------------------------------

            self._last_intent_token = token_resp


            token_id = getattr(
                token_resp,
                "token_id",
                None,
            )


            logger.info(
                "ArmorIQ IntentToken issued successfully."
            )

            logger.info(
                "IntentToken ID: %s",
                token_id or "<SDK did not expose token_id>",
            )

            logger.debug(
                "IntentToken SDK type: %s",
                type(token_resp).__name__,
            )


            return {
                # IMPORTANT:
                # This is the ACTUAL SDK token object.
                "token": token_resp,

                # Metadata only.
                "token_id": token_id,

                "api_key_used": True,

                "provider": "ArmorIQ SDK",

                "validity_seconds": validity_seconds,

                # Keep raw object for diagnostics.
                "raw": token_resp,
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
                "ArmorIQ get_intent_token failed"
            )

            raise ArmorIQException(
                f"ArmorIQ get_intent_token failed: {exc}"
            ) from exc


    # ========================================================
    # GET TOKEN
    # ========================================================

    def get_intent_token(
        self,
        plan_capture: PlanCaptureResult,
        validity_seconds: int = 300,
    ) -> Any:

        """
        Return the actual SDK IntentToken object.

        IMPORTANT:
        Do NOT return token_id here.
        """

        details = self.get_intent_token_details(
            plan_capture,
            validity_seconds,
        )

        token = details.get("token")

        if token is None:
            raise InvalidTokenException(
                "ArmorIQ IntentToken object is missing."
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

        """
        Invoke a protected MCP action.

        IMPORTANT:
        intent_token must be the actual SDK IntentToken object.

        The function deliberately does NOT convert it into
        token_id.
        """

        if intent_token is None:
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


        invoke_fn = getattr(
            self.client,
            "invoke",
            None,
        )


        if not callable(invoke_fn):
            raise ArmorIQException(
                "ArmorIQ SDK invoke API not available."
            )


        # ----------------------------------------------------
        # Diagnostics
        # ----------------------------------------------------

        token_id = getattr(
            intent_token,
            "token_id",
            None,
        )

        logger.info(
            "================================================"
        )

        logger.info(
            "ARMORIQ INVOCATION"
        )

        logger.info(
            "MCP: %s",
            mcp,
        )

        logger.info(
            "ACTION: %s",
            action,
        )

        logger.info(
            "PARAMS: %s",
            params,
        )

        logger.info(
            "TOKEN TYPE: %s",
            type(intent_token).__name__,
        )

        logger.info(
            "TOKEN ID: %s",
            token_id or "<not exposed>",
        )

        logger.info(
            "================================================"
        )


        try:

            # ------------------------------------------------
            # IMPORTANT:
            #
            # Pass the actual IntentToken object.
            # ------------------------------------------------

            result = invoke_fn(
                mcp=mcp,
                action=action,
                intent_token=intent_token,
                params=params,
                user_email=user_email,
            )


            logger.info(
                "ArmorIQ SDK invoke returned."
            )

            logger.debug(
                "Raw invoke result type: %s",
                type(result).__name__,
            )

            logger.debug(
                "Raw invoke result: %r",
                result,
            )


            # ------------------------------------------------
            # Extract useful result metadata.
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

            data = getattr(
                result,
                "data",
                None,
            )

            error = getattr(
                result,
                "error",
                None,
            )


            logger.info(
                "ArmorIQ result status=%r verified=%r",
                status,
                verified,
            )


            # ------------------------------------------------
            # Explicit success
            # ------------------------------------------------

            if (
                status is not None
                and str(status).lower()
                in {
                    "success",
                    "succeeded",
                    "ok",
                    "allowed",
                }
            ):

                return {
                    "decision": "ALLOW",
                    "raw": result,
                    "status": status,
                    "verified": verified,
                    "data": data,
                }


            # ------------------------------------------------
            # Explicit verified result
            # ------------------------------------------------

            if verified is True:

                return {
                    "decision": "ALLOW",
                    "raw": result,
                    "status": status,
                    "verified": verified,
                    "data": data,
                }


            # ------------------------------------------------
            # Explicit blocked result
            # ------------------------------------------------

            if (
                status is not None
                and str(status).lower()
                in {
                    "blocked",
                    "denied",
                    "rejected",
                    "forbidden",
                    "failure",
                    "failed",
                }
            ):

                logger.warning(
                    "ArmorIQ explicitly blocked invocation: %s",
                    error or result,
                )

                return {
                    "decision": "BLOCK",
                    "raw": result,
                    "status": status,
                    "verified": verified,
                    "error": error or str(result),
                    "data": data,
                }


            # ------------------------------------------------
            # UNKNOWN RESULT
            #
            # Fail closed, but preserve diagnostics.
            # ------------------------------------------------

            logger.error(
                "ArmorIQ returned an ambiguous invocation result. "
                "Failing closed."
            )

            return {
                "decision": "BLOCK",
                "raw": result,
                "status": status,
                "verified": verified,
                "error": error or (
                    "ArmorIQ returned an ambiguous result; "
                    "authorization could not be verified."
                ),
                "data": data,
            }


        # ====================================================
        # SDK EXCEPTIONS
        # ====================================================

        except Exception as exc:

            logger.exception(
                "ArmorIQ invocation exception: %s",
                exc,
            )


            # ------------------------------------------------
            # Official SDK PolicyBlockedException
            # ------------------------------------------------

            if (
                HAS_OFFICIAL_SDK
                and sdk_exceptions is not None
            ):

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
                        "error": str(exc),
                        "exception_type": type(exc).__name__,
                    }


                # ------------------------------------------------
                # Policy hold
                # ------------------------------------------------

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
                        "error": str(exc),
                        "exception_type": type(exc).__name__,
                    }


                # ------------------------------------------------
                # Intent mismatch
                # ------------------------------------------------

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
                        "error": str(exc),
                        "exception_type": type(exc).__name__,
                    }


                # ------------------------------------------------
                # Invalid token
                # ------------------------------------------------

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
                        "error": str(exc),
                        "exception_type": type(exc).__name__,
                    }


                # ------------------------------------------------
                # Token expired
                # ------------------------------------------------

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
                        "error": str(exc),
                        "exception_type": type(exc).__name__,
                    }


            # =================================================
            # LOCAL APPLICATION EXCEPTIONS
            # =================================================

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
                    "error": str(exc),
                    "exception_type": type(exc).__name__,
                }


            # =================================================
            # UNKNOWN ERROR
            # =================================================

            raise ArmorIQException(
                f"MCP invocation failed: {exc}"
            ) from exc