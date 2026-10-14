import os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm


def analyze(processed, out):
    os.environ.setdefault('MPLCONFIGDIR', str(out / '.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    daily = pd.read_csv(processed / 'daily_kpis.csv', parse_dates=['full_date'])
    daily['return_rate'] = daily.returned_revenue / daily.gross_revenue.replace(0, np.nan)
    blocks = ['Exploratory Q4 vs non-Q4 analysis. Observed trading days only; no zero-fill.',
              'Daily observations may be autocorrelated. P-values are descriptive, not causal.']
    for metric in ['net_revenue', 'return_rate']:
        a = daily.loc[daily.is_q4.eq(1), metric].dropna().to_numpy()
        b = daily.loc[daily.is_q4.eq(0), metric].dropna().to_numpy()
        if min(len(a),len(b)) < 2:
            blocks.append(f'{metric}: skipped, need >=2 observations in each group.'); continue
        va, vb = a.var(ddof=1)/len(a), b.var(ddof=1)/len(b)
        if va + vb == 0:
            blocks.append(f'{metric}: skipped, zero sampling variance.'); continue
        test = stats.ttest_ind(a,b,equal_var=False)
        df = (va+vb)**2 / (va**2/(len(a)-1)+vb**2/(len(b)-1))
        diff = a.mean()-b.mean(); margin = stats.t.ppf(.975,df)*np.sqrt(va+vb)
        blocks.append(f'{metric}: n_q4={len(a)}, n_non_q4={len(b)}, mean_difference={diff:.6f}, t={test.statistic:.6f}, p={test.pvalue:.8g}, df={df:.3f}, 95% CI=[{diff-margin:.6f}, {diff+margin:.6f}]')
    (out / 'q4_stats_tests_report.txt').write_text('\n\n'.join(blocks)+'\n')
    model_data = daily.rename(columns={'full_date':'order_date','net_revenue':'daily_revenue'})[['order_date','daily_revenue','daily_orders','is_q4']]
    model_data.to_csv(processed / 'q4_regression_dataset_daily.csv',index=False)
    x = sm.add_constant(model_data[['is_q4','daily_orders']].astype(float),has_constant='add')
    if len(x)>3 and np.linalg.matrix_rank(x)==3:
        model = sm.OLS(model_data.daily_revenue.astype(float), x).fit(cov_type='HC3')
        text = model.summary().as_text() + '\nHC3 robust errors; no causal interpretation or correction for temporal dependence.\n'
    else:
        text = 'Regression skipped: insufficient observations or rank-deficient design.\n'
    (out / 'q4_regression_report.txt').write_text(text)
    figures = out / 'figures'; figures.mkdir(exist_ok=True)
    def save(name, title, xs, ys, bars=False):
        fig, ax = plt.subplots(figsize=(10,4))
        if bars:
            ax.bar([str(x) for x in xs],ys); ax.tick_params(axis='x',labelrotation=35)
        else:
            ax.plot(xs,ys)
        ax.set_title(title); ax.set_ylabel('GBP'); fig.tight_layout()
        fig.savefig(figures / (name+'.png'),dpi=140); plt.close(fig)
    save('daily_revenue','Daily net revenue',daily.full_date,daily.net_revenue)
    monthly = daily.groupby(daily.full_date.dt.to_period('M')).net_revenue.sum()
    save('monthly_revenue','Monthly net revenue',monthly.index.astype(str),monthly.values,True)
    for name, label in [('top_countries','country'),('top_products','stockcode')]:
        frame = pd.read_csv(processed / (name+'.csv'))
        save(name,name.replace('_',' ').title(),frame[label],frame.net_revenue,True)
    save('revenue_breakdown','Gross, returns magnitude, net', ['Gross','Returns','Net'],[daily.gross_revenue.sum(),daily.returned_revenue.sum(),daily.net_revenue.sum()],True)
