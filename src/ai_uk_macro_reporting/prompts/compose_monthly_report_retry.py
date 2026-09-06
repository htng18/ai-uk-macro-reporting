from .compose_monthly_report import compose_monthly_report_prompt

compose_monthly_report_retry_prompt = compose_monthly_report_prompt + [
    (
        "human",
        """
The previous composition produced text that may have been truncated in these
fields:

{truncated_fields}

Regenerate the complete report. Rewrite every field listed above substantially
more concisely than before; keep each flagged field below 500 characters. End
every sentence and thought cleanly with terminal punctuation. Preserve all
supplied authoritative classifications.
""",
    )
]
