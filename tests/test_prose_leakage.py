"""Tests for hard public-prose leakage and contextual style warnings."""

import pytest

from ai_uk_macro_reporting.validation.prose_leakage import (
    find_public_prose_leakage,
    find_public_prose_style_warnings,
)


@pytest.mark.parametrize(
    ("text", "issue_type", "matched_text"),
    [
        (
            "Demand remains weakly neutral despite volatile monthly readings.",
            "classifier-like neutral wording",
            "remains weakly neutral",
        ),
        (
            "This was a negative numerical movement.",
            "internal numerical direction",
            "negative numerical movement",
        ),
        (
            "Output breadth was narrow across the latest releases.",
            "technical breadth wording",
            "Output breadth",
        ),
    ],
)
def test_style_detector_flags_classifier_like_phrases(
    text,
    issue_type,
    matched_text,
):
    report = {"executive_summary": {"summary": text}}

    assert find_public_prose_style_warnings(report) == [
        {
            "field": "executive_summary.summary",
            "type": issue_type,
            "matched_text": matched_text,
        }
    ]
    assert find_public_prose_leakage(report) == []


@pytest.mark.parametrize(
    "text",
    [
        "The neutral interest rate remains unusually uncertain.",
        "Market breadth improved as more asset classes advanced.",
        "Price pressures were broadly neutral over the month.",
    ],
)
def test_style_detector_allows_legitimate_neutral_and_breadth_language(text):
    assert find_public_prose_style_warnings({"summary": text}) == []
    assert find_public_prose_leakage({"summary": text}) == []


def test_style_detector_excludes_structured_metadata_fields():
    report = {
        "direction": "remains neutral",
        "classification": "negative movement",
        "summary": "Demand growth was unchanged over the month.",
    }

    assert find_public_prose_style_warnings(report) == []
