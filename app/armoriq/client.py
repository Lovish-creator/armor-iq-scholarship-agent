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

except ImportError:

    ArmorIQClient = None
    HAS_OFFICIAL_SDK = False


class PlanCaptureResult:

    def __init__(
        self,
        raw_sdk_obj: Any,
    ):

        self.raw_sdk_obj = raw_sdk_obj

        self.plan_id = getattr(
            raw_sdk_obj,
            "plan_id",
            None,
        )




class ArmorIQWrapperClient:
    """
    Strict ArmorIQ SDK adapter.

    IMPORTANT:

    This class deliberately does NOT implement a local
    replacement for ArmorIQ.

    If the real ArmorIQ SDK is unavailable or fails,
    consequential actions must fail closed.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):

        self.api_key = (
            api_key
            or os.getenv("ARMORIQ_API_KEY")
        )

        self.user_id = (
            user_id
            or os.getenv("ARMORIQ_USER_ID")
        )

        self.agent_id = (
            agent_id
            or os.getenv("ARMORIQ_AGENT_ID")
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

            # Initialize the official SDK client
            self.client = ArmorIQClient(
                api_key=self.api_key,
                user_id=self.user_id,
                agent_id=self.agent_id,
            )

            # Session holder for the most recent plan/session lifecycle.
            self._last_session = None

        except Exception as exc:

            raise ArmorIQException(
                f"Failed to initialize ArmorIQ SDK: {exc}"
            ) from exc

    def capture_plan(
        self,
        llm: str,
        prompt: str,
        plan: Dict[str, Any],
    ) -> PlanCaptureResult:

        try:
            # Use the Python SDK session API to start a session and record the plan.
            SessionOptions = getattr(self.client, "SessionOptions", None)
            if SessionOptions is None:
                # SDK doesn't expose SessionOptions; fail closed.
                raise ArmorIQException("ArmorIQ SDK SessionOptions unavailable")

            options = SessionOptions(
                mode="sdk",
                llm=llm,
            )

            session = self.client.start_session(options)

            # Convert provided plan into the SDK expected tool call shape.
            steps = plan.get("steps") if isinstance(plan, dict) else getattr(plan, "steps", [])
            calls = []
            for s in steps:
                # step may be Pydantic model or dict
                name = None
                args = {}
                if isinstance(s, dict):
                    tool = s.get("tool")
                    action = s.get("action")
                    args = s.get("inputs", {}) or {}
                else:
                    tool = getattr(s, "tool", None)
                    action = getattr(s, "action", None)
                    args = getattr(s, "inputs", {}) or {}

                # Use MCP-style name: <mcp>__<action>
                if tool and action:
                    name = f"{tool}__{action}"
                elif action:
                    name = action

                if name:
                    calls.append({"name": name, "args": args})

            goal = plan.get("goal") if isinstance(plan, dict) else getattr(plan, "goal", prompt)

            # Start the plan trace in the session
            session.start_plan(calls, goal=goal)

            # Store session for later check/verification calls
            self._last_session = session

            return PlanCaptureResult(raw_sdk_obj=session)

        except Exception as exc:

            raise ArmorIQException(
                f"ArmorIQ capture_plan failed: {exc}"
            ) from exc

    def get_intent_token_details(
        self,
        plan_capture: PlanCaptureResult,
        validity_seconds: int = 300,
    ) -> Dict[str, Any]:

        try:

            # Prefer explicit SDK method if available
            get_token_fn = getattr(self.client, "get_intent_token", None)
            if callable(get_token_fn):
                token_obj = get_token_fn(plan_capture.raw_sdk_obj)
                if not token_obj:
                    raise InvalidTokenException("ArmorIQ returned no intent token.")
                token_string = str(token_obj)
                return {
                    "token_string": token_string,
                    "token_id": getattr(token_obj, "token_id", None),
                    "api_key_used": True,
                    "provider": "ArmorIQ SDK",
                }

            # Fallback: return session metadata if a session is available
            session = getattr(plan_capture, "raw_sdk_obj", None) or getattr(self, "_last_session", None)
            session_id = None
            if session is not None:
                session_id = getattr(session, "session_id", None) or getattr(session, "id", None) or str(session)

            return {
                "token_string": session_id,
                "token_id": session_id,
                "api_key_used": True,
                "provider": "ArmorIQ SDK (session)",
            }

        except (
            InvalidTokenException,
            TokenExpiredException,
            IntentMismatchException,
            PolicyBlockedException,
        ):

            raise

        except Exception as exc:

            raise ArmorIQException(
                f"ArmorIQ get_intent_token failed: {exc}"
            ) from exc

    def get_intent_token(
        self,
        plan_capture: PlanCaptureResult,
        validity_seconds: int = 300,
    ) -> str:

        details = self.get_intent_token_details(
            plan_capture,
            validity_seconds,
        )

        return details["token_string"]

    def verify_intent_token(
        self,
        intent_token: str,
        mcp: Optional[str] = None,
        expected_action: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Verify the provided intent token against the ArmorIQ service.

        IMPORTANT: This method intentionally does not implement a local
        replacement for ArmorIQ verification. If the underlying SDK
        exposes a verification API, it will be invoked. If the SDK is
        not available or verification cannot be performed, this method
        MUST raise an exception to enforce fail-closed behavior.
        """

        if not intent_token:
            raise InvalidTokenException("No intent token supplied for verification.")

        # If a session is available, use its check() API
        session = getattr(self, "_last_session", None)

        if session is not None and hasattr(session, "check"):
            # Ensure token matches session if provided
            session_id = getattr(session, "session_id", None) or getattr(session, "id", None)
            if intent_token and session_id and str(intent_token) != str(session_id):
                raise InvalidTokenException("Intent token does not match active ArmorIQ session.")

            # Construct tool name: prefer MCP__action pattern
            tool_name = None
            if mcp and expected_action:
                tool_name = f"{mcp}__{expected_action}"
            elif expected_action:
                tool_name = expected_action

            try:
                decision = session.check(tool_name, params or {})
                # decision is expected to have 'allowed' boolean per SDK
                allowed = getattr(decision, "allowed", None)
                if allowed is None:
                    # Some SDK builds may return a dict-like object
                    allowed = bool(decision.get("allowed")) if isinstance(decision, dict) else False

                return {"decision": "ALLOW" if allowed else "BLOCK", "raw": decision}

            except (
                InvalidTokenException,
                IntentMismatchException,
                TokenExpiredException,
                PolicyBlockedException,
            ):
                raise
            except Exception as exc:
                raise ArmorIQException(f"ArmorIQ token verification failed: {exc}") from exc

        # Otherwise, if the client exposes a verification API, use it
        verify_fn = getattr(self.client, "verify_intent_token", None)
        if callable(verify_fn):
            try:
                res = verify_fn(intent_token=intent_token, expected_action=expected_action, params=params, mcp=mcp)
                if isinstance(res, dict) and res.get("decision"):
                    return res
                raise ArmorIQException("Unexpected verification response from SDK")
            except (
                InvalidTokenException,
                IntentMismatchException,
                TokenExpiredException,
                PolicyBlockedException,
            ):
                raise
            except Exception as exc:
                raise ArmorIQException(f"ArmorIQ token verification failed: {exc}") from exc

        raise ArmorIQException("ArmorIQ SDK verification API not available. Cannot verify intent token.")

    def invoke(
        self,
        mcp: Optional[str] = None,
        mcp_name: Optional[str] = None,
        action: Optional[str] = None,
        intent_token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        inputs: Optional[Dict[str, Any]] = None,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:

        # tolerate both 'mcp' and 'mcp_name', and 'params' or 'inputs'
        mcp_final = mcp or mcp_name
        params_final = params or inputs or {}

        if not intent_token:
            raise InvalidTokenException("No ArmorIQ intent token supplied.")

        # If the SDK provides an invoke API, call it. Otherwise, fail closed.
        invoke_fn = getattr(self.client, "invoke", None)

        if callable(invoke_fn):
            try:
                result = invoke_fn(
                    mcp=mcp_final,
                    action=action,
                    intent_token=intent_token,
                    params=params_final,
                    user_email=user_email,
                )

                return {
                    "decision": "ALLOW",
                    "raw": str(result),
                    "mcp": mcp_final,
                    "action": action,
                }

            except Exception as exc:

                message = str(exc)
                lowered = message.lower()

                if (
                    "intent" in lowered
                    or "scope" in lowered
                    or "mismatch" in lowered
                    or "policy" in lowered
                    or "denied" in lowered
                    or "blocked" in lowered
                ):

                    raise IntentMismatchException(
                        f"ArmorIQ denied the action: {message}"
                    ) from exc

                raise ArmorIQException(
                    f"ArmorIQ invocation failed: {message}"
                ) from exc

        raise ArmorIQException("ArmorIQ SDK invoke API not available. Cannot perform governance invocation.")
