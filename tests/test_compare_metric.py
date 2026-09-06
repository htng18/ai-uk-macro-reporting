from types import SimpleNamespace

import pytest

from ai_uk_macro_reporting.calculation.compare_metric import (
    breadth_dominant_share,
    calculate_confidence_metrics,
    compare_breadth,
    compare_direction,
    compare_indicator,
    compare_metric_snapshots,
    compare_sector,
    compare_strength,
    compare_theme,
    extract_important_changes,
    extract_score,
)


def _report_with_confidence(level):
    return SimpleNamespace(overall_confidence=SimpleNamespace(level=level))


def test_calculate_confidence_metrics_aggregates_valid_thematic_confidence():
    state = SimpleNamespace(
        output_and_demand_report=_report_with_confidence("high"),
        inflation_report=_report_with_confidence("medium"),
        labour_market_report=_report_with_confidence("low"),
        monetary_policy_report=_report_with_confidence("high"),
    )

    assert calculate_confidence_metrics(state) == {
        "overall_confidence_score": 0.713,
        "overall_confidence": "medium",
        "theme_confidence_metrics": {
            "output_demand": {"confidence": "high", "score": 1.0},
            "inflation": {"confidence": "medium", "score": 0.6},
            "labour_market": {"confidence": "low", "score": 0.25},
            "monetary_policy": {"confidence": "high", "score": 1.0},
        },
    }


@pytest.mark.parametrize("invalid_level", [None, "uncertain", "HIGH"])
def test_calculate_confidence_metrics_rejects_invalid_thematic_confidence(
    invalid_level,
):
    state = SimpleNamespace(
        output_and_demand_report=_report_with_confidence(invalid_level),
        inflation_report=_report_with_confidence("medium"),
        labour_market_report=_report_with_confidence("low"),
        monetary_policy_report=_report_with_confidence("high"),
    )

    with pytest.raises(ValueError, match="output_demand"):
        calculate_confidence_metrics(state)


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        ("neutral", "neutral", "stable_neutral"),
        ("positive", "positive", "persistent"),
        ("negative", "negative", "persistent"),
        ("neutral", "positive", "emerging_positive"),
        ("neutral", "negative", "emerging_negative"),
        ("positive", "neutral", "faded_positive"),
        ("negative", "neutral", "faded_negative"),
        ("positive", "negative", "reversed_negative"),
        ("negative", "positive", "reversed_positive"),
    ],
)
def test_compare_direction_classifies_valid_transitions(previous, current, expected):
    assert compare_direction(previous, current) == expected


@pytest.mark.parametrize(
    ("previous", "current"),
    [
        (None, "positive"),
        ("positive", None),
        ("", ""),
        ("up", "up"),
        ("Positive", "positive"),
        ([], "positive"),
    ],
)
def test_compare_direction_rejects_missing_or_invalid_directions(previous, current):
    assert compare_direction(previous, current) == "insufficient_evidence"


@pytest.mark.parametrize(
    ("previous", "current", "expected"),
    [
        ("weak", "weak", "unchanged"),
        ("moderate", "moderate", "unchanged"),
        ("strong", "strong", "unchanged"),
        ("weak", "moderate", "strengthened"),
        ("weak", "strong", "strengthened"),
        ("moderate", "strong", "strengthened"),
        ("strong", "moderate", "weakened"),
        ("strong", "weak", "weakened"),
        ("moderate", "weak", "weakened"),
    ],
)
def test_compare_strength_classifies_valid_transitions(previous, current, expected):
    assert compare_strength(previous, current) == expected


@pytest.mark.parametrize(
    ("previous", "current"),
    [
        (None, "weak"),
        ("weak", None),
        ("", ""),
        ("powerful", "powerful"),
        ("Weak", "weak"),
        ([], "weak"),
    ],
)
def test_compare_strength_rejects_missing_or_invalid_strengths(previous, current):
    assert compare_strength(previous, current) == "insufficient_evidence"


@pytest.mark.parametrize(
    "invalid_score",
    [
        None,
        "invalid",
        [],
        pytest.param(10**10_000, id="overflow"),
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_extract_score_rejects_missing_malformed_or_non_finite_values(invalid_score):
    assert extract_score({"signal_score": invalid_score}) is None


def test_score_change_retains_precision_for_materiality_check():
    indicator_change = compare_indicator(
        "GDP",
        {"signal_score": 0},
        {"signal_score": 1.999},
    )
    themes = [
        {
            "theme": "output",
            "breadth_change": {"transition": "unchanged"},
            "sector_changes": [
                {
                    "sector": "activity",
                    "direction_transition": "stable_neutral",
                    "indicator_changes": [indicator_change],
                }
            ],
        }
    ]

    assert indicator_change["score_change"] == pytest.approx(1.999)
    assert extract_important_changes(themes)["important_changes"] == []


def test_extract_important_changes_describes_breadth_composition():
    summaries = extract_important_changes(
        [
            {
                "theme": "output",
                "breadth_change": {
                    "transition": "composition_changed",
                    "previous_classification": "mixed",
                    "current_classification": "mixed",
                    "previous_dominant_direction": "positive",
                    "current_dominant_direction": "negative",
                },
                "sector_changes": [],
            }
        ]
    )

    assert summaries["important_changes"] == [
        "output: breadth composition changed from positive to negative."
    ]


def test_extract_important_changes_omits_missing_classification_label():
    summaries = extract_important_changes(
        [
            {
                "theme": "output",
                "breadth_change": {
                    "transition": "classification_changed",
                    "previous_classification": None,
                    "current_classification": "positive",
                },
                "sector_changes": [],
            }
        ]
    )

    assert summaries["important_changes"] == [
        "output: breadth classification changed to positive."
    ]


def test_compare_sector_handles_malformed_signal_and_indicator_payloads():
    comparison = compare_sector(
        "activity",
        {
            "overall_signal": None,
            "GDP": {"direction": "positive", "signal_strength": "moderate"},
        },
        {
            "overall_signal": [],
            "GDP": None,
        },
    )

    assert comparison["direction_transition"] == "insufficient_evidence"
    assert comparison["strength_transition"] == "insufficient_evidence"
    assert comparison["new_indicators"] == []
    assert comparison["removed_indicators"] == []
    assert comparison["indicator_changes"][0]["indicator"] == "GDP"
    assert (
        comparison["indicator_changes"][0]["direction_transition"]
        == "insufficient_evidence"
    )


def test_compare_sector_ignores_nested_metadata():
    comparison = compare_sector(
        "activity",
        {"metadata": {"source": "ONS"}},
        {"metadata": {"source": "ONS"}},
    )

    assert comparison["indicator_changes"] == []
    assert comparison["new_indicators"] == []
    assert comparison["removed_indicators"] == []


def test_compare_theme_handles_malformed_breadth_and_sector_payloads():
    comparison = compare_theme(
        "output",
        {
            "overall_breadth": [],
            "activity": {
                "overall_signal": {
                    "direction": "positive",
                    "strength": "moderate",
                },
                "GDP": {
                    "direction": "positive",
                    "signal_strength": "moderate",
                },
            },
        },
        {
            "overall_breadth": {
                "classification": "positive",
                "positive": 2,
                "negative": 0,
                "neutral": 1,
            },
            "activity": None,
        },
    )

    assert comparison["breadth_change"]["transition"] == "insufficient_evidence"
    assert comparison["new_sectors"] == []
    assert comparison["removed_sectors"] == []

    sector = comparison["sector_changes"][0]
    assert sector["sector"] == "activity"
    assert sector["direction_transition"] == "insufficient_evidence"
    assert sector["new_indicators"] == []
    assert sector["removed_indicators"] == []
    assert sector["indicator_changes"][0]["indicator"] == "GDP"
    assert (
        sector["indicator_changes"][0]["direction_transition"]
        == "insufficient_evidence"
    )


def test_breadth_dominant_share_returns_full_precision():
    direction, share = breadth_dominant_share(
        {"positive": 2, "negative": 0, "neutral": 1}
    )

    assert direction == "positive"
    assert share == pytest.approx(2 / 3)


def test_breadth_dominant_share_rejects_tied_counts():
    assert breadth_dominant_share({"positive": 2, "negative": 2, "neutral": 1}) == (
        None,
        None,
    )


@pytest.mark.parametrize("invalid_count", [None, "2", -1, float("inf"), True])
def test_breadth_dominant_share_rejects_invalid_counts(invalid_count):
    assert breadth_dominant_share(
        {"positive": invalid_count, "negative": 1, "neutral": 0}
    ) == (None, None)


def test_compare_breadth_detects_exact_materiality_boundary():
    previous = {
        "classification": "positive",
        "positive": 2,
        "negative": 0,
        "neutral": 1,
    }
    current = {
        "classification": "positive",
        "positive": 23,
        "negative": 0,
        "neutral": 7,
    }

    comparison = compare_breadth(previous, current)

    assert comparison["transition"] == "broadened"
    assert comparison["previous_dominant_share"] == pytest.approx(2 / 3)
    assert comparison["current_dominant_share"] == pytest.approx(23 / 30)


def test_compare_breadth_detects_exact_negative_materiality_boundary():
    previous = {
        "classification": "positive",
        "positive": 23,
        "negative": 0,
        "neutral": 7,
    }
    current = {
        "classification": "positive",
        "positive": 2,
        "negative": 0,
        "neutral": 1,
    }

    assert compare_breadth(previous, current)["transition"] == "narrowed"


@pytest.mark.parametrize(
    "material_change",
    [0, -0.1, float("nan"), float("inf"), True, "invalid"],
)
def test_compare_breadth_rejects_invalid_material_change(material_change):
    breadth = {
        "classification": "positive",
        "positive": 2,
        "negative": 0,
        "neutral": 1,
    }

    with pytest.raises(ValueError, match="material_change"):
        compare_breadth(breadth, breadth, material_change)


def test_compare_breadth_normalizes_numeric_material_change():
    breadth = {
        "classification": "positive",
        "positive": 2,
        "negative": 0,
        "neutral": 1,
    }

    assert compare_breadth(breadth, breadth, "0.1")["transition"] == "unchanged"


def test_compare_breadth_returns_consistent_shape_without_payloads():
    assert compare_breadth(None, {}) == {
        "previous_classification": None,
        "current_classification": None,
        "previous_dominant_direction": None,
        "current_dominant_direction": None,
        "previous_dominant_share": None,
        "current_dominant_share": None,
        "transition": "insufficient_evidence",
    }


def test_compare_breadth_exposes_precision_used_for_transition():
    previous = {
        "classification": "positive",
        "positive": 4,
        "negative": 0,
        "neutral": 3,
    }
    current = {
        "classification": "positive",
        "positive": 49,
        "negative": 0,
        "neutral": 24,
    }

    comparison = compare_breadth(previous, current)

    assert comparison["transition"] == "unchanged"
    assert (
        comparison["current_dominant_share"] - comparison["previous_dominant_share"]
        < 0.10
    )


@pytest.mark.parametrize("malformed_theme", [None, {}])
def test_compare_metric_snapshots_handles_malformed_theme_and_ignores_metadata(
    malformed_theme,
):
    comparison = compare_metric_snapshots(
        {
            "metadata": {"source": "ONS"},
            "output": {
                "overall_breadth": {
                    "classification": "positive",
                    "positive": 2,
                    "negative": 0,
                    "neutral": 1,
                },
                "activity": {
                    "overall_signal": {
                        "direction": "positive",
                        "strength": "moderate",
                    },
                    "GDP": {
                        "direction": "positive",
                        "signal_strength": "moderate",
                    },
                },
            },
        },
        {
            "metadata": {"source": "updated"},
            "output": malformed_theme,
        },
        "2026-01",
        "2026-02",
    )

    assert comparison["new_themes"] == []
    assert comparison["removed_themes"] == []
    assert [theme["theme"] for theme in comparison["themes"]] == ["output"]

    output = comparison["themes"][0]
    assert output["breadth_change"]["transition"] == "insufficient_evidence"
    assert output["new_sectors"] == []
    assert output["removed_sectors"] == []
    assert output["sector_changes"][0]["indicator_changes"][0]["indicator"] == "GDP"


@pytest.mark.parametrize(
    ("previous_period", "current_period"),
    [(None, "2026-02"), ("", "2026-02"), ("2026-01", None), ("2026-01", "")],
)
def test_compare_metric_snapshots_rejects_missing_periods(
    previous_period, current_period
):
    with pytest.raises(ValueError, match="reporting_period"):
        compare_metric_snapshots({}, {}, previous_period, current_period)


def test_compare_metric_snapshots_preserves_comparison_behaviour():
    previous_metrics = {
        "removed_theme": {"overall_breadth": {}},
        "output": {
            "overall_breadth": {
                "classification": "positive",
                "positive": 6,
                "negative": 2,
                "neutral": 2,
            },
            "removed_sector": {"overall_signal": {}},
            "activity": {
                "overall_signal": {
                    "direction": "positive",
                    "strength": "moderate",
                },
                "GDP": {
                    "direction": "positive",
                    "signal_strength": "moderate",
                    "signal_score": "2",
                    "latest_value": 100,
                    "latest_observation_date": "2026-01-01",
                },
                "Services": {
                    "direction": "neutral",
                    "strength": "weak",
                    "score": 0,
                },
                "removed_indicator": {"direction": "neutral"},
            },
        },
    }
    current_metrics = {
        "new_theme": {"overall_breadth": {}},
        "output": {
            "overall_breadth": {
                "classification": "positive",
                "positive": 8,
                "negative": 1,
                "neutral": 1,
            },
            "new_sector": {"overall_signal": {}},
            "activity": {
                "overall_signal": {
                    "direction": "negative",
                    "strength": "strong",
                },
                "GDP": {
                    "direction": "negative",
                    "signal_strength": "strong",
                    "signal_score": 5,
                    "latest_value": 99,
                    "latest_observation_date": "2026-02-01",
                },
                "Services": {
                    "direction": "positive",
                    "strength": "moderate",
                    "score": 1,
                },
                "new_indicator": {"direction": "neutral"},
            },
        },
    }

    comparison = compare_metric_snapshots(
        previous_metrics,
        current_metrics,
        "2026-01",
        "2026-02",
    )

    assert comparison["previous_reporting_period"] == "2026-01"
    assert comparison["current_reporting_period"] == "2026-02"
    assert comparison["new_themes"] == ["new_theme"]
    assert comparison["removed_themes"] == ["removed_theme"]

    theme = comparison["themes"][0]
    assert theme["theme"] == "output"
    assert theme["breadth_change"] == {
        "previous_classification": "positive",
        "current_classification": "positive",
        "previous_dominant_direction": "positive",
        "current_dominant_direction": "positive",
        "previous_dominant_share": 0.6,
        "current_dominant_share": 0.8,
        "transition": "broadened",
    }
    assert theme["new_sectors"] == ["new_sector"]
    assert theme["removed_sectors"] == ["removed_sector"]

    sector = theme["sector_changes"][0]
    assert sector["sector"] == "activity"
    assert sector["direction_transition"] == "reversed_negative"
    assert sector["strength_transition"] == "strengthened"
    assert sector["new_indicators"] == ["new_indicator"]
    assert sector["removed_indicators"] == ["removed_indicator"]

    gdp, services = sector["indicator_changes"]
    assert gdp["indicator"] == "GDP"
    assert gdp["direction_transition"] == "reversed_negative"
    assert gdp["strength_transition"] == "strengthened"
    assert gdp["previous_score"] == 2.0
    assert gdp["current_score"] == 5.0
    assert gdp["score_change"] == 3.0
    assert gdp["previous_latest_value"] == 100
    assert gdp["current_latest_value"] == 99
    assert services["indicator"] == "Services"
    assert services["direction_transition"] == "emerging_positive"

    assert comparison["important_changes"] == [
        "output: positive breadth broadened from 60.0% to 80.0%.",
        "output/activity: reversed_negative.",
        "output/activity: signal strengthened from moderate to strong.",
        "output/activity/GDP: signal strengthened from moderate to strong.",
        "output/activity/GDP: signal score changed from 2.0 to 5.0.",
        "output/activity/Services: signal strengthened from weak to moderate.",
    ]
    assert comparison["persistent_features"] == []
    assert comparison["reversals"] == ["output/activity/GDP: reversed_negative."]
    assert comparison["emerging_signals"] == [
        "output/activity/Services: emerging_positive."
    ]
    assert comparison["fading_signals"] == []


def test_compare_metric_snapshots_handles_empty_snapshots():
    assert compare_metric_snapshots({}, {}, "2026-01", "2026-02") == {
        "previous_reporting_period": "2026-01",
        "current_reporting_period": "2026-02",
        "themes": [],
        "important_changes": [],
        "persistent_features": [],
        "reversals": [],
        "emerging_signals": [],
        "fading_signals": [],
        "new_themes": [],
        "removed_themes": [],
    }


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"signal_score": "2.5"}, 2.5),
        ({"score": 3}, 3.0),
        ({"signal_score": 0, "score": 4}, 0.0),
        ({"signal_score": None, "score": 4}, None),
    ],
)
def test_extract_score_supports_snapshot_field_names(payload, expected):
    assert extract_score(payload) == expected


def test_compare_indicator_reports_values_dates_and_missing_score():
    comparison = compare_indicator(
        "GDP",
        {
            "direction": "neutral",
            "strength": "weak",
            "score": 1,
            "latest_value": 100,
            "latest_observation_date": "2026-01-01",
        },
        {
            "direction": "positive",
            "signal_strength": "moderate",
            "latest_value": 101,
            "latest_observation_date": "2026-02-01",
        },
    )

    assert comparison == {
        "indicator": "GDP",
        "previous_direction": "neutral",
        "current_direction": "positive",
        "direction_transition": "emerging_positive",
        "previous_strength": "weak",
        "current_strength": "moderate",
        "strength_transition": "strengthened",
        "previous_score": 1.0,
        "current_score": None,
        "score_change": None,
        "previous_latest_value": 100,
        "current_latest_value": 101,
        "previous_observation_date": "2026-01-01",
        "current_observation_date": "2026-02-01",
    }


def test_compare_sector_sorts_indicator_membership():
    comparison = compare_sector(
        "activity",
        {
            "overall_signal": {
                "direction": "positive",
                "strength": "moderate",
            },
            "shared_b": {"direction": "positive"},
            "shared_a": {"direction": "neutral"},
            "removed_z": {"direction": "negative"},
        },
        {
            "overall_signal": {
                "direction": "positive",
                "strength": "moderate",
            },
            "shared_a": {"direction": "positive"},
            "shared_b": {"direction": "positive"},
            "new_z": {"direction": "neutral"},
            "new_a": {"direction": "neutral"},
        },
    )

    assert comparison["direction_transition"] == "persistent"
    assert [item["indicator"] for item in comparison["indicator_changes"]] == [
        "shared_a",
        "shared_b",
    ]
    assert comparison["new_indicators"] == ["new_a", "new_z"]
    assert comparison["removed_indicators"] == ["removed_z"]


def test_compare_theme_sorts_sector_membership_and_ignores_metadata():
    comparison = compare_theme(
        "output",
        {
            "sector_b": {"overall_signal": {}},
            "sector_a": {"overall_signal": {}},
            "removed": {"overall_signal": {}},
            "metadata": {"overall_signal_description": "not a sector"},
        },
        {
            "sector_a": {"overall_signal": {}},
            "sector_b": {"overall_signal": {}},
            "new_z": {"overall_signal": {}},
            "new_a": {"overall_signal": {}},
        },
    )

    assert [item["sector"] for item in comparison["sector_changes"]] == [
        "sector_a",
        "sector_b",
    ]
    assert comparison["new_sectors"] == ["new_a", "new_z"]
    assert comparison["removed_sectors"] == ["removed"]


def test_compare_breadth_prioritizes_dominant_direction_change():
    previous = {
        "classification": "broad_positive",
        "positive": 3,
        "negative": 1,
        "neutral": 0,
    }
    current = {
        "classification": "broad_negative",
        "positive": 1,
        "negative": 8,
        "neutral": 1,
    }

    comparison = compare_breadth(previous, current)

    assert comparison["transition"] == "composition_changed"
    assert comparison["previous_dominant_direction"] == "positive"
    assert comparison["current_dominant_direction"] == "negative"


def test_compare_breadth_reports_non_material_classification_change():
    previous = {
        "classification": "mixed",
        "positive": 6,
        "negative": 2,
        "neutral": 2,
    }
    current = {
        "classification": "broad_positive",
        "positive": 13,
        "negative": 4,
        "neutral": 3,
    }

    comparison = compare_breadth(previous, current)

    assert comparison["current_dominant_share"] == pytest.approx(0.65)
    assert comparison["transition"] == "classification_changed"


def test_breadth_dominant_share_rejects_zero_total():
    assert breadth_dominant_share({"positive": 0, "negative": 0, "neutral": 0}) == (
        None,
        None,
    )


def test_extract_important_changes_populates_all_summary_categories():
    summaries = extract_important_changes(
        [
            {
                "theme": "output",
                "breadth_change": {
                    "transition": "narrowed",
                    "current_dominant_direction": "positive",
                    "previous_dominant_share": 0.8,
                    "current_dominant_share": 0.6,
                },
                "sector_changes": [
                    {
                        "sector": "activity",
                        "direction_transition": "persistent",
                        "current_direction": "positive",
                        "previous_strength": "strong",
                        "current_strength": "moderate",
                        "strength_transition": "weakened",
                        "indicator_changes": [
                            {
                                "indicator": "GDP",
                                "direction_transition": "reversed_negative",
                                "strength_transition": "unchanged",
                                "previous_score": 4.0,
                                "current_score": 2.0,
                                "score_change": -2.0,
                            },
                            {
                                "indicator": "Services",
                                "direction_transition": "emerging_positive",
                                "strength_transition": "unchanged",
                                "score_change": None,
                            },
                            {
                                "indicator": "Production",
                                "direction_transition": "faded_negative",
                                "strength_transition": "unchanged",
                                "score_change": None,
                            },
                        ],
                    }
                ],
            }
        ]
    )

    assert summaries == {
        "important_changes": [
            "output: positive breadth narrowed from 80.0% to 60.0%.",
            "output/activity: signal weakened from strong to moderate.",
            "output/activity/GDP: signal score changed from 4.0 to 2.0.",
        ],
        "persistent_features": ["output/activity: positive signal persisted."],
        "reversals": ["output/activity/GDP: reversed_negative."],
        "emerging_signals": ["output/activity/Services: emerging_positive."],
        "fading_signals": ["output/activity/Production: faded_negative."],
    }


@pytest.mark.parametrize(
    ("level", "expected_score", "expected_confidence"),
    [
        ("low", 0.25, "low"),
        ("medium", 0.6, "medium"),
        ("high", 1.0, "high"),
    ],
)
def test_calculate_confidence_metrics_classifies_uniform_levels(
    level,
    expected_score,
    expected_confidence,
):
    report = _report_with_confidence(level)
    state = SimpleNamespace(
        output_and_demand_report=report,
        inflation_report=report,
        labour_market_report=report,
        monetary_policy_report=report,
    )

    result = calculate_confidence_metrics(state)

    assert result["overall_confidence_score"] == expected_score
    assert result["overall_confidence"] == expected_confidence


def test_compare_metric_snapshots_sorts_theme_membership():
    previous = {
        "shared_b": {"overall_breadth": {}},
        "shared_a": {"overall_breadth": {}},
        "removed_z": {"overall_breadth": {}},
    }
    current = {
        "shared_a": {"overall_breadth": {}},
        "shared_b": {"overall_breadth": {}},
        "new_z": {"overall_breadth": {}},
        "new_a": {"overall_breadth": {}},
    }

    comparison = compare_metric_snapshots(
        previous,
        current,
        "2026-01",
        "2026-02",
    )

    assert [theme["theme"] for theme in comparison["themes"]] == [
        "shared_a",
        "shared_b",
    ]
    assert comparison["new_themes"] == ["new_a", "new_z"]
    assert comparison["removed_themes"] == ["removed_z"]
