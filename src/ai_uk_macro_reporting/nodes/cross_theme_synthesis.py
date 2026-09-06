import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
    Confidence,
)
from ai_uk_macro_reporting.prompts.cross_theme import cross_theme_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.cross_theme import CrossThemeReportResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

synthesis_llm = get_chat_model(ModelRole.SYNTHESIS)
cross_theme_chain = cross_theme_prompt | (
    synthesis_llm.with_structured_output(CrossThemeReportResponse)
)


def cross_theme_synthesis(state: MonthlyReport) -> dict[str, Any]:
    """Generate and validate the cross-theme synthesis report."""
    authoritative_confidence = Confidence(
        state.confidence_profile["metrics"]["overall_confidence"]
    )

    result = invoke_chat_model(
        cross_theme_chain,
        {
            "reporting_period": state.reporting_period,
            "output_demand_report": serialize_prompt_data(
                state.output_and_demand_report
            ),
            "inflation_report": serialize_prompt_data(state.inflation_report),
            "labour_market_report": serialize_prompt_data(state.labour_market_report),
            "monetary_policy_report": serialize_prompt_data(
                state.monetary_policy_report
            ),
            "monthly_change_analysis": serialize_prompt_data(
                state.monthly_change_analysis
            ),
            "confidence_profile": serialize_prompt_data(state.confidence_profile),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )

    report = result.cross_theme_report
    report.headline_assessment.confidence = authoritative_confidence
    report.overall_confidence.level = authoritative_confidence
    report.confidence_assessment.classification = authoritative_confidence

    log.info(
        "Cross-theme synthesis report generated with overall confidence: %s",
        report.overall_confidence.level,
    )
    return {"cross_theme_report": report.model_dump(mode="json")}
