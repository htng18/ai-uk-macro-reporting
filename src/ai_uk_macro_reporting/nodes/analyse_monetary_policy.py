import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.monetary_policy import monetary_policy_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.monetary_policy import MonetaryPolicyReportResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

analysis_llm = get_chat_model(ModelRole.ANALYSIS)
monetary_policy_chain = monetary_policy_prompt | (
    analysis_llm.with_structured_output(MonetaryPolicyReportResponse)
)


def analyse_monetary_policy(state: MonthlyReport) -> dict[str, Any]:
    """Generate and validate the monetary policy report section."""
    result = invoke_chat_model(
        monetary_policy_chain,
        {
            "reporting_period": state.reporting_period,
            "monetary_policy_metrics": serialize_prompt_data(
                state.metrics.get("monetary_policy", {})
            ),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )
    log.info("Analysis of monetary policy completed successfully.")
    return {
        "monetary_policy_report": (
            result.monetary_policy_report.model_dump(mode="json")
        )
    }
