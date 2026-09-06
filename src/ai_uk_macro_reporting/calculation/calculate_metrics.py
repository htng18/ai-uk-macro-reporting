from typing import Any, Literal, NotRequired, TypedDict

import numpy as np
import pandas as pd

from ai_uk_macro_reporting.common import (
    BroadClassification,
    Direction,
    SignalTransform,
    SignalUnit,
    Strength,
)

from .metric_definitions import (
    BREADTH_COMPONENTS,
    SIGNAL_CONFIG,
    THEME_INDICATORS_MAP,
)

type NumericValue = int | float | np.integer | np.floating
type BreadthClassification = BroadClassification | Literal["insufficient_data"]
type MetricsSnapshot = dict[str, dict[str, Any]]


class SignalDatum(TypedDict):
    """Represent one indicator's contribution to an aggregate signal."""

    indicator: str
    direction: Direction
    score: int


class InsufficientOverallSignal(TypedDict):
    """Represent an aggregate signal with insufficient underlying data."""

    status: Literal["insufficient_data"]


class AvailableOverallSignal(TypedDict):
    """Represent an available aggregate signal and its scored direction."""

    status: Literal["available"]
    direction: Direction
    direction_score: float
    strength_score: float
    strength: Strength


type OverallSignal = AvailableOverallSignal | InsufficientOverallSignal


class IndicatorMetric(TypedDict):
    """Represent calculated metrics and classifications for one indicator."""

    latest_observation_date: str
    latest_value: object | None
    signal_transform: SignalTransform
    signal_unit: SignalUnit
    latest_signal_change: float
    three_month_momentum: float
    six_month_trend: float
    twelve_month_volatility: float | None
    direction: NotRequired[Direction]
    signal_strength: NotRequired[Strength]
    signal_score: NotRequired[int]


SIGNAL_TRANSFORMS: dict[str, SignalTransform] = {
    indicator: config["transform"] for indicator, config in SIGNAL_CONFIG.items()
}

DIRECTION_VALUES: dict[Direction, int] = {
    Direction.POSITIVE: 1,
    Direction.NEUTRAL: 0,
    Direction.NEGATIVE: -1,
}

BREADTH_RATIO: float = 2 / 3


def to_python_number(value: object) -> object | None:
    """Convert pandas/NumPy scalar values into serializable Python values.

    Missing values become ``None``, NumPy integers and floats become their
    built-in Python equivalents, and all other values are returned unchanged.
    """
    if pd.isna(value):
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    return value


def signal_transform(
    indicator: str,
    series: pd.Series,
) -> pd.Series:
    """Transform an indicator series into configured directional changes.

    The configured as-reported, percentage-change, or first-difference
    transform is applied, followed by the indicator's direction multiplier so
    positive values always represent movement in the configured positive
    economic direction.

    Args:
        indicator: Indicator name used to look up its signal configuration.
        series: Chronologically ordered observation values.

    Returns:
        The transformed series with missing change values removed.

    Raises:
        ValueError: If the indicator has no configuration or its configured
            transform is unsupported.
    """
    try:
        config = SIGNAL_CONFIG[indicator]
    except KeyError as exc:
        raise ValueError(f"No signal configuration for {indicator!r}") from exc

    transform = config["transform"]

    if transform == SignalTransform.AS_REPORTED:
        transformed = series.copy()
    elif transform == SignalTransform.PCT_CHANGE:
        transformed = series.pct_change(fill_method=None) * 100
    elif transform == SignalTransform.DIFFERENCE:
        transformed = series.diff()
    else:
        raise ValueError(
            f"Unknown signal transformation {transform!r} for {indicator!r}"
        )

    transformed *= config.get("direction_multiplier", 1)
    return transformed.dropna()


class IndicatorSignalStrength:
    """
    Calculate the strength and direction of one economic indicator.

    score:
        0-1 -> weak
        2-4 -> moderate
        5-6 -> strong
    """

    def __init__(
        self,
        monthly_changes: pd.Series,
        latest_monthly_change: NumericValue | None,
        three_month_momentum: NumericValue | None,
        six_month_trend: NumericValue | None,
        twelve_month_volatility: NumericValue | None,
        direction_threshold: float = 0.5,
    ) -> None:
        """Calculate and retain an indicator's direction and strength signal.

        Args:
            monthly_changes: Chronologically ordered transformed monthly changes.
            latest_monthly_change: Most recent transformed monthly change.
            three_month_momentum: Mean transformed change over the latest three
                observations.
            six_month_trend: Mean transformed change over the latest six
                observations.
            twelve_month_volatility: Standard deviation of transformed changes
                over the latest twelve observations.
            direction_threshold: Absolute standardized value above which a signal
                is classified as positive or negative rather than neutral.
        """
        self.monthly_changes = monthly_changes
        self.latest_monthly_change = latest_monthly_change
        self.three_month_momentum = three_month_momentum
        self.six_month_trend = six_month_trend
        self.twelve_month_volatility = twelve_month_volatility
        self.direction_threshold = direction_threshold

        # -------------------------------------------
        # Direction
        # -------------------------------------------

        self.latest_direction = self.classify_direction(
            self.standardise(latest_monthly_change)
        )
        self.momentum_direction = self.classify_direction(
            self.standardise(three_month_momentum)
        )
        self.trend_direction = self.classify_direction(
            self.standardise(six_month_trend)
        )
        # Use 3-month momentum as the primary
        # underlying indicator direction.
        self.direction = self.momentum_direction

        # -------------------------------------------
        # Strength scores
        # -------------------------------------------

        self.magnitude_score = self.calculate_magnitude_score()
        self.persistence_score = self.calculate_persistence_score()
        self.consistency_score = self.calculate_consistency_score()

        self.score = self.calculate_score()
        self.signal_strength = self.classify_signal_strength()

    def standardise(self, value: NumericValue | None) -> NumericValue:
        """Scale a value by twelve-month volatility for signal comparison.

        Returns zero when the value or volatility is missing, or when volatility
        is not positive.
        """
        volatility = self.twelve_month_volatility

        if (
            value is None
            or pd.isna(value)
            or volatility is None
            or pd.isna(volatility)
            or volatility <= 0
        ):
            return 0.0

        return value / volatility

    def classify_direction(self, value: NumericValue) -> Direction:
        """Classify a standardized value using the direction threshold."""
        if value > self.direction_threshold:
            return Direction.POSITIVE

        if value < -self.direction_threshold:
            return Direction.NEGATIVE

        return Direction.NEUTRAL

    def calculate_magnitude_score(self) -> int:
        """Score the latest change's absolute standardized magnitude.

        Returns 0 below 0.75 standard deviations, 1 from 0.75 to below 1.5,
        and 2 at 1.5 standard deviations or greater.
        """

        z = abs(self.standardise(self.latest_monthly_change))

        if z >= 1.5:
            return 2

        if z >= 0.75:
            return 1

        return 0

    def calculate_persistence_score(self) -> int:
        """Score how consistently recent changes support momentum direction.

        Returns 2 when all three latest changes match the three-month momentum
        direction, 1 when two match, and 0 otherwise or for neutral momentum.
        """

        direction = self.momentum_direction

        if direction == Direction.NEUTRAL:
            return 0

        last_three_months_changes = self.monthly_changes.iloc[-3:]

        last_three_months_directions = [
            self.classify_direction(self.standardise(monthly_change))
            for monthly_change in last_three_months_changes
            if not pd.isna(monthly_change)
        ]

        matching = last_three_months_directions.count(direction)

        if matching == 3:
            return 2

        if matching == 2:
            return 1

        return 0

    def calculate_consistency_score(self) -> int:
        """Score agreement across latest change, momentum, and trend direction.

        Returns 2 for three matching positive or negative directions, 1 when two
        agree, and 0 otherwise.
        """

        signals = [
            self.latest_direction,
            self.momentum_direction,
            self.trend_direction,
        ]

        positive = signals.count(Direction.POSITIVE)
        negative = signals.count(Direction.NEGATIVE)

        if positive == 3 or negative == 3:
            return 2

        if positive >= 2 or negative >= 2:
            return 1

        return 0

    def calculate_score(self) -> int:
        """Return the sum of magnitude, persistence, and consistency scores."""
        return self.magnitude_score + self.persistence_score + self.consistency_score

    def classify_signal_strength(self) -> Strength:
        """Map the combined zero-to-six score to weak, moderate, or strong."""
        if self.score >= 5:
            return Strength.STRONG

        if self.score >= 2:
            return Strength.MODERATE

        return Strength.WEAK


class OverallBreadthSignal:
    """
    Calculate theme breadth and overall directional signal.
    """

    def __init__(
        self,
        breadth_directions: list[Direction],
        signal_data: list[SignalDatum],
    ) -> None:
        """Calculate breadth counts and an aggregate directional signal.

        Args:
            breadth_directions: Directions included in the breadth calculation.
            signal_data: Indicator directions and strength scores to aggregate.
        """
        self.breadth_total = len(breadth_directions)
        self.breadth_positive = breadth_directions.count(Direction.POSITIVE)
        self.breadth_negative = breadth_directions.count(Direction.NEGATIVE)
        self.breadth_neutral = breadth_directions.count(Direction.NEUTRAL)
        self.breadth_classification = self.classify_breadth()

        self.overall_signal = self.calculate_theme_signal(signal_data)

    def classify_breadth(self) -> BreadthClassification:
        """Classify breadth when one direction represents at least two thirds.

        Returns ``insufficient_data`` when no breadth directions are available
        and ``mixed`` when no direction reaches the threshold.
        """
        if self.breadth_total == 0:
            return "insufficient_data"

        positive_share = self.breadth_positive / self.breadth_total
        negative_share = self.breadth_negative / self.breadth_total
        neutral_share = self.breadth_neutral / self.breadth_total

        if positive_share >= BREADTH_RATIO:
            return BroadClassification.BROAD_POSITIVE

        if negative_share >= BREADTH_RATIO:
            return BroadClassification.BROAD_NEGATIVE

        if neutral_share >= BREADTH_RATIO:
            return BroadClassification.BROADLY_STABLE

        return BroadClassification.MIXED

    @staticmethod
    def calculate_theme_signal(signal_data: list[SignalDatum]) -> OverallSignal:
        """Aggregate indicator direction and strength into an overall signal.

        Direction is based on the mean signed indicator score, while strength is
        based on the mean unsigned score. Empty input is explicitly marked as
        insufficient rather than being conflated with a neutral, weak signal.
        """
        if not signal_data:
            return {
                "status": "insufficient_data",
            }

        # -----------------------------------
        # 1. Overall direction
        # -----------------------------------

        signed_scores = [
            DIRECTION_VALUES[signal["direction"]] * signal["score"]
            for signal in signal_data
        ]

        direction_score = sum(signed_scores) / len(signed_scores)

        if direction_score > 0.5:
            direction = Direction.POSITIVE

        elif direction_score < -0.5:
            direction = Direction.NEGATIVE

        else:
            direction = Direction.NEUTRAL

        # -----------------------------------
        # 2. Overall signal strength
        # -----------------------------------

        strength_score = sum(signal["score"] for signal in signal_data) / len(
            signal_data
        )

        if strength_score >= 4:
            strength = Strength.STRONG

        elif strength_score >= 2:
            strength = Strength.MODERATE

        else:
            strength = Strength.WEAK

        return {
            "status": "available",
            "direction": direction,
            "direction_score": round(direction_score, 2),
            "strength_score": round(strength_score, 2),
            "strength": strength,
        }


def _select_indicator_observations(
    observations: pd.DataFrame,
    indicator_name: str,
    observation_offset: int,
) -> pd.DataFrame:
    """Return ordered, non-null observations for one snapshot position."""
    indicator_observations = (
        observations.loc[
            observations["full_name"] == indicator_name,
            ["value", "date"],
        ]
        .sort_values("date")
        .dropna(subset=["value"])
        .copy()
    )

    if observation_offset <= 0:
        return indicator_observations

    if len(indicator_observations) <= observation_offset:
        return indicator_observations.iloc[0:0]

    return indicator_observations.iloc[:-observation_offset]


def _calculate_indicator_metric(
    indicator_name: str,
    indicator_observations: pd.DataFrame,
) -> tuple[IndicatorMetric, SignalDatum] | None:
    """Calculate one indicator metric and its sector-level signal input."""
    if len(indicator_observations) < 2:
        return None

    observation_values = (
        indicator_observations["value"].astype(float).reset_index(drop=True)
    )
    monthly_changes = signal_transform(
        indicator=indicator_name,
        series=observation_values,
    )
    if monthly_changes.empty:
        return None

    latest_change = monthly_changes.iloc[-1]
    three_month_momentum = monthly_changes.iloc[-3:].mean()
    six_month_trend = monthly_changes.iloc[-6:].mean()
    twelve_month_volatility = monthly_changes.iloc[-12:].std()

    signal_strength = IndicatorSignalStrength(
        monthly_changes=monthly_changes,
        latest_monthly_change=latest_change,
        three_month_momentum=three_month_momentum,
        six_month_trend=six_month_trend,
        twelve_month_volatility=twelve_month_volatility,
    )
    indicator_metric: IndicatorMetric = {
        "latest_observation_date": pd.Timestamp(indicator_observations["date"].iloc[-1])
        .date()
        .isoformat(),
        "latest_value": to_python_number(observation_values.iloc[-1]),
        "signal_transform": SIGNAL_TRANSFORMS[indicator_name],
        "signal_unit": SIGNAL_CONFIG[indicator_name]["unit"],
        "latest_signal_change": round(float(latest_change), 3),
        "three_month_momentum": round(float(three_month_momentum), 3),
        "six_month_trend": round(float(six_month_trend), 3),
        "twelve_month_volatility": (
            None
            if pd.isna(twelve_month_volatility)
            else round(float(twelve_month_volatility), 3)
        ),
        "direction": signal_strength.direction,
        "signal_strength": signal_strength.signal_strength,
        "signal_score": signal_strength.score,
    }
    sector_signal: SignalDatum = {
        "indicator": indicator_name,
        "direction": signal_strength.direction,
        "score": signal_strength.score,
    }
    return indicator_metric, sector_signal


def _summarize_theme_breadth(
    breadth_directions: list[Direction],
) -> dict[str, Any]:
    """Build theme-level breadth counts and an explicit classification."""
    breadth_signal = OverallBreadthSignal(
        breadth_directions=breadth_directions,
        signal_data=[],
    )
    return {
        "classification": breadth_signal.breadth_classification,
        Direction.POSITIVE: breadth_signal.breadth_positive,
        Direction.NEGATIVE: breadth_signal.breadth_negative,
        Direction.NEUTRAL: breadth_signal.breadth_neutral,
    }


def calculate_metrics_snapshot(
    observations: pd.DataFrame,
    observation_offset: int = 0,
) -> MetricsSnapshot:
    """Build a deterministic snapshot of configured economic indicators.

    For each indicator in ``THEME_INDICATORS_MAP``, observations are ordered by
    date and transformed according to ``SIGNAL_CONFIG``. The snapshot includes
    the latest transformed change, three- and six-month averages, twelve-month
    volatility, and volatility-adjusted direction and strength classifications.
    It also aggregates indicator signals into sector-level overall signals and
    configured breadth components into theme-level breadth classifications.

    Indicators with fewer than two usable observations at the requested offset
    are omitted.

    Args:
        observations: Observation data containing ``full_name``, ``date``, and
            ``value`` columns.
        observation_offset: Number of the most recent observations to exclude
            from each indicator. Use ``0`` for the latest snapshot or ``1`` for
            the snapshot immediately preceding each indicator's latest value.

    Returns:
        Metrics grouped by theme and sector, including per-indicator metrics,
        sector overall signals, and theme breadth summaries where configured.
    """

    snapshot: MetricsSnapshot = {}

    for theme, sectors in THEME_INDICATORS_MAP.items():
        theme_metrics: dict[str, Any] = {}
        breadth_directions: list[Direction] = []
        breadth_signal_groups: set[str] = set()

        for sector_name, indicator_names in sectors.items():
            sector_metrics: dict[str, Any] = {}
            sector_signal_data: list[SignalDatum] = []
            sector_signal_groups: set[str] = set()

            for indicator_name in indicator_names:
                indicator_observations = _select_indicator_observations(
                    observations,
                    indicator_name,
                    observation_offset,
                )
                calculation = _calculate_indicator_metric(
                    indicator_name,
                    indicator_observations,
                )
                if calculation is None:
                    continue

                indicator_metric, indicator_signal = calculation
                sector_metrics[indicator_name] = indicator_metric
                signal_group = str(
                    SIGNAL_CONFIG[indicator_name].get("signal_group", indicator_name)
                )

                if signal_group not in sector_signal_groups:
                    sector_signal_data.append(indicator_signal)
                    sector_signal_groups.add(signal_group)

                if (
                    indicator_name in BREADTH_COMPONENTS.get(theme, [])
                    and signal_group not in breadth_signal_groups
                ):
                    breadth_directions.append(indicator_signal["direction"])
                    breadth_signal_groups.add(signal_group)

            aggregate_sector_signal = OverallBreadthSignal(
                breadth_directions=[],
                signal_data=sector_signal_data,
            )
            sector_metrics["overall_signal"] = aggregate_sector_signal.overall_signal
            theme_metrics[sector_name] = sector_metrics

        theme_metrics["overall_breadth"] = _summarize_theme_breadth(breadth_directions)
        snapshot[theme] = theme_metrics

    return snapshot
