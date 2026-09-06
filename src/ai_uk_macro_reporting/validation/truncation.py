import re

SUSPICIOUS_TRAILING_WORDS = frozenset(
    {
        # Conjunctions and subordinators
        "although",
        "and",
        "because",
        "but",
        "if",
        "nor",
        "or",
        "than",
        "though",
        "unless",
        "whereas",
        "while",
        "yet",
        # Prepositions
        "at",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "onto",
        "over",
        "to",
        "under",
        "with",
        "without",
        # Determiners and auxiliary verbs
        "a",
        "an",
        "the",
        "can",
        "could",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "will",
        "would",
    }
)

SENTENCE_ENDING_PATTERN = re.compile(r"[.!?][\"'\u2019\u201d)\]]*(?=\s|$)")
DOTTED_INITIALISM_PATTERN = re.compile(r"(?:\b[A-Za-z]\.){2,}$")


def _is_sentence_ending(text: str, match: re.Match[str]) -> bool:
    """Return whether matched punctuation ends a sentence, excluding initialisms."""
    if text[match.start()] != ".":
        return True

    preceding_text = text[: match.start() + 1]
    following_text = text[match.end() :].lstrip()

    return not (
        following_text
        and following_text[0].islower()
        and DOTTED_INITIALISM_PATTERN.search(preceding_text)
    )


def looks_truncated(text: str) -> bool:
    """Return whether text appears to end with an incomplete sentence or word."""
    text = text.strip()

    if not text:
        return False

    lowered = text.lower()

    trailing_word = re.search(r"\b([a-z]+)$", lowered)

    if trailing_word and trailing_word.group(1) in SUSPICIOUS_TRAILING_WORDS:
        return True

    if text.endswith((",", ":", ";")):
        return True

    # ---------------------------------------------
    # Long prose normally should end as a sentence
    # ---------------------------------------------
    if len(text) >= 120 and not re.search(r"[.!?][\"'\u2019\u201d)\]]*$", text):
        return True

    # ---------------------------------------------
    # Catch obvious chopped last words
    # e.g. "...the ca"
    # ---------------------------------------------
    match = re.search(r"\b([A-Za-z]+)$", text)

    if match:
        last_word = match.group(1)

        if len(last_word) <= 2:
            return True

    return False


def find_truncated_strings(
    value,
    path: str = "report",
) -> list[str]:
    """Return paths to strings that appear truncated within a nested value."""
    problems = []

    if isinstance(value, str):
        if looks_truncated(value):
            problems.append(path)

    elif isinstance(value, dict):
        for key, item in value.items():
            problems.extend(
                find_truncated_strings(
                    item,
                    f"{path}.{key}",
                )
            )

    elif isinstance(value, list):
        for index, item in enumerate(value):
            problems.extend(
                find_truncated_strings(
                    item,
                    f"{path}[{index}]",
                )
            )

    return problems


def trim_incomplete_trailing_prose(value):
    """Recursively trim suspected trailing fragments after the last complete sentence."""
    if isinstance(value, str):
        if not looks_truncated(value):
            return value

        sentence_endings = [
            match
            for match in SENTENCE_ENDING_PATTERN.finditer(value)
            if _is_sentence_ending(value, match)
        ]
        if sentence_endings:
            return value[: sentence_endings[-1].end()].rstrip()

        return value

    if isinstance(value, dict):
        return {
            key: trim_incomplete_trailing_prose(item) for key, item in value.items()
        }

    if isinstance(value, list):
        return [trim_incomplete_trailing_prose(item) for item in value]

    return value
