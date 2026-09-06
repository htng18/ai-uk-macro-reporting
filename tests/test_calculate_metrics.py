import numpy as np
import pandas as pd
import pytest

import ai_uk_macro_reporting.calculation.calculate_metrics as metrics_module
from ai_uk_macro_reporting.calculation.calculate_metrics import (
    IndicatorSignalStrength,
    OverallBreadthSignal,
    calculate_metrics_snapshot,
    signal_transform,
    to_python_number,
)
from ai_uk_macro_reporting.common import (
    BroadClassification,
    Direction,
    SignalTransform,
    SignalUnit,
    Strength,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (np.int64(4), 4),
        (np.float64(2.5), 2.5),
        (np.nan, None),
        (pd.NA, None),
        ("unchanged", "unchanged"),
    ],
)
def test_to_python_number_normalizes_scalar_values(value, expected):
    result = to_python_number(value)

    assert result == expected
    if expected is not None and isinstance(value, (np.integer, np.floating)):
        assert type(result) in (int, float)


def test_signal_transform_applies_percentage_change():
    result = signal_transform(
        "Monthly GDP Index",
        pd.Series([100.0, 110.0, 121.0]),
    )

    assert result.tolist() == pytest.approx([10.0, 10.0])


def test_signal_transform_applies_difference_and_direction_multiplier():
    result = signal_transform(
        "Unemployment Rate",
        pd.Series([5.0, 4.0, 3.5]),
    )

    assert result.tolist() == pytest.approx([1.0, 0.5])


def test_signal_transform_preserves_as_reported_monthly_rate():
    result = signal_transform(
        "Monthly GDP Growth Rate",
        pd.Series([0.2, -0.1, 0.3]),
    )

    assert result.tolist() == pytest.approx([0.2, -0.1, 0.3])


def test_signal_transform_rejects_unconfigured_indicator():
    with pytest.raises(ValueError, match="No signal configuration"):
        signal_transform("Unknown indicator", pd.Series([1.0, 2.0]))


def test_signal_config_covers_every_grouped_indicator_exactly_once():
    grouped_indicators = [
        indicator
        for sectors in metrics_module.THEME_INDICATORS_MAP.values()
        for indicators in sectors.values()
        for indicator in indicators
    ]

    assert len(grouped_indicators) == len(set(grouped_indicators))
    assert set(grouped_indicators) == set(metrics_module.SIGNAL_CONFIG)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.51, Direction.POSITIVE),
        (0.5, Direction.NEUTRAL),
        (-0.5, Direction.NEUTRAL),
        (-0.51, Direction.NEGATIVE),
    ],
)
def test_indicator_direction_threshold_boundaries(value, expected):
    signal = IndicatorSignalStrength(
        monthly_changes=pd.Series(dtype=float),
        latest_monthly_change=None,
        three_month_momentum=None,
        six_month_trend=None,
        twelve_month_volatility=None,
    )

    assert signal.classify_direction(value) == expected


def test_indicator_signal_classifies_persistent_large_change_as_strong():
    signal = IndicatorSignalStrength(
        monthly_changes=pd.Series([2.0, 2.0, 2.0]),
        latest_monthly_change=2.0,
        three_month_momentum=2.0,
        six_month_trend=2.0,
        twelve_month_volatility=1.0,
    )

    assert signal.direction == Direction.POSITIVE
    assert signal.magnitude_score == 2
    assert signal.persistence_score == 2
    assert signal.consistency_score == 2
    assert signal.score == 6
    assert signal.signal_strength == Strength.STRONG


@pytest.mark.parametrize("volatility", [None, np.nan, 0.0, -1.0])
def test_indicator_signal_treats_unusable_volatility_as_neutral(volatility):
    signal = IndicatorSignalStrength(
        monthly_changes=pd.Series([2.0, 2.0, 2.0]),
        latest_monthly_change=2.0,
        three_month_momentum=2.0,
        six_month_trend=2.0,
        twelve_month_volatility=volatility,
    )

    assert signal.direction == Direction.NEUTRAL
    assert signal.score == 0
    assert signal.signal_strength == Strength.WEAK


@pytest.mark.parametrize(
    ("directions", "expected"),
    [
        ([], "insufficient_data"),
        (
            [Direction.POSITIVE, Direction.POSITIVE, Direction.NEGATIVE],
            BroadClassification.BROAD_POSITIVE,
        ),
        (
            [Direction.NEGATIVE, Direction.NEGATIVE, Direction.NEUTRAL],
            BroadClassification.BROAD_NEGATIVE,
        ),
        (
            [Direction.NEUTRAL, Direction.NEUTRAL, Direction.POSITIVE],
            BroadClassification.BROADLY_STABLE,
        ),
        (
            [Direction.POSITIVE, Direction.NEGATIVE, Direction.NEUTRAL],
            BroadClassification.MIXED,
        ),
    ],
)
def test_overall_breadth_classifies_direction_shares(directions, expected):
    breadth = OverallBreadthSignal(directions, [])

    assert breadth.breadth_classification == expected


def test_calculate_theme_signal_aggregates_signed_direction_and_strength():
    result = OverallBreadthSignal.calculate_theme_signal(
        [
            {
                "indicator": "expansion",
                "direction": Direction.POSITIVE,
                "score": 6,
            },
            {
                "indicator": "contraction",
                "direction": Direction.NEGATIVE,
                "score": 1,
            },
        ]
    )

    assert result == {
        "status": "available",
        "direction": Direction.POSITIVE,
        "direction_score": 2.5,
        "strength_score": 3.5,
        "strength": Strength.MODERATE,
    }


def test_calculate_theme_signal_marks_empty_input_as_insufficient():
    assert OverallBreadthSignal.calculate_theme_signal([]) == {
        "status": "insufficient_data",
    }


def test_calculate_metrics_snapshot_orders_rows_and_applies_offset(monkeypatch):
    indicator = "CPI Services Inflation"
    monkeypatch.setattr(
        metrics_module,
        "THEME_INDICATORS_MAP",
        {"inflation": {"composition": [indicator]}},
    )
    monkeypatch.setattr(
        metrics_module,
        "BREADTH_COMPONENTS",
        {"inflation": [indicator]},
    )
    observations = pd.DataFrame(
        [
            {"full_name": indicator, "date": "2024-03-01", "value": 3.0},
            {"full_name": indicator, "date": "2024-01-01", "value": 0.0},
            {"full_name": indicator, "date": "2024-02-01", "value": 1.0},
        ]
    )

    current = calculate_metrics_snapshot(observations)
    previous = calculate_metrics_snapshot(observations, observation_offset=1)

    current_metric = current["inflation"]["composition"][indicator]
    assert current_metric == {
        "latest_observation_date": "2024-03-01",
        "latest_value": 3.0,
        "signal_transform": SignalTransform.DIFFERENCE,
        "signal_unit": SignalUnit.PERCENTAGE_POINT,
        "latest_signal_change": 2.0,
        "three_month_momentum": 1.5,
        "six_month_trend": 1.5,
        "twelve_month_volatility": pytest.approx(0.707),
        "direction": Direction.POSITIVE,
        "signal_strength": Strength.STRONG,
        "signal_score": 5,
    }
    assert current["inflation"]["overall_breadth"] == {
        "classification": BroadClassification.BROAD_POSITIVE,
        Direction.POSITIVE: 1,
        Direction.NEGATIVE: 0,
        Direction.NEUTRAL: 0,
    }

    previous_metric = previous["inflation"]["composition"][indicator]
    assert previous_metric["latest_observation_date"] == "2024-02-01"
    assert previous_metric["latest_value"] == 1.0
    assert previous_metric["latest_signal_change"] == 1.0
    assert previous_metric["twelve_month_volatility"] is None
    assert previous_metric["direction"] == Direction.NEUTRAL


def test_calculate_metrics_snapshot_omits_indicator_without_two_values(monkeypatch):
    indicator = "CPI Services Inflation"
    monkeypatch.setattr(
        metrics_module,
        "THEME_INDICATORS_MAP",
        {"inflation": {"composition": [indicator]}},
    )
    monkeypatch.setattr(
        metrics_module,
        "BREADTH_COMPONENTS",
        {"inflation": [indicator]},
    )
    observations = pd.DataFrame(
        [{"full_name": indicator, "date": "2024-01-01", "value": 1.0}]
    )

    snapshot = calculate_metrics_snapshot(observations)

    assert indicator not in snapshot["inflation"]["composition"]
    assert snapshot["inflation"]["composition"]["overall_signal"] == {
        "status": "insufficient_data",
    }
    assert snapshot["inflation"]["overall_breadth"] == {
        "classification": "insufficient_data",
        Direction.POSITIVE: 0,
        Direction.NEGATIVE: 0,
        Direction.NEUTRAL: 0,
    }


def test_calculate_metrics_snapshot_deduplicates_equivalent_signal_groups(monkeypatch):
    indicators = ["Monthly GDP Index", "Monthly GDP Growth Rate"]
    monkeypatch.setattr(
        metrics_module,
        "THEME_INDICATORS_MAP",
        {"output_demand": {"output": indicators}},
    )
    monkeypatch.setattr(
        metrics_module,
        "BREADTH_COMPONENTS",
        {"output_demand": indicators},
    )

    def fake_calculation(indicator_name, observations):
        direction = (
            Direction.POSITIVE
            if indicator_name == "Monthly GDP Index"
            else Direction.NEGATIVE
        )
        return {}, {"indicator": indicator_name, "direction": direction, "score": 6}

    monkeypatch.setattr(
        metrics_module,
        "_calculate_indicator_metric",
        fake_calculation,
    )
    observations = pd.DataFrame(columns=["full_name", "date", "value"])

    snapshot = calculate_metrics_snapshot(observations)

    assert snapshot["output_demand"]["output"]["overall_signal"] == {
        "status": "available",
        "direction": Direction.POSITIVE,
        "direction_score": 6.0,
        "strength_score": 6.0,
        "strength": Strength.STRONG,
    }
    assert snapshot["output_demand"]["overall_breadth"] == {
        "classification": BroadClassification.BROAD_POSITIVE,
        Direction.POSITIVE: 1,
        Direction.NEGATIVE: 0,
        Direction.NEUTRAL: 0,
    }
