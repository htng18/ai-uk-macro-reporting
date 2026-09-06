import logging
from typing import Any

from ai_uk_macro_reporting.calculation.compare_metric import compare_metric_snapshots
from ai_uk_macro_reporting.state import MonthlyReport

log = logging.getLogger(__name__)


def compare_monthly_state(
    state: MonthlyReport,
) -> dict[str, Any]:
    """
    Compare the current deterministic metric snapshot against
    the snapshot used for the previous monthly report.
    """

    current_metrics = state.metrics
    previous_metrics = state.previous_metrics

    # ---------------------------------------------
    # First report / no historical snapshot
    # ---------------------------------------------

    if not previous_metrics or not state.previous_reporting_period:
        return {
            "monthly_change_analysis": {
                "previous_reporting_period": None,
                "current_reporting_period": str(state.reporting_period),
                "themes": [],
                "important_changes": [],
                "persistent_features": [],
                "reversals": [],
                "emerging_signals": [],
                "fading_signals": [],
                "new_themes": [],
                "removed_themes": [],
                "comparison_available": False,
            }
        }

    comparison = compare_metric_snapshots(
        previous_metrics=previous_metrics,
        current_metrics=current_metrics,
        previous_reporting_period=(state.previous_reporting_period),
        current_reporting_period=str(state.reporting_period),
    )

    comparison["comparison_available"] = True

    log.info(
        "Comparison of current and previous monthly metrics completed successfully."
    )
    return {"monthly_change_analysis": comparison}
