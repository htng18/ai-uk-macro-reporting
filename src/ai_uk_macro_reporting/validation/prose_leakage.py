import re
from typing import Any

BANNED_PUBLIC_PROSE_PATTERNS = {
    "confidence terminology": re.compile(r"\bconfidence\b", re.IGNORECASE),
    "cross-theme terminology": re.compile(r"\bcross[\s-]?theme\b", re.IGNORECASE),
    "authoritative terminology": re.compile(r"\bauthoritative\b", re.IGNORECASE),
    "signal strength": re.compile(r"\bsignal strength\b", re.IGNORECASE),
    "signal score": re.compile(r"\bsignal score\b", re.IGNORECASE),
    "breadth score": re.compile(r"\bbreadth score\b", re.IGNORECASE),
    "timing alignment": re.compile(r"\btiming alignment\b", re.IGNORECASE),
    "relationship score": re.compile(r"\brelationship score\b", re.IGNORECASE),
    "correlation stability score": re.compile(
        r"\bcorrelation stability score\b", re.IGNORECASE
    ),
    "classifier": re.compile(r"\bclassifier\b", re.IGNORECASE),
}

PUBLIC_PROSE_STYLE_PATTERNS = {
    "classifier-like neutral wording": re.compile(
        r"\b(?:remains?|is|are|from)\s+(?:weakly\s+)?neutral\b",
        re.IGNORECASE,
    ),
    "internal numerical direction": re.compile(
        r"\b(?:positive|negative)\s+(?:numerical\s+)?"
        r"(?:move|movement|development)s?\b",
        re.IGNORECASE,
    ),
    "technical breadth wording": re.compile(
        r"\b(?:output|activity|demand)\s+breadth\b",
        re.IGNORECASE,
    ),
}


PUBLIC_FORBIDDEN_REGIME_LABELS = {
    "resilient_disinflation",
    "soft_landing",
    "broad_cooling",
    "demand_reacceleration",
    "inflationary_reacceleration",
    "weak_growth_sticky_inflation",
    "stagflationary_pressure",
    "balanced_stability",
    "mixed_transition",
    "insufficient_evidence",
}

STRUCTURED_METADATA_KEYS = {
    "reporting_period",
    "macro_regime",
    "confidence",
    "direction",
    "classification",
    "counter_analysis_verdict",
    "scenario_type",
}


def iter_public_prose(
    value: Any,
    path: tuple[str, ...] = (),
):
    """
    Yield all reader-facing strings while excluding structured
    classifier/metadata fields.

    Returns:
        ("executive_summary.summary", "Some prose...")
    """

    if isinstance(value, dict):
        for key, child in value.items():
            if key in STRUCTURED_METADATA_KEYS:
                continue

            yield from iter_public_prose(
                child,
                path=(*path, key),
            )

    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_public_prose(
                child,
                path=(
                    *path,
                    str(index),
                ),
            )

    elif isinstance(value, str):
        yield ".".join(path), value


def find_public_prose_leakage(
    report: dict,
) -> list[dict]:
    """Return internal terminology found in reader-facing report prose."""
    findings = []

    for path, text in iter_public_prose(report):
        # ==========================================
        # Internal methodological terminology
        # ==========================================

        for (
            issue_type,
            pattern,
        ) in BANNED_PUBLIC_PROSE_PATTERNS.items():
            match = pattern.search(text)

            if not match:
                continue

            findings.append(
                {
                    "field": path,
                    "type": issue_type,
                    "matched_text": (match.group(0)),
                }
            )

        # ==========================================
        # Raw macro-regime identifiers
        # ==========================================

        lower_text = text.lower()

        for regime in PUBLIC_FORBIDDEN_REGIME_LABELS:
            if regime in lower_text:
                findings.append(
                    {
                        "field": path,
                        "type": ("raw regime identifier"),
                        "matched_text": regime,
                    }
                )

    return findings


def find_public_prose_style_warnings(
    report: dict,
) -> list[dict]:
    """Return classifier-like wording that requires contextual editorial review."""
    findings = []

    for path, text in iter_public_prose(report):
        for issue_type, pattern in PUBLIC_PROSE_STYLE_PATTERNS.items():
            match = pattern.search(text)

            if match:
                findings.append(
                    {
                        "field": path,
                        "type": issue_type,
                        "matched_text": match.group(0),
                    }
                )

    return findings
