# Online Retail Project Report

## Objective

Analyze retail revenue, returns and seasonal patterns across December 2009–December 2011 using the complete Online Retail II dataset.

## Data and Method

Source: Chen, D. (2012), Online Retail II, UCI, https://doi.org/10.24432/C5CG6D, CC BY 4.0.

The two original sheets contain 1,067,371 transaction rows. Eight-field normalized deduplication produces 1,033,036 unique raw rows. Filtering invalid/fee/manual rows and enforcing fact eligibility produces 1,031,644 sales facts. Negative quantities are retained as returns; unidentified customers remain NULL. Amounts are GBP, stored to four decimal places.

## Results

Net revenue is GBP 19,097,536.1680. Q4 daily net revenue exceeds non-Q4 daily net revenue by GBP 18,959.40 in the exploratory Welch comparison (95% CI approximately GBP 15,774.60–22,144.19; p approximately 1.38e-24). The return-rate comparison does not show a statistically significant difference (p approximately 0.958).

The OLS model uses Q4 and daily distinct invoice count, with HC3 robust standard errors. R-squared is approximately 0.482; the Q4 coefficient is approximately GBP 8,708.98 after controlling for invoice count. These coefficients describe associations, not causal effects.

## Limitations

Observed trading days are analyzed without zero-filling missing days. The last December is incomplete. Daily observations may be temporally dependent, and the methods do not correct for serial correlation. Duplicate removal and explicit exclusions affect totals; conclusions apply to the documented analytical dataset.

## Supporting Files

See `figures/`, `q4_stats_tests_report.txt` and `q4_regression_report.txt`. Cleaned data, KPI datasets and warehouse exports are in `data/processed`. Run counts and integrity results are in `run_summary.csv`.
