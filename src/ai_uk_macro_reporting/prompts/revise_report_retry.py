from .revise_report import revise_report_prompt

revise_report_retry_prompt = revise_report_prompt + [
    (
        "human",
        """
The previous revision produced text that may have been truncated in these
fields:

{truncated_fields}

Regenerate the complete revised report. Rewrite every field listed above
substantially more concisely than before; keep each flagged field below 500
characters. End every sentence and thought cleanly with terminal punctuation.
Preserve all supplied authoritative classifications and all corrections
required by the quality-control evaluation.
""",
    )
]
