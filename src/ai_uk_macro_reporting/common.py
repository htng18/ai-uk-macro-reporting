from enum import StrEnum

MAX_REVISION_ITERATIONS = 2

LLM_MODEL_LENGTH_LIMIT_MESSAGE = (
    "The model reached its completion limit before returning "
    "a valid structured report. Increase the relevant "
    "MONTHLY_REPORT_*_MAX_COMPLETION_TOKENS setting or reduce its "
    "reasoning-effort setting, then run the report again."
)

LLM_MODEL_QUOTA_MESSAGE = (
    "OpenAI API quota is unavailable for the project associated with "
    "OPENAI_API_KEY. Check the API billing balance and project usage limits, "
    "then run the report again."
)


class BroadClassification(StrEnum):
    """Describe whether a signal is broad, stable, or mixed."""

    BROAD_POSITIVE = "broad_positive"
    BROAD_NEGATIVE = "broad_negative"
    BROADLY_STABLE = "broadly_stable"
    MIXED = "mixed"


class Direction(StrEnum):
    """Describe the interpreted direction of an economic signal."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class DirectionTransition(StrEnum):
    """Describe how a signal direction changed between periods."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    STABLE_NEUTRAL = "stable_neutral"
    PERSISTENT = "persistent"
    EMERGING_POSITIVE = "emerging_positive"
    EMERGING_NEGATIVE = "emerging_negative"
    FADED_POSITIVE = "faded_positive"
    FADED_NEGATIVE = "faded_negative"
    REVERSED_POSITIVE = "reversed_positive"
    REVERSED_NEGATIVE = "reversed_negative"


class BreadthTransition(StrEnum):
    """Describe how the breadth of a signal changed between periods."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    COMPOSITION_CHANGED = "composition_changed"
    BROADENED = "broadened"
    NARROWED = "narrowed"
    CLASSIFICATION_CHANGED = "classification_changed"
    UNCHANGED = "unchanged"


class Strength(StrEnum):
    """Express the relative strength of an economic signal."""

    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class SignalTransform(StrEnum):
    """Identify the calculation used to transform an indicator series."""

    AS_REPORTED = "as_reported"
    PCT_CHANGE = "pct_change"
    DIFFERENCE = "difference"


class SignalUnit(StrEnum):
    """Identify the unit of a transformed indicator signal."""

    PERCENT = "percent"
    PERCENTAGE_POINT = "percentage_point"
    GBP_MILLION = "GBP_million"


class Confidence(StrEnum):
    """Express confidence in an analytical conclusion."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MacroRegime(StrEnum):
    """Classify the overall macroeconomic configuration."""

    RESILIENT_DISINFLATION = "resilient_disinflation"
    SOFT_LANDING = "soft_landing"
    BROAD_COOLING = "broad_cooling"
    DEMAND_REACCELERATION = "demand_reacceleration"
    INFLATIONARY_REACCELERATION = "inflationary_reacceleration"
    WEAK_GROWTH_STICKY_INFLATION = "weak_growth_sticky_inflation"
    STAGFLATIONARY_PRESSURE = "stagflationary_pressure"
    BALANCED_STABILITY = "balanced_stability"
    MIXED_TRANSITION = "mixed_transition"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class CounterVerdict(StrEnum):
    """Summarise how well a central thesis survives counter-analysis."""

    SURVIVES = "survives"
    SURVIVES_WITH_QUALIFICATIONS = "survives_with_qualifications"
    MATERIALLY_WEAKENED = "materially_weakened"
    SHOULD_BE_REPLACED = "should_be_replaced"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ThemeName(StrEnum):
    """Name a theme referenced in report evaluation."""

    OUTPUT_DEMAND = "output_demand"
    INFLATION = "inflation"
    LABOUR_MARKET = "labour_market"
    MONETARY_POLICY = "monetary_policy"


class Severity(StrEnum):
    """Express the severity of an evaluation issue."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class PublicationVerdict(StrEnum):
    """State whether a report is ready for publication."""

    PASS = "pass"
    PASS_WITH_MINOR_EDITS = "pass_with_minor_edits"
    REVISE = "revise"
    FAIL = "fail"


class EvaluationDimensionName(StrEnum):
    """Name a quality dimension used to evaluate a report."""

    CLASSIFICATION_FIDELITY = "classification_fidelity"
    NUMERICAL_EVIDENCE_FIDELITY = "numerical_evidence_fidelity"
    THEME_SEMANTIC_FIDELITY = "theme_semantic_fidelity"
    CROSS_THEME_CONSISTENCY = "cross_theme_consistency"
    COUNTER_ANALYSIS_INTEGRATION = "counter_analysis_integration"
    OUTLOOK_SCENARIO_DISCIPLINE = "outlook_scenario_discipline"
    CAUSAL_TRANSMISSION_DISCIPLINE = "causal_transmission_discipline"
    UNCERTAINTY_CONFIDENCE_CALIBRATION = "uncertainty_confidence_calibration"
    TIMING_FREQUENCY_ALIGNMENT = "timing_frequency_alignment"
    INTERNAL_CONSISTENCY = "internal_consistency"
    COMPLETENESS_TRUNCATION = "completeness_truncation"
    REPETITION_EDITORIAL_QUALITY = "repetition_editorial_quality"
    ANALYTICAL_DEPTH_READER_ACCESSIBILITY = "analytical_depth_reader_accessibility"
    LENGTH_STYLE = "length_style"


class ScenarioLikelihood(StrEnum):
    """Express the relative likelihood assigned to a scenario."""

    PRIMARY = "primary"
    MEANINGFUL_RISK = "meaningful_risk"
    TAIL_RISK = "tail_risk"


class ScenarioType(StrEnum):
    """Identify a scenario as central, upside, or downside."""

    CENTRAL = "central"
    UPSIDE = "upside"
    DOWNSIDE = "downside"
