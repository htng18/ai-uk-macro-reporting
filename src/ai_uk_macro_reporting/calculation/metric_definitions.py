from ai_uk_macro_reporting.common import SignalTransform, SignalUnit, ThemeName

THEME_INDICATORS_MAP = {
    ThemeName.OUTPUT_DEMAND: {
        "output": [
            "Monthly GDP Index",
            "Monthly GDP Growth Rate",
            "Services output index",
            "Services output monthly growth",
            "Production output index",
            "Production output monthly growth",
            "Manufacturing output index",
            "Manufacturing output monthly growth",
            "Construction output index",
            "Construction output monthly growth",
        ],
        "household_demand": [
            "Retail sales volume index",
            "Retail sales value index",
            "Net Consumer Credit Lending",
        ],
        "housing_demand": [
            "Mortgage Approvals for House Purchases",
            "Net mortgage lending",
            "UK House Price Index",
        ],
        "business_demand": [
            "PNFC net finance raised",
        ],
    },
    ThemeName.INFLATION: {
        "headline_underlying": [
            "CPI Annual Inflation",
            "Core CPI Inflation",
            "Monthly Consumer Price Index Rate",
        ],
        "inflation_composition": [
            "CPI Services Inflation",
            "CPI Goods Inflation",
            "CPI Food Inflation",
            "CPI Energy Inflation",
        ],
        "pipeline_pressure": [
            "PPI Input Prices",
            "Producer Price Input Index",
            "PPI Output Prices",
            "Producer Price Output Index",
        ],
        "inflation_expectations": [
            "DMP 1-Year CPI Expectation",
            "DMP 3-Year CPI Expectation",
            "DMP 1-Year Own-Price Expectation",
        ],
    },
    ThemeName.LABOUR_MARKET: {
        "employment_conditions": [
            "Employment Rate",
            "Unemployment Rate",
            "Economic Inactivity Rate",
        ],
        "labour_demand": [
            "UK Vacancies",
            "Job Vacancies",
        ],
        "wage_pressure": [
            "Regular Pay Growth",
            "Total Pay Growth",
        ],
        "labour_expectations": [
            "DMP 1-Year Wage Growth Expectation",
            "DMP 1-Year Employment Growth Expectation",
        ],
    },
    ThemeName.MONETARY_POLICY: {
        "policy_conditions": [
            "Bank Rate",
            "SONIA",
        ],
        "market_rates": [
            "UK 5-Year Gilt Yield",
            "UK 10-Year Gilt Yield",
        ],
        "money_credit_conditions": [
            "M4 12-Month Growth",
            "M4 Lending 12-Month Growth",
            "UK M4 Money Supply",
            "UK EMU M3 Money Supply",
            "UK EMU M2 Money Supply",
        ],
    },
}

BREADTH_COMPONENTS = {
    ThemeName.OUTPUT_DEMAND: [
        "Services output index",
        "Services output monthly growth",
        "Production output index",
        "Production output monthly growth",
        "Construction output index",
        "Construction output monthly growth",
    ],
    ThemeName.INFLATION: [
        "CPI Services Inflation",
        "CPI Goods Inflation",
        "PPI Input Prices",
        "Producer Price Input Index",
        "PPI Output Prices",
        "Producer Price Output Index",
        "DMP 1-Year CPI Expectation",
        "DMP 3-Year CPI Expectation",
        "DMP 1-Year Own-Price Expectation",
    ],
    ThemeName.LABOUR_MARKET: [
        "UK Vacancies",
        "Job Vacancies",
        "Regular Pay Growth",
        "DMP 1-Year Employment Growth Expectation",
    ],
    ThemeName.MONETARY_POLICY: {
        "Bank Rate",
        "UK 5-Year Gilt Yield",
        "M4 12-Month Growth",
        "M4 Lending 12-Month Growth",
    },
}


SIGNAL_CONFIG = {
    # Index / level series -> percentage change in percentage terms.
    "Monthly GDP Index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "monthly_gdp",
    },
    "Monthly GDP Growth Rate": {
        "transform": SignalTransform.AS_REPORTED,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "monthly_gdp",
    },
    "Services output index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "services_output",
    },
    "Services output monthly growth": {
        "transform": SignalTransform.AS_REPORTED,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "services_output",
    },
    "Production output index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "production_output",
    },
    "Production output monthly growth": {
        "transform": SignalTransform.AS_REPORTED,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "production_output",
    },
    "Manufacturing output index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "manufacturing_output",
    },
    "Manufacturing output monthly growth": {
        "transform": SignalTransform.AS_REPORTED,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "manufacturing_output",
    },
    "Construction output index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "construction_output",
    },
    "Construction output monthly growth": {
        "transform": SignalTransform.AS_REPORTED,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "construction_output",
    },
    "Retail sales volume index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
    },
    "Retail sales value index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
    },
    "Mortgage Approvals for House Purchases": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
    },
    "UK House Price Index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
    },
    # Flow series -> absolute change in the source series' native unit.
    "Net mortgage lending": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.GBP_MILLION,
        "direction_multiplier": 1,
    },
    "Net Consumer Credit Lending": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.GBP_MILLION,
        "direction_multiplier": 1,
    },
    "PNFC net finance raised": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.GBP_MILLION,
        "direction_multiplier": 1,
    },
    "CPI Annual Inflation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "Core CPI Inflation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "Monthly Consumer Price Index Rate": {
        "transform": SignalTransform.AS_REPORTED,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
    },
    "CPI Services Inflation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "CPI Goods Inflation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "CPI Food Inflation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "CPI Energy Inflation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "PPI Output Prices": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "producer_output_prices",
    },
    "Producer Price Output Index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "producer_output_prices",
    },
    "PPI Input Prices": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "producer_input_prices",
    },
    "Producer Price Input Index": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "producer_input_prices",
    },
    "DMP 1-Year CPI Expectation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "DMP 3-Year CPI Expectation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "DMP 1-Year Own-Price Expectation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "Employment Rate": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "Unemployment Rate": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": -1,
    },
    "Economic Inactivity Rate": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": -1,
    },
    "UK Vacancies": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "uk_vacancies",
    },
    "Job Vacancies": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": 1,
        "signal_group": "uk_vacancies",
    },
    "Regular Pay Growth": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "Total Pay Growth": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "DMP 1-Year Wage Growth Expectation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "DMP 1-Year Employment Growth Expectation": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    # ============================================================
    # Policy rates
    # Interest rates -> change in percentage points
    # Higher rates = tighter conditions
    # ============================================================
    "Bank Rate": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "SONIA": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    # ============================================================
    # Government bond yields
    # Yields -> change in percentage points
    # Higher yields = tighter market financial conditions
    # ============================================================
    "UK 5-Year Gilt Yield": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    "UK 10-Year Gilt Yield": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": 1,
    },
    # ============================================================
    # Money / credit growth
    # These series are already annual percentage growth rates.
    #
    # Therefore use difference, NOT pct_change.
    #
    # Faster money/credit growth = looser conditions,
    # so reverse the sign to maintain:
    # positive = tightening
    # ============================================================
    "M4 12-Month Growth": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": -1,
    },
    "M4 Lending 12-Month Growth": {
        "transform": SignalTransform.DIFFERENCE,
        "unit": SignalUnit.PERCENTAGE_POINT,
        "direction_multiplier": -1,
    },
    "UK M4 Money Supply": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": -1,
        "signal_group": "broad_money_levels",
    },
    "UK EMU M3 Money Supply": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": -1,
        "signal_group": "broad_money_levels",
    },
    "UK EMU M2 Money Supply": {
        "transform": SignalTransform.PCT_CHANGE,
        "unit": SignalUnit.PERCENT,
        "direction_multiplier": -1,
        "signal_group": "broad_money_levels",
    },
}
