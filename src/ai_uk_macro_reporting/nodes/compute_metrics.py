import logging
from typing import Any

import pandas as pd

from ai_uk_macro_reporting.calculation.calculate_metrics import (
    calculate_metrics_snapshot,
)
from ai_uk_macro_reporting.state import MonthlyReport

log = logging.getLogger(__name__)


def compute_metrics(state: MonthlyReport) -> dict[str, Any]:
    """Calculate current and previous metric snapshots from supplied rows."""
    observations = pd.DataFrame.from_dict(state.rows)
    log.info("Number of observations in metrics: %s", len(observations))

    current_metrics = calculate_metrics_snapshot(
        observations=observations,
        observation_offset=0,
    )

    previous_metrics = calculate_metrics_snapshot(
        observations=observations,
        observation_offset=1,
    )
    log.info("Computed current and previous metrics successfully.")
    return {
        "metrics": current_metrics,
        "previous_metrics": previous_metrics,
    }
