"""Restore authoritative report fields and enforce publication safeguards."""

from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.public_prose_cleanup import (
    public_prose_cleanup_prompt,
)
from ai_uk_macro_reporting.report_context import (
    AuthoritativeMetadata,
    serialize_prompt_data,
)
from ai_uk_macro_reporting.schemas.compose_monthly_report import ComposedMonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)
from ai_uk_macro_reporting.validation.prose_leakage import (
    find_public_prose_leakage,
    find_public_prose_style_warnings,
)

analysis_llm = get_chat_model(ModelRole.ANALYSIS)
public_prose_cleanup_chain = (
    public_prose_cleanup_prompt
    | analysis_llm.with_structured_output(ComposedMonthlyReport)
)


def restore_authoritative_metadata(
    report: ComposedMonthlyReport,
    metadata: AuthoritativeMetadata,
) -> ComposedMonthlyReport:
    """Restore metadata that downstream models may not change."""
    report.reporting_period = metadata["reporting_period"]
    report.executive_summary.macro_regime = metadata["regime"]
    report.executive_summary.confidence = metadata["confidence"]
    report.overall_assessment.confidence = metadata["confidence"]
    report.risks_to_central_interpretation.counter_analysis_verdict = metadata[
        "verdict"
    ]
    report.current_conditions.output_and_demand.direction = metadata["output_direction"]
    report.current_conditions.inflation.direction = metadata["inflation_direction"]
    report.current_conditions.labour_market.classification = metadata[
        "labour_classification"
    ]
    report.current_conditions.monetary_and_financial_conditions.classification = (
        metadata["monetary_classification"]
    )
    return report


def cleanup_public_prose(
    report: ComposedMonthlyReport,
    metadata: AuthoritativeMetadata,
) -> ComposedMonthlyReport:
    """Review public-prose findings and restore protected report fields."""
    report_data = report.model_dump(mode="json")
    leakage_findings = find_public_prose_leakage(report_data)
    style_warnings = find_public_prose_style_warnings(report_data)

    if not leakage_findings and not style_warnings:
        return report

    cleaned_report = invoke_chat_model(
        public_prose_cleanup_chain,
        {
            "current_report": serialize_prompt_data(report_data),
            "leakage_findings": serialize_prompt_data(leakage_findings),
            "style_warnings": serialize_prompt_data(style_warnings),
            "authoritative_metadata": serialize_prompt_data(metadata),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )
    return restore_authoritative_metadata(cleaned_report, metadata)


def validate_evaluation_consistency(evaluation_data: dict[str, Any]) -> None:
    """Raise an error when issue severities conflict with verdict or score."""
    issues = evaluation_data["issues"]
    critical_count = sum(issue["severity"] == "critical" for issue in issues)
    major_count = sum(issue["severity"] == "major" for issue in issues)
    overall = evaluation_data["overall_evaluation"]
    verdict = overall["publication_verdict"]
    score = overall["score"]
    passing_verdicts = {"pass", "pass_with_minor_edits"}

    if critical_count > 0 and verdict in passing_verdicts:
        raise ValueError(
            "Evaluation inconsistency: "
            "critical issues cannot receive "
            f"publication verdict {verdict!r}"
        )

    if critical_count > 0 and score > 7.9:
        raise ValueError(
            "Evaluation inconsistency: critical issues cannot receive a score above 7.9"
        )

    if major_count > 0 and verdict in passing_verdicts:
        raise ValueError("Evaluation inconsistency: major issues require revision")
