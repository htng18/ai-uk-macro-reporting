import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.compose_monthly_report import (
    compose_monthly_report_prompt,
)
from ai_uk_macro_reporting.prompts.compose_monthly_report_retry import (
    compose_monthly_report_retry_prompt,
)
from ai_uk_macro_reporting.report_context import (
    build_compose_inputs,
    get_authoritative_metadata,
)
from ai_uk_macro_reporting.report_safeguards import (
    cleanup_public_prose,
    restore_authoritative_metadata,
)
from ai_uk_macro_reporting.schemas.compose_monthly_report import (
    ComposedMonthlyReport,
    ComposedMonthlyReportResponse,
)
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)
from ai_uk_macro_reporting.validation.prose_leakage import (
    find_public_prose_leakage,
    find_public_prose_style_warnings,
)
from ai_uk_macro_reporting.validation.truncation import (
    find_truncated_strings,
    trim_incomplete_trailing_prose,
)

log = logging.getLogger(__name__)

synthesis_llm = get_chat_model(ModelRole.SYNTHESIS)
compose_monthly_report_chain = compose_monthly_report_prompt | (
    synthesis_llm.with_structured_output(ComposedMonthlyReportResponse)
)

compose_monthly_report_retry_chain = compose_monthly_report_retry_prompt | (
    synthesis_llm.with_structured_output(ComposedMonthlyReportResponse)
)


def compose_monthly_report(
    state: MonthlyReport,
) -> dict[str, Any]:
    """Compose and validate the final monthly report."""

    metadata = get_authoritative_metadata(state)

    compose_inputs = build_compose_inputs(
        state,
        metadata,
    )

    # --------------------------------------------------
    # Initial generation
    # --------------------------------------------------

    result = invoke_chat_model(
        compose_monthly_report_chain,
        compose_inputs,
        length_limit_message=(LLM_MODEL_LENGTH_LIMIT_MESSAGE),
        quota_message=(LLM_MODEL_QUOTA_MESSAGE),
    )

    report = restore_authoritative_metadata(
        result.compose_monthly_report,
        metadata,
    )

    report_data = report.model_dump(mode="json")

    # --------------------------------------------------
    # Truncation retry
    # --------------------------------------------------

    truncated_fields = find_truncated_strings(report_data)

    if truncated_fields:
        retry_result = invoke_chat_model(
            compose_monthly_report_retry_chain,
            {
                **compose_inputs,
                "truncated_fields": ", ".join(truncated_fields),
            },
            length_limit_message=(LLM_MODEL_LENGTH_LIMIT_MESSAGE),
            quota_message=(LLM_MODEL_QUOTA_MESSAGE),
        )

        report = restore_authoritative_metadata(
            retry_result.compose_monthly_report,
            metadata,
        )

        report_data = report.model_dump(mode="json")

        truncated_fields = find_truncated_strings(report_data)

        if truncated_fields:
            report_data = trim_incomplete_trailing_prose(report_data)

            truncated_fields = find_truncated_strings(report_data)

        if truncated_fields:
            raise ValueError(
                "Possible truncated report fields "
                "after one regeneration: " + ", ".join(truncated_fields)
            )

        # Important: keep report in sync
        report = ComposedMonthlyReport.model_validate(report_data)

    # --------------------------------------------------
    # Public prose cleanup
    # --------------------------------------------------

    report = cleanup_public_prose(
        report,
        metadata,
    )

    report_data = report.model_dump(mode="json")

    truncated_fields = find_truncated_strings(report_data)

    if truncated_fields:
        report_data = trim_incomplete_trailing_prose(report_data)
        truncated_fields = find_truncated_strings(report_data)

        if truncated_fields:
            raise ValueError(
                "Possible truncated report fields "
                "after public prose cleanup: " + ", ".join(truncated_fields)
            )

        report = ComposedMonthlyReport.model_validate(report_data)
        report_data = report.model_dump(mode="json")

    remaining_leakage = find_public_prose_leakage(report_data)
    remaining_style_warnings = find_public_prose_style_warnings(report_data)

    log.info("Composition of monthly report completed successfully.")
    return {
        "compose_monthly_report": report_data,
        "prose_leakage_issues": (remaining_leakage),
        "prose_style_warnings": remaining_style_warnings,
    }
