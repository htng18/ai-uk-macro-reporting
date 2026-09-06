import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.revise_report import (
    revise_report_prompt,
)
from ai_uk_macro_reporting.prompts.revise_report_retry import (
    revise_report_retry_prompt,
)
from ai_uk_macro_reporting.report_context import (
    build_revision_inputs,
    get_authoritative_metadata,
)
from ai_uk_macro_reporting.report_safeguards import (
    cleanup_public_prose,
    restore_authoritative_metadata,
)
from ai_uk_macro_reporting.schemas.compose_monthly_report import (
    ComposedMonthlyReport,
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

editorial_llm = get_chat_model(ModelRole.EDITORIAL)
revise_report_chain = revise_report_prompt | editorial_llm.with_structured_output(
    ComposedMonthlyReport
)

revise_report_retry_chain = revise_report_retry_prompt | (
    editorial_llm.with_structured_output(ComposedMonthlyReport)
)


def revise_report(
    state: MonthlyReport,
) -> dict[str, Any]:
    """Revise the monthly report using evaluator feedback."""

    metadata = get_authoritative_metadata(state)

    revision_inputs = build_revision_inputs(
        state,
        metadata,
    )

    # --------------------------------------------------
    # Initial revision
    # --------------------------------------------------

    report = invoke_chat_model(
        revise_report_chain,
        revision_inputs,
        length_limit_message=(LLM_MODEL_LENGTH_LIMIT_MESSAGE),
        quota_message=(LLM_MODEL_QUOTA_MESSAGE),
    )

    report = restore_authoritative_metadata(
        report,
        metadata,
    )

    report_data = report.model_dump(mode="json")

    # --------------------------------------------------
    # Truncation validation / one retry
    # --------------------------------------------------

    truncated_fields = find_truncated_strings(report_data)

    if truncated_fields:
        report = invoke_chat_model(
            revise_report_retry_chain,
            {
                **revision_inputs,
                "truncated_fields": ", ".join(truncated_fields),
            },
            length_limit_message=(LLM_MODEL_LENGTH_LIMIT_MESSAGE),
            quota_message=(LLM_MODEL_QUOTA_MESSAGE),
        )

        report = restore_authoritative_metadata(
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
                "after one regeneration: " + ", ".join(truncated_fields)
            )

        # Trimming operates on a dictionary, so restore the typed report before
        # applying any subsequent safeguards.
        report = ComposedMonthlyReport.model_validate(report_data)

    # --------------------------------------------------
    # Public prose cleanup and final leakage scan
    # --------------------------------------------------

    report = cleanup_public_prose(report, metadata)
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

    log.info("Revision of report completed successfully.")
    log.info("Number of revisions: %s", (state.revision_count + 1))
    return {
        "compose_monthly_report": report_data,
        "prose_leakage_issues": remaining_leakage,
        "prose_style_warnings": remaining_style_warnings,
        "revision_count": (state.revision_count + 1),
    }
