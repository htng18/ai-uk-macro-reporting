from ai_uk_macro_reporting.validation.truncation import trim_incomplete_trailing_prose


def test_trim_ignores_dotted_initialism_within_sentence():
    text = "Conditions were stable. The U.K. economy weakened because"

    assert trim_incomplete_trailing_prose(text) == "Conditions were stable."


def test_trim_recognizes_sentence_ending_before_closing_quote():
    text = (
        "The assessment concluded: \u201cGrowth improved.\u201d Demand weakened because"
    )

    assert trim_incomplete_trailing_prose(text) == (
        "The assessment concluded: \u201cGrowth improved.\u201d"
    )
