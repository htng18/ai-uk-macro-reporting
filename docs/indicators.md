# Indicator guide

This guide describes the 49 monthly indicators recognized by **AI UK Macro
Reporting**. It explains why each indicator is included, what users should
provide in the `value` field, and how the project converts the observations
into monthly signals.

The indicator names in this document must match the `full_name` values in the
input data exactly. See [Input data specification](input-data.md) for the full
record structure.

## Scope of this guide

The project deliberately does not prescribe database tables, API endpoints, or
provider-specific series identifiers. Users are responsible for selecting a
series whose definition, frequency, seasonal adjustment, units, and geographic
coverage match the description below.

Where an indicator can be constructed in more than one reasonable way—such as
core CPI, energy inflation, gilt yields, or M4—the consuming application should
record the exact series identifier and methodology it uses.

## How signals are calculated

The calculation layer uses one of three transformations:

| Transformation | Calculation | Typical input |
| --- | --- | --- |
| As reported | `current` | Already-calculated monthly growth or inflation rate |
| Percentage change | `(current / previous - 1) * 100` | Index, count, or level |
| Difference | `current - previous` | Percentage rate or monthly flow |

For percentage rates, supply percentage values rather than decimal fractions.
For example, provide `3.75` for a rate of 3.75%, not `0.0375`.

The transformed change is then multiplied by the configured direction
multiplier. The meaning of a positive signal depends on the theme:

| Theme | Meaning of a positive configured signal |
| --- | --- |
| Output and demand | Stronger activity or demand |
| Inflation | Greater inflation pressure |
| Labour market | Firmer employment conditions or wage pressure |
| Monetary policy | Tighter monetary or financial conditions |

This is why unemployment, economic inactivity, M4 growth, and M4 lending growth
have reversed signs in the current configuration.

## Output and demand

These indicators describe changes in aggregate output and the strength of
household, housing, and business demand. UK GDP measures the value of goods and
services produced, while the output indices provide more detailed views of
services, production, manufacturing, and construction.

### Output

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `Monthly GDP Index` | A monthly volume index of total economic output, used as the broadest timely measure of UK activity. | Seasonally adjusted index level | Percentage change |
| `Monthly GDP Growth Rate` | The already-calculated monthly growth rate of total economic output. | Monthly growth rate in percent | As reported |
| `Services output index` | Measures changes in the volume of output produced by service industries, the largest part of the UK economy. | Seasonally adjusted index level | Percentage change |
| `Services output monthly growth` | The already-calculated monthly growth rate of services output. | Monthly growth rate in percent | As reported |
| `Production output index` | Measures output from production industries, including manufacturing, mining and quarrying, energy supply, and water and waste activities. | Seasonally adjusted index level | Percentage change |
| `Production output monthly growth` | The already-calculated monthly growth rate of production output. | Monthly growth rate in percent | As reported |
| `Manufacturing output index` | Measures the volume of output produced by manufacturing industries and is a component of the broader production index. | Seasonally adjusted index level | Percentage change |
| `Manufacturing output monthly growth` | The already-calculated monthly growth rate of manufacturing output. | Monthly growth rate in percent | As reported |
| `Construction output index` | Measures changes in the volume of construction work, covering new work and repair and maintenance. Check the geographic coverage of the selected series. | Seasonally adjusted index level | Percentage change |
| `Construction output monthly growth` | The already-calculated monthly growth rate of construction output. | Monthly growth rate in percent | As reported |

When both an output index and its corresponding monthly-growth series are
present, both metrics remain available for analysis but count as one underlying
signal in the output aggregate and theme breadth.

### Household demand

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `Retail sales volume index` | Measures the quantity of retail goods purchased after removing the effect of price changes. | Seasonally adjusted volume index | Percentage change |
| `Retail sales value index` | Measures the amount spent on retail goods at current prices, so it reflects both quantities and prices. | Seasonally adjusted value index | Percentage change |
| `Net Consumer Credit Lending` | The monthly net flow of consumer credit to individuals, generally including credit-card lending and other unsecured borrowing. Negative values indicate net repayment. | Monthly net flow in GBP millions | Difference in GBP millions |

### Housing demand

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `Mortgage Approvals for House Purchases` | The number of mortgages approved for purchasing homes. It is a forward-looking indicator because approval usually precedes completed borrowing and property transactions. | Monthly approval count or consistently scaled count | Percentage change |
| `Net mortgage lending` | The monthly net flow of lending secured on dwellings, after repayments. Negative values indicate net repayment. | Monthly net flow in GBP millions | Difference in GBP millions |
| `UK House Price Index` | A monthly index of UK residential property prices. Confirm the provider's geography, mix adjustment, and seasonal-adjustment basis. | House-price index level | Percentage change |

### Business demand

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `PNFC net finance raised` | Net finance raised by private non-financial corporations through the financial instruments covered by the selected source, such as bank borrowing and capital-market issuance. | Monthly net flow in GBP millions | Difference in GBP millions |

`PNFC` means **private non-financial corporation**. Because different data
tables may include different combinations of loans, bonds, commercial paper,
and equity, document the exact aggregate used.

## Inflation

These indicators distinguish headline inflation, underlying pressure,
inflation composition, producer-price pressure, and businesses' expectations.
Consumer price inflation measures changes in the prices of goods and services
purchased by households.

### Headline and underlying inflation

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `CPI Annual Inflation` | The 12-month percentage change in the Consumer Prices Index (CPI), representing headline consumer price inflation. | Annual inflation rate in percent | Difference in percentage points |
| `Core CPI Inflation` | An underlying inflation measure that normally excludes energy, food, alcoholic beverages, and tobacco from CPI. Verify the exclusions used by the selected series. | Annual inflation rate in percent | Difference in percentage points |
| `Monthly Consumer Price Index Rate` | The already-calculated one-month rate of change in consumer prices. | Monthly inflation rate in percent | As reported |

### Inflation composition

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `CPI Services Inflation` | The annual inflation rate for service components of CPI. It is often examined for evidence of domestically generated and persistent price pressure. | Annual inflation rate in percent | Difference in percentage points |
| `CPI Goods Inflation` | The annual inflation rate for goods components of CPI, which can be sensitive to import prices, exchange rates, energy, and global supply conditions. | Annual inflation rate in percent | Difference in percentage points |
| `CPI Food Inflation` | The annual inflation rate for the selected food component of CPI. State whether the series includes non-alcoholic beverages. | Annual inflation rate in percent | Difference in percentage points |
| `CPI Energy Inflation` | The annual inflation rate for the selected energy-related CPI component. Document which items, such as electricity, gas, and other fuels, are included. | Annual inflation rate in percent | Difference in percentage points |

### Pipeline pressure

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `PPI Input Prices` | Measures prices paid by UK manufacturers for materials and fuels used in production. It can indicate upstream cost pressure before it reaches consumers. | Producer input price index level | Percentage change |
| `Producer Price Input Index` | An alternate producer input-price index series. Verify its coverage and base period against other PPI inputs. | Producer input price index level | Percentage change |
| `PPI Output Prices` | Measures prices charged by UK manufacturers when goods leave the factory, often called factory-gate prices. | Producer output price index level | Percentage change |
| `Producer Price Output Index` | An alternate producer output-price index series. Verify its coverage and base period against other PPI outputs. | Producer output price index level | Percentage change |

The current project configuration expects PPI **index levels**. Do not provide
an already calculated annual PPI inflation rate unless the signal configuration
is changed accordingly.

### Inflation expectations

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `DMP 1-Year CPI Expectation` | UK businesses' expectation for CPI inflation one year ahead, collected through the Decision Maker Panel (DMP). | Expected inflation rate in percent | Difference in percentage points |
| `DMP 3-Year CPI Expectation` | UK businesses' expectation for CPI inflation three years ahead, providing a view of medium-term inflation expectations. | Expected inflation rate in percent | Difference in percentage points |
| `DMP 1-Year Own-Price Expectation` | The price growth that businesses expect for their own products or services over the next year. This is distinct from their expectation for economy-wide CPI inflation. | Expected annual own-price growth in percent | Difference in percentage points |

The DMP is a survey of chief financial officers from small, medium, and large
UK businesses. Survey estimates may be published as weighted rolling averages;
use one consistent published measure throughout the input history.

## Labour market

These indicators cover participation, employment, labour demand, wage growth,
and businesses' expectations. Together they help distinguish a firm labour
market from one that is losing momentum.

### Employment conditions

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `Employment Rate` | The proportion of people aged 16 to 64 who are in paid work or temporarily away from a job. | Rate in percent | Difference in percentage points |
| `Unemployment Rate` | The proportion of the economically active population who are without work, have recently sought work, and are available to start. | Rate in percent | Difference in percentage points, sign reversed |
| `Economic Inactivity Rate` | The proportion of people aged 16 to 64 who are outside the labour force because they are neither employed nor classified as unemployed. | Rate in percent | Difference in percentage points, sign reversed |

The signs of unemployment and inactivity are reversed so that a fall in either
rate contributes positively to the project's labour-market signal. This is an
analytical orientation, not a claim that every change in inactivity has the
same economic cause.

### Labour demand

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `UK Vacancies` | The estimated stock of positions for which employers are actively seeking recruits from outside their organizations. | Vacancy count or consistently scaled count | Percentage change |
| `Job Vacancies` | An alternate vacancy-count series representing positions employers are seeking to fill. Verify its coverage against `UK Vacancies`. | Vacancy count or consistently scaled count | Percentage change |

`UK Vacancies` and `Job Vacancies` remain visible when both are supplied but
count as one underlying signal in the labour-demand aggregate and breadth.

### Wage pressure

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `Regular Pay Growth` | Annual growth in employees' average earnings excluding bonuses. It provides a less volatile measure of underlying wage pressure. | Annual growth rate in percent | Difference in percentage points |
| `Total Pay Growth` | Annual growth in employees' average earnings including bonuses. It may be more volatile than regular pay growth. | Annual growth rate in percent | Difference in percentage points |

### Labour expectations

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `DMP 1-Year Wage Growth Expectation` | The wage growth businesses expect for their employees over the next year. | Expected annual growth rate in percent | Difference in percentage points |
| `DMP 1-Year Employment Growth Expectation` | The change in employment businesses expect within their own organizations over the next year. | Expected annual growth rate in percent | Difference in percentage points |

## Monetary policy and financial conditions

These indicators combine the policy rate, overnight money-market conditions,
government bond yields, broad money, and bank lending. In this theme, a
positive configured signal means **tighter** conditions.

### Policy conditions

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `Bank Rate` | The official interest rate set by the Bank of England's Monetary Policy Committee. It influences short-term market rates and borrowing costs across the economy. | Rate in percent | Difference in percentage points |
| `SONIA` | The Sterling Overnight Index Average, based on actual transactions and reflecting the average interest rate paid to borrow sterling overnight in wholesale markets. | Rate in percent | Difference in percentage points |

### Market rates

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `UK 5-Year Gilt Yield` | A representative five-year nominal yield on UK government debt, reflecting expected policy rates, inflation compensation, and term premia over a medium horizon. | Yield in percent | Difference in percentage points |
| `UK 10-Year Gilt Yield` | A representative ten-year nominal yield on UK government debt, widely used as a longer-term benchmark for financing conditions. | Yield in percent | Difference in percentage points |

State whether the chosen gilt series is a conventional bond yield, par yield,
spot rate, or zero-coupon yield. Use the same methodology across the complete
history.

### Money and credit conditions

| Indicator | Brief description | Expected input | Signal calculation |
| --- | --- | --- | --- |
| `M4 12-Month Growth` | The annual growth rate of the selected M4 broad-money aggregate, which captures sterling money holdings of the relevant UK private-sector groups. | Annual growth rate in percent | Difference in percentage points, sign reversed |
| `M4 Lending 12-Month Growth` | The annual growth rate of lending corresponding to the selected M4 measure, representing credit supplied by monetary financial institutions to the covered private-sector groups. | Annual growth rate in percent | Difference in percentage points, sign reversed |
| `UK M4 Money Supply` | The level of the selected UK M4 broad-money aggregate. | Money-supply level in a consistent unit | Percentage change, sign reversed |
| `UK EMU M3 Money Supply` | A provider-labelled M3 money-supply level. Verify that its geographic coverage is appropriate for the UK analysis. | Money-supply level in a consistent unit | Percentage change, sign reversed |
| `UK EMU M2 Money Supply` | A provider-labelled M2 money-supply level. Verify that its geographic coverage is appropriate for the UK analysis. | Money-supply level in a consistent unit | Percentage change, sign reversed |

The signs of the M4 growth and money-supply indicators are reversed because
faster money or credit growth is treated as looser—not tighter—financial
conditions. M2, M3, and M4 levels overlap conceptually; when several are
present, they remain visible but count as one underlying broad-money-level
signal in the sector aggregate. Specify whether the selected aggregates exclude
intermediate other financial corporations, because the Bank of England
publishes more than one M4-related measure.

## Interpretation limitations

- The indicators are analytical inputs, not forecasts by themselves.
- A positive signal does not always mean a socially or economically desirable
  outcome. For example, higher inflation is positive only in the sense of
  greater inflation pressure.
- Monthly data can be revised, noisy, or published with different reference
  periods. Preserve release metadata separately if real-time analysis matters.
- Similar series from different providers may differ in seasonal adjustment,
  population, geography, aggregation, or revision policy.
- The project configuration determines transformations and sign orientation;
  the source provider does not endorse those analytical choices.

## Official reference sources

The descriptions above are based on general definitions published by the UK
Office for National Statistics and the Bank of England:

- [ONS: Gross Domestic Product](https://www.ons.gov.uk/economy/grossdomesticproductgdp)
- [ONS: Understanding the UK economy](https://www.ons.gov.uk/economy/nationalaccounts/articles/dashboardunderstandingtheukeconomy/2017-02-22)
- [ONS: Consumer Price Inflation quality and methodology information](https://www.ons.gov.uk/economy/inflationandpriceindices/methodologies/consumerpriceinflationincludesall3indicescpihcpiandrpiqmi)
- [ONS: Producer Price Index definitions](https://www.ons.gov.uk/economy/inflationandpriceindices/articles/additionalanalysisoftheproducerpriceindexppiandconsumerpriceindexcpi/focusontheeffectsofchangesinthesterlingexchangerate)
- [ONS: Guide to labour-market statistics](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/aguidetolabourmarketstatistics)
- [Bank of England: Decision Maker Panel](https://www.bankofengland.co.uk/decision-maker-panel/2026/july-2026)
- [Bank of England: SONIA benchmark](https://www.bankofengland.co.uk/markets/sonia-benchmark)
- [Bank of England: Money and credit statistics](https://www.bankofengland.co.uk/statistics/visual-summaries/money-and-credit-statistics)
- [Bank of England: Further details about M4](https://www.bankofengland.co.uk/statistics/details/further-details-about-m4-data)

These links explain the broad concepts. They do not select a particular series
on behalf of the user. Record the precise series identifiers used by the
consuming application so that the report can be reproduced.

## Data-source and licensing disclaimer

The data sources mentioned in this guide are provided for reference only. They illustrate the types of series that may be suitable for each indicator and do not constitute an endorsement, licence, or grant of permission to access, use, reproduce, or redistribute the data.

Users are responsible for verifying the relevant institution’s current terms of use, data licence, attribution requirements, and any restrictions applying to their intended use. Permission from the data provider may be required. This project does not include third-party economic data or grant rights to use it.
