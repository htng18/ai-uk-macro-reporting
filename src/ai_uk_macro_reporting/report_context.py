"""Build shared metadata, evidence, and prompt inputs for report nodes."""

import json
from typing import Any, TypedDict

from ai_uk_macro_reporting.calculation.metric_definitions import SIGNAL_CONFIG
from ai_uk_macro_reporting.common import (
    Confidence,
    CounterVerdict,
    Direction,
    MacroRegime,
)
from ai_uk_macro_reporting.state import MonthlyReport


class AuthoritativeMetadata(TypedDict):
    """Metadata that generated and revised reports must preserve."""

    reporting_period: str
    regime: MacroRegime
    regime_display_name: str
    verdict: CounterVerdict
    output_direction: str
    inflation_direction: str
    labour_classification: str
    monetary_classification: str
    confidence: Confidence


REGIME_DISPLAY_NAMES = {
    MacroRegime.RESILIENT_DISINFLATION: "modest activity resilience alongside easing inflation pressure",
    MacroRegime.SOFT_LANDING: "a soft-landing configuration",
    MacroRegime.BROAD_COOLING: "broad-based economic cooling",
    MacroRegime.DEMAND_REACCELERATION: "a renewed strengthening in demand",
    MacroRegime.INFLATIONARY_REACCELERATION: "renewed inflationary pressure",
    MacroRegime.WEAK_GROWTH_STICKY_INFLATION: "weak growth alongside persistent inflation pressure",
    MacroRegime.STAGFLATIONARY_PRESSURE: "weak activity combined with persistent inflation pressure",
    MacroRegime.BALANCED_STABILITY: "broad economic stability",
    MacroRegime.MIXED_TRANSITION: "a mixed transitional configuration",
    MacroRegime.INSUFFICIENT_EVIDENCE: "an unclear macroeconomic configuration",
}


def serialize_prompt_data(value: Any) -> str:
    """Serialize prompt data as readable JSON, converting unsupported values."""
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def get_authoritative_metadata(state: MonthlyReport) -> AuthoritativeMetadata:
    """Extract and validate authoritative classifications from report state."""
    regime = MacroRegime(state.cross_theme_report.overall_macro_regime.classification)
    output_signal = state.metrics["output_demand"]["output"]["overall_signal"]

    if not isinstance(output_signal, dict):
        raise TypeError("Output overall signal must be a mapping")

    if output_signal.get("status") == "insufficient_data":
        output_direction = "insufficient_evidence"
    elif output_signal.get("status") == "available":
        output_direction = Direction(output_signal.get("direction")).value
    else:
        raise ValueError(
            "Output overall signal must have status 'available' or 'insufficient_data'"
        )

    return {
        "reporting_period": state.reporting_period.isoformat(),
        "regime": regime,
        "regime_display_name": REGIME_DISPLAY_NAMES[regime],
        "verdict": CounterVerdict(state.counter_analysis_report.verdict.classification),
        "output_direction": output_direction,
        "inflation_direction": (
            state.inflation_report.inflation_pressure_relationship.direction
        ),
        "labour_classification": (
            state.labour_market_report.labour_market_relationship.classification
        ),
        "monetary_classification": (
            state.monetary_policy_report.monetary_policy_relationship.classification
        ),
        "confidence": Confidence(
            state.confidence_profile["metrics"]["overall_confidence"]
        ),
    }


def build_numeric_evidence_packet(
    metrics: dict,
    max_indicators_per_theme: int = 4,
) -> dict:
    """Return the highest-scoring indicator evidence for each metrics theme."""
    evidence = {}

    for theme, theme_data in metrics.items():
        candidates = []

        for sector, sector_data in theme_data.items():
            if sector == "overall_breadth" or not isinstance(sector_data, dict):
                continue

            for indicator, metric in sector_data.items():
                if indicator == "overall_signal" or not isinstance(metric, dict):
                    continue

                signal_score = metric.get("signal_score", 0)
                candidates.append(
                    {
                        "sector": sector,
                        "indicator": indicator,
                        "latest_observation_date": metric.get(
                            "latest_observation_date"
                        ),
                        "latest_value": metric.get("latest_value"),
                        "latest_change": metric.get("latest_signal_change"),
                        "three_month_momentum": metric.get("three_month_momentum"),
                        "signal_unit": metric.get("signal_unit"),
                        "direction": metric.get("direction"),
                        "signal_score": signal_score,
                    }
                )

        candidates.sort(
            key=lambda evidence_item: evidence_item["signal_score"],
            reverse=True,
        )
        selected_candidates = []
        selected_signal_groups = set()

        for candidate in candidates:
            indicator = candidate["indicator"]
            signal_group = SIGNAL_CONFIG.get(indicator, {}).get(
                "signal_group", indicator
            )
            if signal_group in selected_signal_groups:
                continue

            selected_candidates.append(candidate)
            selected_signal_groups.add(signal_group)

            if len(selected_candidates) == max_indicators_per_theme:
                break

        evidence[theme] = selected_candidates

    return evidence


def build_compose_inputs(
    state: MonthlyReport,
    metadata: AuthoritativeMetadata,
) -> dict[str, Any]:
    """Build prompt inputs for composing a monthly report."""
    numeric_evidence = build_numeric_evidence_packet(state.metrics)

    return {
        "reporting_period": state.reporting_period,
        "central_regime": metadata["regime"],
        "regime_display_name": metadata["regime_display_name"],
        "counter_verdict": metadata["verdict"],
        "output_direction": metadata["output_direction"],
        "inflation_direction": metadata["inflation_direction"],
        "labour_classification": metadata["labour_classification"],
        "monetary_classification": metadata["monetary_classification"],
        "overall_confidence": metadata["confidence"],
        "output_demand_report": serialize_prompt_data(state.output_and_demand_report),
        "inflation_report": serialize_prompt_data(state.inflation_report),
        "labour_market_report": serialize_prompt_data(state.labour_market_report),
        "monetary_policy_report": serialize_prompt_data(state.monetary_policy_report),
        "cross_theme_report": serialize_prompt_data(state.cross_theme_report),
        "counter_analysis_report": serialize_prompt_data(state.counter_analysis_report),
        "outlook_scenarios_report": serialize_prompt_data(
            state.outlook_scenarios_report
        ),
        "confidence_profile": serialize_prompt_data(state.confidence_profile),
        "monthly_change_analysis": serialize_prompt_data(state.monthly_change_analysis),
        "numeric_evidence": serialize_prompt_data(numeric_evidence),
    }


def build_revision_inputs(
    state: MonthlyReport,
    metadata: AuthoritativeMetadata,
) -> dict[str, Any]:
    """Build prompt inputs for revising a monthly report."""
    return {
        "reporting_period": state.reporting_period,
        "revision_iteration": state.revision_count + 1,
        "outlook_horizon": "next 3 to 6 months",
        "central_regime": metadata["regime"],
        "counter_verdict": metadata["verdict"],
        "output_direction": metadata["output_direction"],
        "inflation_direction": metadata["inflation_direction"],
        "labour_classification": metadata["labour_classification"],
        "monetary_classification": metadata["monetary_classification"],
        "overall_confidence": metadata["confidence"],
        "output_demand_report": serialize_prompt_data(state.output_and_demand_report),
        "inflation_report": serialize_prompt_data(state.inflation_report),
        "labour_market_report": serialize_prompt_data(state.labour_market_report),
        "monetary_policy_report": serialize_prompt_data(state.monetary_policy_report),
        "cross_theme_report": serialize_prompt_data(state.cross_theme_report),
        "counter_analysis_report": serialize_prompt_data(state.counter_analysis_report),
        "outlook_scenarios_report": serialize_prompt_data(
            state.outlook_scenarios_report
        ),
        "composed_monthly_report": serialize_prompt_data(state.compose_monthly_report),
        "report_evaluation": serialize_prompt_data(state.report_evaluation),
        "confidence_profile": serialize_prompt_data(state.confidence_profile),
        "monthly_change_analysis": serialize_prompt_data(state.monthly_change_analysis),
    }


def build_evaluation_inputs(
    state: MonthlyReport,
    metadata: AuthoritativeMetadata,
) -> dict[str, Any]:
    """Build prompt inputs for evaluating a monthly report."""
    return {
        "reporting_period": state.reporting_period,
        "central_regime": metadata["regime"],
        "counter_verdict": metadata["verdict"],
        "output_direction": metadata["output_direction"],
        "inflation_direction": metadata["inflation_direction"],
        "labour_classification": metadata["labour_classification"],
        "monetary_classification": metadata["monetary_classification"],
        "overall_confidence": metadata["confidence"],
        "output_demand_report": serialize_prompt_data(state.output_and_demand_report),
        "inflation_report": serialize_prompt_data(state.inflation_report),
        "labour_market_report": serialize_prompt_data(state.labour_market_report),
        "monetary_policy_report": serialize_prompt_data(state.monetary_policy_report),
        "cross_theme_report": serialize_prompt_data(state.cross_theme_report),
        "counter_analysis_report": serialize_prompt_data(state.counter_analysis_report),
        "outlook_scenarios_report": serialize_prompt_data(
            state.outlook_scenarios_report
        ),
        "confidence_profile": serialize_prompt_data(state.confidence_profile),
        "monthly_change_analysis": serialize_prompt_data(state.monthly_change_analysis),
        "composed_monthly_report": serialize_prompt_data(state.compose_monthly_report),
        "prose_leakage_issues": serialize_prompt_data(state.prose_leakage_issues),
        "prose_style_warnings": serialize_prompt_data(state.prose_style_warnings),
    }
