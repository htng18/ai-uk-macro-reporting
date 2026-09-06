"""Compare two deterministic metric snapshots and summarize their changes.

The comparison is deliberately descriptive. Directions are assumed to have
already been normalized by the metric-calculation layer, so this module does
not attach additional economic meaning to a positive or negative signal.
"""

import math
from numbers import Real
from typing import Any, TypedDict

from ai_uk_macro_reporting.common import (
    BreadthTransition,
    Confidence,
    Direction,
    DirectionTransition,
    Strength,
    ThemeName,
)

STRENGTH_RANK: dict[Strength, int] = {
    Strength.WEAK: 0,
    Strength.MODERATE: 1,
    Strength.STRONG: 2,
}

DIRECTION_TRANSITIONS: dict[
    tuple[Direction, Direction],
    DirectionTransition,
] = {
    (Direction.NEUTRAL, Direction.POSITIVE): DirectionTransition.EMERGING_POSITIVE,
    (Direction.NEUTRAL, Direction.NEGATIVE): DirectionTransition.EMERGING_NEGATIVE,
    (Direction.POSITIVE, Direction.NEUTRAL): DirectionTransition.FADED_POSITIVE,
    (Direction.NEGATIVE, Direction.NEUTRAL): DirectionTransition.FADED_NEGATIVE,
    (Direction.POSITIVE, Direction.NEGATIVE): DirectionTransition.REVERSED_NEGATIVE,
    (Direction.NEGATIVE, Direction.POSITIVE): DirectionTransition.REVERSED_POSITIVE,
}

IMPORTANT_DIRECTION_TRANSITIONS: set[DirectionTransition] = {
    DirectionTransition.EMERGING_POSITIVE,
    DirectionTransition.EMERGING_NEGATIVE,
    DirectionTransition.FADED_POSITIVE,
    DirectionTransition.FADED_NEGATIVE,
    DirectionTransition.REVERSED_POSITIVE,
    DirectionTransition.REVERSED_NEGATIVE,
}

IMPORTANT_STRENGTH_TRANSITIONS: set[str] = {
    "strengthened",
    "weakened",
}

MATERIAL_SCORE_CHANGE: int = 2

INDICATOR_FIELDS: frozenset[str] = frozenset(
    {
        "direction",
        "latest_observation_date",
        "latest_signal_change",
        "latest_value",
        "score",
        "signal_score",
        "signal_strength",
        "signal_transform",
        "signal_unit",
        "six_month_trend",
        "strength",
        "three_month_momentum",
        "twelve_month_volatility",
    }
)

CONFIDENCE_SCORES = {
    Confidence.LOW: 0.25,
    Confidence.MEDIUM: 0.6,
    Confidence.HIGH: 1.0,
}


class ChangeSummaries(TypedDict):
    """Prompt-ready summaries extracted from detailed snapshot comparisons."""

    important_changes: list[str]
    persistent_features: list[str]
    reversals: list[str]
    emerging_signals: list[str]
    fading_signals: list[str]


def breadth_dominant_share(
    breadth: dict[str, Any],
) -> tuple[str | None, float | None]:
    """Return the most common direction and its share of classified signals."""

    # Ignore any metadata in the breadth payload; only directional counts
    # contribute to the denominator.
    counts = {
        Direction.POSITIVE: breadth.get(Direction.POSITIVE, 0),
        Direction.NEGATIVE: breadth.get(Direction.NEGATIVE, 0),
        Direction.NEUTRAL: breadth.get(Direction.NEUTRAL, 0),
    }

    valid_counts = all(
        isinstance(count, Real)
        and not isinstance(count, bool)
        and math.isfinite(count)
        and count >= 0
        for count in counts.values()
    )

    if not valid_counts:
        return None, None

    total = sum(counts.values())

    if total == 0:
        return None, None

    dominant_count = max(counts.values())
    dominant_directions = [
        direction for direction, count in counts.items() if count == dominant_count
    ]

    if len(dominant_directions) != 1:
        return None, None

    dominant = dominant_directions[0]
    share = counts[dominant] / total

    return dominant, share


def compare_breadth(
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
    material_change: float = 0.10,
) -> dict[str, Any]:
    """Describe how a theme's directional breadth changed between snapshots.

    A change in dominant direction takes precedence over changes in its share.
    When the direction is stable, a ten-percentage-point move is material by
    default; classification-only changes are reported after that test.
    """

    try:
        if isinstance(material_change, bool):
            raise TypeError

        material_change = float(material_change)
    except (TypeError, ValueError):
        raise ValueError(
            "material_change must be a finite number between 0 and 1"
        ) from None

    if not math.isfinite(material_change) or not 0 < material_change <= 1:
        raise ValueError("material_change must be a finite number between 0 and 1")

    previous_classification = (previous or {}).get("classification")
    current_classification = (current or {}).get("classification")

    # An absent or empty payload cannot support a like-for-like comparison.
    if not previous or not current:
        return {
            "previous_classification": previous_classification,
            "current_classification": current_classification,
            "previous_dominant_direction": None,
            "current_dominant_direction": None,
            "previous_dominant_share": None,
            "current_dominant_share": None,
            "transition": "insufficient_evidence",
        }

    previous_dominant, previous_share = breadth_dominant_share(previous)
    current_dominant, current_share = breadth_dominant_share(current)

    if (
        previous_dominant is None
        or current_dominant is None
        or previous_share is None
        or current_share is None
    ):
        transition = BreadthTransition.INSUFFICIENT_EVIDENCE

    elif previous_dominant != current_dominant:
        transition = BreadthTransition.COMPOSITION_CHANGED

    else:
        share_change = current_share - previous_share

        if share_change >= material_change - 1e-12:
            transition = BreadthTransition.BROADENED
        elif share_change <= -material_change + 1e-12:
            transition = BreadthTransition.NARROWED
        elif previous_classification != current_classification:
            transition = BreadthTransition.CLASSIFICATION_CHANGED
        else:
            transition = BreadthTransition.UNCHANGED

    return {
        "previous_classification": previous_classification,
        "current_classification": current_classification,
        "previous_dominant_direction": previous_dominant,
        "current_dominant_direction": current_dominant,
        "previous_dominant_share": previous_share,
        "current_dominant_share": current_share,
        "transition": transition,
    }


def compare_direction(
    previous: str | None,
    current: str | None,
) -> DirectionTransition:
    """
    Compare two normalized deterministic directions.

    Assumes signal directions have already been normalized by
    SIGNAL_CONFIG / direction_multiplier.

    This avoids assigning macroeconomic meaning here.
    """

    try:
        previous_direction = Direction(previous)
        current_direction = Direction(current)
    except (TypeError, ValueError):
        return DirectionTransition.INSUFFICIENT_EVIDENCE

    if previous_direction == current_direction:
        if current_direction == Direction.NEUTRAL:
            return DirectionTransition.STABLE_NEUTRAL

        return DirectionTransition.PERSISTENT

    return DIRECTION_TRANSITIONS[(previous_direction, current_direction)]


def extract_direction(
    signal: dict[str, Any],
) -> str | None:
    """Read the normalized direction from a signal payload."""
    return signal.get("direction")


def extract_strength(
    signal: dict[str, Any],
) -> str | None:
    """Read strength from either supported snapshot naming convention."""
    return signal.get("signal_strength") or signal.get("strength")


def extract_score(
    signal: dict[str, Any],
) -> float | None:
    """Read and normalize a score from either supported field name."""
    value = (
        signal.get("signal_score") if "signal_score" in signal else signal.get("score")
    )

    if value is None:
        return None

    try:
        score = float(value)
    except (OverflowError, TypeError, ValueError):
        return None

    return score if math.isfinite(score) else None


def compare_strength(
    previous: str | None,
    current: str | None,
) -> str:
    """Classify a strength transition using the ordered strength scale."""
    try:
        previous_strength = Strength(previous)
        current_strength = Strength(current)
    except (TypeError, ValueError):
        return "insufficient_evidence"

    if previous_strength == current_strength:
        return "unchanged"

    previous_rank = STRENGTH_RANK[previous_strength]
    current_rank = STRENGTH_RANK[current_strength]

    if current_rank > previous_rank:
        return "strengthened"

    return "weakened"


def _compare_signal_fields(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    include_score: bool = False,
) -> dict[str, Any]:
    """Compare the common direction, strength, and optional score fields."""
    previous_direction = extract_direction(previous)
    current_direction = extract_direction(current)
    previous_strength = extract_strength(previous)
    current_strength = extract_strength(current)

    comparison = {
        "previous_direction": previous_direction,
        "current_direction": current_direction,
        "direction_transition": compare_direction(
            previous_direction,
            current_direction,
        ),
        "previous_strength": previous_strength,
        "current_strength": current_strength,
        "strength_transition": compare_strength(
            previous_strength,
            current_strength,
        ),
    }

    if not include_score:
        return comparison

    previous_score = extract_score(previous)
    current_score = extract_score(current)
    score_change = None

    if previous_score is not None and current_score is not None:
        score_change = current_score - previous_score

    return {
        **comparison,
        "previous_score": previous_score,
        "current_score": current_score,
        "score_change": score_change,
    }


def _compare_membership(
    previous_names: set[str],
    current_names: set[str],
) -> tuple[list[str], list[str], list[str]]:
    """Return sorted shared, new, and removed member names."""
    return (
        sorted(previous_names & current_names),
        sorted(current_names - previous_names),
        sorted(previous_names - current_names),
    )


def _is_indicator_payload(value: Any) -> bool:
    """Return whether a value has the expected shape of an indicator metric."""
    return isinstance(value, dict) and bool(value.keys() & INDICATOR_FIELDS)


def _normalize_sector_payload(value: Any, reference: Any) -> dict[str, Any]:
    """Return a sector mapping, preserving reference indicators when malformed."""
    if isinstance(value, dict) and "overall_signal" in value:
        return value

    normalized = {"overall_signal": {}}

    if isinstance(reference, dict):
        normalized.update(
            {
                name: None
                for name, payload in reference.items()
                if _is_indicator_payload(payload)
            }
        )

    return normalized


def _is_sector_payload(value: Any) -> bool:
    """Return whether a value has the reserved aggregate sector entry."""
    return isinstance(value, dict) and "overall_signal" in value


def _is_theme_payload(value: Any) -> bool:
    """Return whether a value has the expected shape of a metrics theme."""
    return isinstance(value, dict) and (
        "overall_breadth" in value
        or any(_is_sector_payload(child) for child in value.values())
    )


def _normalize_theme_payload(value: Any, reference: Any) -> dict[str, Any]:
    """Return a theme mapping, preserving reference sectors when malformed."""
    if _is_theme_payload(value):
        return value

    normalized = {}

    if isinstance(reference, dict):
        if "overall_breadth" in reference:
            normalized["overall_breadth"] = None

        normalized.update(
            {
                name: None
                for name, payload in reference.items()
                if _is_sector_payload(payload)
            }
        )

    return normalized


def compare_indicator(
    indicator: str,
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Build a field-level comparison for one indicator."""
    signal_comparison = _compare_signal_fields(
        previous,
        current,
        include_score=True,
    )

    return {
        "indicator": indicator,
        **signal_comparison,
        "previous_latest_value": previous.get("latest_value"),
        "current_latest_value": current.get("latest_value"),
        "previous_observation_date": previous.get("latest_observation_date"),
        "current_observation_date": current.get("latest_observation_date"),
    }


def compare_sector(
    sector: str,
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare a sector's aggregate signal and its indicator membership."""
    # ``overall_signal`` is the reserved aggregate entry in every sector payload.
    previous_signal = previous.get("overall_signal", {})
    current_signal = current.get("overall_signal", {})

    if not isinstance(previous_signal, dict):
        previous_signal = {}

    if not isinstance(current_signal, dict):
        current_signal = {}

    signal_comparison = _compare_signal_fields(previous_signal, current_signal)

    candidate_indicators = {
        name
        for name in previous.keys() | current.keys()
        if name != "overall_signal"
        and (
            _is_indicator_payload(previous.get(name))
            or _is_indicator_payload(current.get(name))
        )
    }
    previous_indicators = candidate_indicators & previous.keys()
    current_indicators = candidate_indicators & current.keys()

    shared_indicators, new_indicators, removed_indicators = _compare_membership(
        previous_indicators,
        current_indicators,
    )
    indicator_changes = [
        compare_indicator(
            indicator=indicator,
            previous=(
                previous[indicator] if isinstance(previous[indicator], dict) else {}
            ),
            current=current[indicator] if isinstance(current[indicator], dict) else {},
        )
        for indicator in shared_indicators
    ]

    return {
        "sector": sector,
        **signal_comparison,
        "indicator_changes": indicator_changes,
        "new_indicators": new_indicators,
        "removed_indicators": removed_indicators,
    }


def compare_theme(
    theme: str,
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compare breadth and all shared sectors within a macro theme."""

    previous_breadth = previous.get("overall_breadth")
    current_breadth = current.get("overall_breadth")

    breadth_change = compare_breadth(
        previous=previous_breadth if isinstance(previous_breadth, dict) else None,
        current=current_breadth if isinstance(current_breadth, dict) else None,
    )

    # ``overall_signal`` distinguishes a sector payload from other theme-level
    # dictionaries such as ``overall_breadth``.
    candidate_sectors = {
        name
        for name in previous.keys() | current.keys()
        if _is_sector_payload(previous.get(name))
        or _is_sector_payload(current.get(name))
    }
    previous_sectors = candidate_sectors & previous.keys()
    current_sectors = candidate_sectors & current.keys()

    shared_sectors, new_sectors, removed_sectors = _compare_membership(
        previous_sectors,
        current_sectors,
    )
    sector_changes = [
        compare_sector(
            sector=sector,
            previous=_normalize_sector_payload(previous[sector], current[sector]),
            current=_normalize_sector_payload(current[sector], previous[sector]),
        )
        for sector in shared_sectors
    ]

    return {
        "theme": theme,
        "breadth_change": breadth_change,
        "sector_changes": sector_changes,
        "new_sectors": new_sectors,
        "removed_sectors": removed_sectors,
    }


def _describe_breadth_change(
    theme_name: str,
    breadth_change: dict[str, Any],
) -> str | None:
    """Convert one material breadth transition into a concise sentence."""
    transition = breadth_change["transition"]

    if transition == "composition_changed":
        return (
            f"{theme_name}: breadth composition changed from "
            f"{breadth_change['previous_dominant_direction']} to "
            f"{breadth_change['current_dominant_direction']}."
        )

    if transition in {"broadened", "narrowed"}:
        return (
            f"{theme_name}: {breadth_change['current_dominant_direction']} breadth "
            f"{transition} from {breadth_change['previous_dominant_share']:.1%} "
            f"to {breadth_change['current_dominant_share']:.1%}."
        )

    if transition != "classification_changed":
        return None

    previous = breadth_change["previous_classification"]
    current = breadth_change["current_classification"]
    if previous is None and current is None:
        return None
    if previous is None:
        classification_change = f"to {current}"
    elif current is None:
        classification_change = f"from {previous} to unavailable"
    else:
        classification_change = f"from {previous} to {current}"

    return f"{theme_name}: breadth classification changed {classification_change}."


def _append_sector_summaries(
    theme_name: str,
    sector: dict[str, Any],
    summaries: ChangeSummaries,
) -> None:
    """Add material direction and strength summaries for one sector."""
    sector_name = sector["sector"]
    label = f"{theme_name}/{sector_name}"
    direction_transition = sector["direction_transition"]

    if direction_transition in IMPORTANT_DIRECTION_TRANSITIONS:
        summaries["important_changes"].append(f"{label}: {direction_transition}.")
    elif direction_transition == "persistent":
        summaries["persistent_features"].append(
            f"{label}: {sector['current_direction']} signal persisted."
        )

    strength_transition = sector.get("strength_transition")
    if strength_transition in IMPORTANT_STRENGTH_TRANSITIONS:
        summaries["important_changes"].append(
            f"{label}: signal {strength_transition} from "
            f"{sector['previous_strength']} to {sector['current_strength']}."
        )


def _append_indicator_summaries(
    theme_name: str,
    sector_name: str,
    indicator_change: dict[str, Any],
    summaries: ChangeSummaries,
) -> None:
    """Add direction, strength, and score summaries for one indicator."""
    label = f"{theme_name}/{sector_name}/{indicator_change['indicator']}"
    direction_transition = indicator_change["direction_transition"]

    if direction_transition.startswith("reversed_"):
        summaries["reversals"].append(f"{label}: {direction_transition}.")
    elif direction_transition.startswith("emerging_"):
        summaries["emerging_signals"].append(f"{label}: {direction_transition}.")
    elif direction_transition.startswith("faded_"):
        summaries["fading_signals"].append(f"{label}: {direction_transition}.")

    strength_transition = indicator_change.get("strength_transition")
    if strength_transition in IMPORTANT_STRENGTH_TRANSITIONS:
        summaries["important_changes"].append(
            f"{label}: signal {strength_transition} from "
            f"{indicator_change['previous_strength']} to "
            f"{indicator_change['current_strength']}."
        )

    score_change = indicator_change.get("score_change")
    if score_change is not None and abs(score_change) >= MATERIAL_SCORE_CHANGE:
        summaries["important_changes"].append(
            f"{label}: signal score changed from "
            f"{indicator_change['previous_score']} to "
            f"{indicator_change['current_score']}."
        )


def extract_important_changes(themes: list[dict[str, Any]]) -> ChangeSummaries:
    """Flatten detailed comparisons into prompt-ready narrative summaries."""
    summaries: ChangeSummaries = {
        "important_changes": [],
        "persistent_features": [],
        "reversals": [],
        "emerging_signals": [],
        "fading_signals": [],
    }

    for theme in themes:
        theme_name = theme["theme"]
        breadth_summary = _describe_breadth_change(
            theme_name,
            theme["breadth_change"],
        )
        if breadth_summary is not None:
            summaries["important_changes"].append(breadth_summary)

        for sector in theme["sector_changes"]:
            _append_sector_summaries(theme_name, sector, summaries)
            for indicator_change in sector["indicator_changes"]:
                _append_indicator_summaries(
                    theme_name,
                    sector["sector"],
                    indicator_change,
                    summaries,
                )

    return summaries


def compare_metric_snapshots(
    previous_metrics: dict[str, Any],
    current_metrics: dict[str, Any],
    previous_reporting_period: str,
    current_reporting_period: str,
) -> dict[str, Any]:
    """Compare shared themes and report additions/removals at snapshot level."""

    if not isinstance(previous_reporting_period, str) or not previous_reporting_period:
        raise ValueError("previous_reporting_period must be a non-empty string")

    if not isinstance(current_reporting_period, str) or not current_reporting_period:
        raise ValueError("current_reporting_period must be a non-empty string")

    candidate_themes = {
        name
        for name in previous_metrics.keys() | current_metrics.keys()
        if _is_theme_payload(previous_metrics.get(name))
        or _is_theme_payload(current_metrics.get(name))
    }
    previous_themes = candidate_themes & previous_metrics.keys()
    current_themes = candidate_themes & current_metrics.keys()

    shared_themes, new_themes, removed_themes = _compare_membership(
        previous_themes,
        current_themes,
    )
    themes = [
        compare_theme(
            theme=theme,
            previous=_normalize_theme_payload(
                previous_metrics[theme], current_metrics[theme]
            ),
            current=_normalize_theme_payload(
                current_metrics[theme], previous_metrics[theme]
            ),
        )
        for theme in shared_themes
    ]

    summaries = extract_important_changes(themes)

    return {
        "previous_reporting_period": previous_reporting_period,
        "current_reporting_period": current_reporting_period,
        "themes": themes,
        **summaries,
        "new_themes": new_themes,
        "removed_themes": removed_themes,
    }


def calculate_confidence_metrics(state: Any) -> dict[str, Any]:
    """Aggregate the four thematic report confidence classifications.

    The confidence explainer requires a deterministic profile before it can
    produce prose. Each thematic report already contains an authoritative
    ``overall_confidence.level`` classification, so use those classifications
    as the common input rather than asking another model to rescore them.

    The numeric values are policy weights, not probabilities: low confidence
    receives 0.25 because it still represents some usable evidence, medium
    receives 0.60 to sit above the midpoint, and high is the normalized ceiling
    of 1.0. The four themes are weighted equally. An average below 0.50 remains
    low, while 0.80 reserves a high classification for broadly strong thematic
    confidence; intermediate averages are medium. The average is rounded to
    three decimal places to keep the serialized profile stable and concise.
    """

    reports = {
        ThemeName.OUTPUT_DEMAND: state.output_and_demand_report,
        ThemeName.INFLATION: state.inflation_report,
        ThemeName.LABOUR_MARKET: state.labour_market_report,
        ThemeName.MONETARY_POLICY: state.monetary_policy_report,
    }
    theme_confidence_metrics: dict[str, dict[str, Any]] = {}
    scores: list[float] = []

    for theme, report in reports.items():
        try:
            level = Confidence(report.overall_confidence.level)
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(
                f"{theme} report must provide a valid overall confidence level"
            ) from exc

        score = CONFIDENCE_SCORES[level]
        scores.append(score)
        theme_confidence_metrics[theme] = {
            "confidence": level.value,
            "score": score,
        }

    overall_score = round(sum(scores) / len(scores), 3)
    if overall_score >= 0.8:
        overall_confidence = Confidence.HIGH
    elif overall_score >= 0.5:
        overall_confidence = Confidence.MEDIUM
    else:
        overall_confidence = Confidence.LOW

    return {
        "overall_confidence_score": overall_score,
        "overall_confidence": overall_confidence,
        "theme_confidence_metrics": theme_confidence_metrics,
    }
