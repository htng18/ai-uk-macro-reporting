# Input data specification

Users provide monthly indicator observations in a CSV or JSON file. The
`uk-macro-report` command loads and validates that file before running the
reporting graph, so users do not need to read it with pandas or construct graph
state themselves. This keeps the workflow independent of any particular
database, vendor, or data provider. The CSV examples follow the source export
order: `date`, `value`, and `full_name`. The loader identifies columns by name,
so their order does not affect processing.

## Record structure

Each record represents one monthly observation for one indicator.

| Field | Required | Type | Description |
| --- | --- | --- | --- |
| `full_name` | Yes | String | Exact configured indicator name. Matching is case-sensitive. |
| `date` | Yes | ISO date string | Observation period represented as `YYYY-MM-DD`. Use one consistent monthly date convention. |
| `value` | Yes | Number or null | Raw indicator observation. Do not supply a precomputed monthly change. Null observations are ignored. |

Example record:

```json
{
  "full_name": "Monthly GDP Index",
  "date": "2026-04-01",
  "value": 103.3
}
```

The order of the fields is not significant.

## CSV input

CSV is the recommended format for command-line use because it is easy to
inspect and can be exported by most data tools.

```csv
date,value,full_name
2026-01-01,103.1,Monthly GDP Index
2026-02-01,103.4,Monthly GDP Index
2026-03-01,103.2,Monthly GDP Index
2026-01-01,3.0,CPI Annual Inflation
2026-02-01,2.8,CPI Annual Inflation
2026-03-01,2.7,CPI Annual Inflation
```

Save the data as, for example, `monthly-indicators.csv`, then pass the file
directly to the CLI:

```bash
uv run uk-macro-report --input monthly-indicators.csv
```

## JSON input

The CLI also accepts the same records as a JSON array:

```json
[
  {
    "full_name": "Monthly GDP Index",
    "date": "2026-01-01",
    "value": 103.1
  },
  {
    "full_name": "Monthly GDP Index",
    "date": "2026-02-01",
    "value": 103.4
  },
  {
    "full_name": "CPI Annual Inflation",
    "date": "2026-01-01",
    "value": 3.0
  },
  {
    "full_name": "CPI Annual Inflation",
    "date": "2026-02-01",
    "value": 2.8
  }
]
```

Save the array as, for example, `monthly-indicators.json`, then pass it directly
to the CLI:

```bash
uv run uk-macro-report --input monthly-indicators.json
```

The JSON file may alternatively be an object containing the array under a
`rows` key. The CLI decodes either supported form automatically.

## Data requirements

### Monthly frequency

Provide monthly observations only. Daily, weekly, quarterly, and annual rows
should be converted or filtered before running the CLI. All rows for one
indicator should follow the same date convention, such as the first day of
each observation month.

### Observation history

A history window of up to 60 months is recommended, although the calculation
function does not impose a maximum.

- At least **two non-null observations** are the current implementation requires at least two non-null observations for every indicator.
- At least **four raw observations** are recommended for a full three-change
  momentum window.
- At least **seven raw observations** are recommended for a full six-change
  trend window.
- At least **thirteen raw observations** are recommended for a full
  twelve-change volatility window.
- Up to **60 months** provides useful recent history without requiring a large
  input file.

An indicator with fewer than two usable observations is omitted from the
calculated snapshot. The graph can still run when some configured indicators
are unavailable, but missing coverage may reduce the quality and confidence of
the report.

### Indicator names

`full_name` must exactly match a name in
`calculation/metric_definitions.py`. For example:

```text
Monthly GDP Index
CPI Annual Inflation
Unemployment Rate
Bank Rate
UK 10-Year Gilt Yield
```

Do not substitute abbreviations, change capitalization, add whitespace, or add
source names to these values. The CLI rejects unrecognized names. The
[indicator guide](indicators.md) explains every supported name, theme,
transformation, unit, and signal orientation.

If an exported file intentionally contains additional series, pass
`--ignore-unknown-indicators`. The CLI will log their names and row count, then
run the report using only configured indicators. Strict rejection remains the
default so misspellings and unexpected source changes are not hidden.

```bash
uv run uk-macro-report \
  --input data/input_data_202608.csv \
  --ignore-unknown-indicators
```

### Values

Supply the published observation level or rate expected by the indicator
definition:

- Index series should contain index levels.
- Inflation, interest-rate, yield, and growth-rate series should contain their
  published percentage values, such as `3.5` for 3.5%, unless the indicator
  guide states otherwise.
- Lending and finance flow series configured as `GBP_million` should contain
  values in millions of pounds.

The calculation layer applies the configured percentage-change or difference
transformation. Do not calculate those changes before supplying the data.

## Data-quality rules

The CLI automatically checks that:

1. All three required columns are present.
2. Every `full_name` is non-empty and either exactly matches a configured name
   or is explicitly skipped with `--ignore-unknown-indicators`.
3. Every `date` is a valid calendar date written exactly as `YYYY-MM-DD`.
4. Every `value` is numeric or null.
5. Duplicate `full_name` and `date` records do not contain conflicting values.

Exact duplicates are collapsed, and null values are excluded from an
indicator's calculation. Users remain responsible for ensuring that rows
represent monthly observations, use the intended observation-month convention,
and do not mix frequencies.

Rows do not have to be sorted. The calculation layer sorts each indicator by
`date`, but using ISO-formatted dates is important when dates arrive as text.

## Preparing data from an existing database

Database users can retain their own query and export its `full_name`, `date`,
and `value` columns to CSV or JSON. Pass the exported file to
`uk-macro-report --input`; no conversion to Python row dictionaries or graph
state is required.

Database credentials, connection code, table definitions, and provider-specific
queries should remain in the consuming application rather than in this public
reporting package.

## Data sources and licensing

This repository defines a reporting and analysis workflow; it does not bundle
economic observations or grant permission to redistribute third-party data.
Users are responsible for:

- obtaining data from sources they are permitted to use;
- complying with the source's licence and attribution requirements;
- checking revisions, seasonal-adjustment status, units, and release dates;
- confirming that differently sourced series are conceptually compatible with
  the configured indicator definitions.

Example values in this document are synthetic and are provided only to
illustrate the input format.
