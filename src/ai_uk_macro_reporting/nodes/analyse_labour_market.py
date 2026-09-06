import logging
from typing import Any

from ai_uk_macro_reporting.common import (
    LLM_MODEL_LENGTH_LIMIT_MESSAGE,
    LLM_MODEL_QUOTA_MESSAGE,
)
from ai_uk_macro_reporting.prompts.labour_market import labour_market_prompt
from ai_uk_macro_reporting.report_context import serialize_prompt_data
from ai_uk_macro_reporting.schemas.labour_market import LabourMarketReportResponse
from ai_uk_macro_reporting.state import MonthlyReport
from ai_uk_macro_reporting.tools import (
    ModelRole,
    get_chat_model,
    invoke_chat_model,
)

log = logging.getLogger(__name__)

analysis_llm = get_chat_model(ModelRole.ANALYSIS)
labour_market_chain = labour_market_prompt | (
    analysis_llm.with_structured_output(LabourMarketReportResponse)
)


def analyse_labour_market(state: MonthlyReport) -> dict[str, Any]:
    """Generate and validate the labour market report section."""
    result = invoke_chat_model(
        labour_market_chain,
        {
            "reporting_period": state.reporting_period,
            "labour_market_metrics": serialize_prompt_data(
                state.metrics.get("labour_market", {})
            ),
        },
        length_limit_message=LLM_MODEL_LENGTH_LIMIT_MESSAGE,
        quota_message=LLM_MODEL_QUOTA_MESSAGE,
    )

    log.info("Analysis of labour market metrics completed successfully.")
    return {"labour_market_report": result.labour_market_report.model_dump(mode="json")}
