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

            self.client = ArmorIQClient(
                api_key=self.api_key,
                user_id=self.user_id,
                agent_id=self.agent_id,
            )

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

            raw_plan = self.client.capture_plan(
                llm=llm,
                prompt=prompt,
                plan=plan,
            )

            return PlanCaptureResult(
                raw_sdk_obj=raw_plan
            )

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

            token_obj = self.client.get_intent_token(
                plan_capture.raw_sdk_obj
            )

            if not token_obj:

                raise InvalidTokenException(
                    "ArmorIQ returned no intent token."
                )

            token_string = str(token_obj)

            return {
                "token_string": token_string,
                "token_id": getattr(
                    token_obj,
                    "token_id",
                    None,
                ),
                "api_key_used": True,
                "provider": "ArmorIQ SDK",
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

    def invoke(
        self,
        mcp: str,
        action: str,
        intent_token: str,
        params: Dict[str, Any],
        user_email: str,
    ) -> Dict[str, Any]:

        if not intent_token:

            raise InvalidTokenException(
                "No ArmorIQ intent token supplied."
            )

        try:

            result = self.client.invoke(
                mcp=mcp,
                action=action,
                intent_token=intent_token,
                params=params,
                user_email=user_email,
            )

            return {
                "decision": "ALLOW",
                "raw": str(result),
                "mcp": mcp,
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
