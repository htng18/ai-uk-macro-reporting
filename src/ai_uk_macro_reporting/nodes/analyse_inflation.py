import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.inflation import inflation_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.inflation import InflationResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

analysis_llm = get_chat_model(ModelRole.ANALYSIS)
inflation_chain = inflation_prompt | (
    analysis_llm.with_structured_output(InflationResponse)
)


def analyse_inflation(state: MonthlyReport) -> dict[str, Any]:
    """Generate and validate the inflation report section."""
    result = invoke_chat_model(
        inflation_chain,
        {
            "reporting_period": state.reporting_period,
            "inflation_metrics": serialize_prompt_data(
                state.metrics.get("inflation", {})
            ),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )

    log.info("Analysis of inflation completed successfully.")
    return {"inflation_report": result.inflation_report.model_dump(mode="json")}
