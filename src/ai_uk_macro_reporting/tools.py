import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from functools import cache

from dotenv import load_dotenv
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from openai import LengthFinishReasonError, RateLimitError

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)

log = logging.getLogger(__name__)

load_dotenv()


class ReportQuotaError(RuntimeError):
    """Raised when report generation cannot proceed because API quota is exhausted."""


class ReportLengthError(RuntimeError):
    """Raised when the model exhausts its completion budget before valid JSON."""


def _openai_error_code(exc: RateLimitError) -> str | None:
    """Extract an OpenAI error code across supported response shapes."""
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code

    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return None

    error = body.get("error", body)
    if not isinstance(error, dict):
        return None

    code = error.get("code")
    return code if isinstance(code, str) else None


def create_chat_model(
    *,
    model: str,
    reasoning_effort: str,
    max_completion_tokens: int,
) -> ChatOpenAI:
    """Create a chat model configured for structured report generation."""
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        reasoning_effort=reasoning_effort,
        max_completion_tokens=max_completion_tokens,
        timeout=120,
        max_retries=2,
    )


class ModelRole(StrEnum):
    """Workload categories used to select report-generation models."""

    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    EDITORIAL = "editorial"


@dataclass(frozen=True)
class ModelSettings:
    """Configuration for a report-generation model role."""

    model: str
    reasoning_effort: str
    max_completion_tokens: int


MODEL_SETTINGS: dict[ModelRole, ModelSettings] = {
    ModelRole.ANALYSIS: ModelSettings(
        model=os.getenv("MONTHLY_REPORT_ANALYSIS_MODEL", "gpt-5.6-luna"),
        reasoning_effort=os.getenv(
            "MONTHLY_REPORT_ANALYSIS_REASONING_EFFORT",
            "medium",
        ),
        max_completion_tokens=int(
            os.getenv(
                "MONTHLY_REPORT_ANALYSIS_MAX_COMPLETION_TOKENS",
                "16000",
            )
        ),
    ),
    ModelRole.SYNTHESIS: ModelSettings(
        model=os.getenv("MONTHLY_REPORT_SYNTHESIS_MODEL", "gpt-5.6-terra"),
        reasoning_effort=os.getenv(
            "MONTHLY_REPORT_SYNTHESIS_REASONING_EFFORT",
            "medium",
        ),
        max_completion_tokens=int(
            os.getenv("MONTHLY_REPORT_SYNTHESIS_MAX_COMPLETION_TOKENS", "16000")
        ),
    ),
    ModelRole.EDITORIAL: ModelSettings(
        model=os.getenv("MONTHLY_REPORT_EDITORIAL_MODEL", "gpt-5.6-terra"),
        reasoning_effort=os.getenv(
            "MONTHLY_REPORT_EDITORIAL_REASONING_EFFORT",
            "high",
        ),
        max_completion_tokens=int(
            os.getenv("MONTHLY_REPORT_EDITORIAL_MAX_COMPLETION_TOKENS", "16000")
        ),
    ),
}


@cache
def get_chat_model(role: ModelRole) -> ChatOpenAI:
    """Return the shared chat model configured for a workload role."""
    settings = MODEL_SETTINGS[role]
    return create_chat_model(
        model=settings.model,
        reasoning_effort=settings.reasoning_effort,
        max_completion_tokens=settings.max_completion_tokens,
    )


def invoke_chat_model[InputT, OutputT](
    runnable: Runnable[InputT, OutputT],
    input_: InputT,
    *,
    length_limit_message: str = LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    quota_message: str = LLM_MODEL_QUOTA_MESSAGE,
) -> OutputT:
    """Invoke a chat-model runnable and translate known terminal failures."""
    try:
        return runnable.invoke(input_)
    except LengthFinishReasonError as exc:
        log.error("Report generation failed due to length limit: %s", exc)
        raise ReportLengthError(length_limit_message) from exc
    except RateLimitError as exc:
        if _openai_error_code(exc) == "insufficient_quota":
            log.error("Report generation failed due to insufficient quota: %s", exc)
            raise ReportQuotaError(quota_message) from exc
        raise
