"""Backward-compatible entry point for running the project from source."""

from ai_uk_macro_reporting.cli import generate_report, load_rows, main

__all__ = ["generate_report", "load_rows", "main"]


if __name__ == "__main__":
    main()
