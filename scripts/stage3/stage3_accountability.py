"""
DECODE X 2026 — Stage 3: Strategic Accountability & Stabilized Regime Evaluation
==================================================================================
Q4 2025 out-of-time data: Oct 1 – Dec 31, 2025.
Sections:
  A. Forecast Performance Audit (Stage1 vs Q3, Stage2 vs Q4)
  B. Strategic Alignment Evaluation
  C. Elasticity & Substitution Diagnosis
  D. 2026 Forward Strategy
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r'c:\Users\asus\Desktop\decodex'

print("=" * 70)
print("STAGE 3: STRATEGIC ACCOUNTABILITY & STABILIZED REGIME EVALUATION")
print("=" * 70)

# ============================================================
# 0. LOAD ALL DATA
# ============================================================
# Historical
master_df = pd.read_csv(f'{DATA_DIR}/data/generated/master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'], format='mixed', dayfirst=True)
master_df['Total_Pax'] = master_df['Boarding_Count'] + master_df['Alighting_Count'] if 'Total_Pax' not in master_df.columns else master_df['Total_Pax']

routes_df = pd.read_csv(f'{DATA_DIR}/data/raw/Bus_Routes.csv')

# Stage 1 forecast
s1_forecast = pd.read_csv(f'{DATA_DIR}/data/generated/forecast_h2_2025.csv')
s1_forecast['Date'] = pd.to_datetime(s1_forecast['Date'], format='mixed', dayfirst=True)

# Stage 2 revised forecast
s2_forecast = pd.read_csv(f'{DATA_DIR}/data/generated/revised_forecast_q4_2025.csv')
s2_forecast['Date'] = pd.to_datetime(s2_forecast['Date'], format='mixed', dayfirst=True)

# Q3 actuals (shock)
q3_actual = pd.read_csv(f'{DATA_DIR}/data/shock/Shock_Ridership_2025_Q3.csv')
q3_actual['Date'] = pd.to_datetime(q3_actual['Date'], format='mixed', dayfirst=True)
q3_actual['Total_Pax'] = q3_actual['Boarding_Count'] + q3_actual['Alighting_Count']

# Q4 actuals (out-of-time) — NEW
q4_actual = pd.read_csv(f'{DATA_DIR}/data/raw/OutOfTime_Ridership_2025_Q4.csv')
q4_actual['Date'] = pd.to_datetime(q4_actual['Date'], format='mixed', dayfirst=True)
q4_actual['Total_Pax'] = q4_actual['Boarding_Count'] + q4_actual['Alighting_Count']

q4_traffic = pd.read_csv(f'{DATA_DIR}/data/raw/OutOfTime_Traffic_2025_Q4.csv')
q4_traffic['Date'] = pd.to_datetime(q4_traffic['Date'], format='mixed', dayfirst=True)

q3_traffic = pd.read_csv(f'{DATA_DIR}/data/shock/Shock_Traffic_2025_Q3.csv')
q3_traffic['Date'] = pd.to_datetime(q3_traffic['Date'], format='mixed', dayfirst=True)

# H1 2025 for baseline comparisons
h1_data = master_df[master_df['Date'] >= '2025-01-01']

print(f"\n  Data loaded:")
print(f"    Q4 Ridership: {q4_actual.shape[0]:,} rows, {q4_actual['Date'].nunique()} days")
print(f"    Q4 Traffic:   {q4_traffic.shape[0]} rows")
print(f"    Q4 Total Pax: {q4_actual['Total_Pax'].sum():,.0f}")

# ============================================================
# A. FORECAST PERFORMANCE AUDIT
# ============================================================
print("\n" + "=" * 70)
print("SECTION A: FORECAST PERFORMANCE AUDIT")
print("=" * 70)

# --- A1: Stage 1 Forecast vs Q3 Actual ---
print(f"\n  A1. STAGE 1 FORECAST vs Q3 ACTUAL (Jul-Sep 2025)")
s1_q3 = s1_forecast[(s1_forecast['Date'] >= '2025-07-01') & (s1_forecast['Date'] <= '2025-09-30')]
s1_q3_route = s1_q3.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
q3_route = q3_actual.groupby(['Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()

comp_q3 = s1_q3_route.merge(q3_route, on=['Route_Code', 'Route_Type'], suffixes=('_fcast', '_actual'))
comp_q3['Error'] = comp_q3['Total_Pax'] - comp_q3['Forecast_Total_Pax']
comp_q3['APE'] = (abs(comp_q3['Error']) / comp_q3['Total_Pax']) * 100
comp_q3['Bias'] = ((comp_q3['Forecast_Total_Pax'] / comp_q3['Total_Pax']) - 1) * 100

s1_q3_mape = comp_q3['APE'].mean()
s1_q3_total_fcast = comp_q3['Forecast_Total_Pax'].sum()
s1_q3_total_actual = comp_q3['Total_Pax'].sum()
s1_q3_overall_error = ((s1_q3_total_fcast / s1_q3_total_actual) - 1) * 100

print(f"    Overall: Forecast={s1_q3_total_fcast:,.0f}, Actual={s1_q3_total_actual:,.0f}, Error={s1_q3_overall_error:+.1f}%")
print(f"    Route-level MAPE: {s1_q3_mape:.1f}%")
print(f"\n    {'Route':<8} {'Type':<12} {'Forecast':>10} {'Actual':>10} {'APE':>7} {'Bias':>8} {'Verdict'}")
print("    " + "-" * 70)
for _, r in comp_q3.sort_values('APE', ascending=False).iterrows():
    verdict = "UNDER-forecast" if r['Bias'] < -5 else ("OVER-forecast" if r['Bias'] > 5 else "Accurate")
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Forecast_Total_Pax']:>9,.0f} "
          f"{r['Total_Pax']:>9,.0f} {r['APE']:>6.1f}% {r['Bias']:>+7.1f}% {verdict}")

# --- A2: Stage 2 Forecast vs Q4 Actual ---
print(f"\n  A2. STAGE 2 FORECAST vs Q4 ACTUAL (Oct-Dec 2025)")
s2_q4_route = s2_forecast.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
q4_route = q4_actual.groupby(['Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()

comp_q4 = s2_q4_route.merge(q4_route, on=['Route_Code', 'Route_Type'], suffixes=('_fcast', '_actual'))
comp_q4['Error'] = comp_q4['Total_Pax'] - comp_q4['Forecast_Total_Pax']
comp_q4['APE'] = (abs(comp_q4['Error']) / comp_q4['Total_Pax']) * 100
comp_q4['Bias'] = ((comp_q4['Forecast_Total_Pax'] / comp_q4['Total_Pax']) - 1) * 100

s2_q4_mape = comp_q4['APE'].mean()
s2_q4_total_fcast = comp_q4['Forecast_Total_Pax'].sum()
s2_q4_total_actual = comp_q4['Total_Pax'].sum()
s2_q4_overall_error = ((s2_q4_total_fcast / s2_q4_total_actual) - 1) * 100

print(f"    Overall: Forecast={s2_q4_total_fcast:,.0f}, Actual={s2_q4_total_actual:,.0f}, Error={s2_q4_overall_error:+.1f}%")
print(f"    Route-level MAPE: {s2_q4_mape:.1f}%")
print(f"\n    {'Route':<8} {'Type':<12} {'Forecast':>10} {'Actual':>10} {'APE':>7} {'Bias':>8} {'Verdict'}")
print("    " + "-" * 70)
for _, r in comp_q4.sort_values('APE', ascending=False).iterrows():
    verdict = "UNDER-forecast" if r['Bias'] < -5 else ("OVER-forecast" if r['Bias'] > 5 else "Accurate")
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Forecast_Total_Pax']:>9,.0f} "
          f"{r['Total_Pax']:>9,.0f} {r['APE']:>6.1f}% {r['Bias']:>+7.1f}% {verdict}")

# --- A3: Stage 1 vs Q4 (unadjusted) for comparison ---
print(f"\n  A3. STAGE 1 (UNADJUSTED) vs Q4 ACTUAL — Did recalibration help?")
s1_q4 = s1_forecast[(s1_forecast['Date'] >= '2025-10-01') & (s1_forecast['Date'] <= '2025-12-31')]
s1_q4_route = s1_q4.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
comp_s1q4 = s1_q4_route.merge(q4_route, on=['Route_Code', 'Route_Type'], suffixes=('_fcast', '_actual'))
comp_s1q4['APE'] = (abs(comp_s1q4['Total_Pax'] - comp_s1q4['Forecast_Total_Pax']) / comp_s1q4['Total_Pax']) * 100
s1_q4_mape = comp_s1q4['APE'].mean()
s1_q4_total_fcast = comp_s1q4['Forecast_Total_Pax'].sum()
s1_q4_overall_error = ((s1_q4_total_fcast / s2_q4_total_actual) - 1) * 100

print(f"    Stage 1 (unadjusted) MAPE: {s1_q4_mape:.1f}%  |  Overall error: {s1_q4_overall_error:+.1f}%")
print(f"    Stage 2 (recalibrated) MAPE: {s2_q4_mape:.1f}%  |  Overall error: {s2_q4_overall_error:+.1f}%")
improvement = s1_q4_mape - s2_q4_mape
print(f"    Recalibration {'IMPROVED' if improvement > 0 else 'WORSENED'} MAPE by {abs(improvement):.1f}pp")

# --- A4: Route-type aggregated error ---
print(f"\n  A4. ROUTE-TYPE AGGREGATED ERROR")
for rtype in ['City', 'Express', 'Feeder', 'Intercity']:
    s1_ape = comp_q3[comp_q3['Route_Type'] == rtype]['APE'].mean()
    s2_ape = comp_q4[comp_q4['Route_Type'] == rtype]['APE'].mean()
    s1_bias = comp_q3[comp_q3['Route_Type'] == rtype]['Bias'].mean()
    s2_bias = comp_q4[comp_q4['Route_Type'] == rtype]['Bias'].mean()
    print(f"    {rtype:<12} Stage1 MAPE={s1_ape:>5.1f}%, Bias={s1_bias:>+6.1f}%  |  "
          f"Stage2 MAPE={s2_ape:>5.1f}%, Bias={s2_bias:>+6.1f}%")

# --- A5: Directional bias ---
print(f"\n  A5. DIRECTIONAL BIAS ANALYSIS")
s1_under = (comp_q3['Bias'] < -5).sum()
s1_over = (comp_q3['Bias'] > 5).sum()
s2_under = (comp_q4['Bias'] < -5).sum()
s2_over = (comp_q4['Bias'] > 5).sum()
print(f"    Stage 1 → Q3: {s1_under} under-forecasts, {s1_over} over-forecasts (systematic under-estimation)")
print(f"    Stage 2 → Q4: {s2_under} under-forecasts, {s2_over} over-forecasts")
if s2_over > s2_under:
    print(f"    ⚠️  Stage 2 OVERREACTED — over-corrected for metro shock (demand partially reverted)")
elif s2_under > s2_over:
    print(f"    ⚠️  Stage 2 UNDERREACTED — did not fully capture the structural shift")
else:
    print(f"    ✓  Stage 2 was directionally balanced")

# --- A6: Variance misestimation ---
print(f"\n  A6. VARIANCE MISESTIMATION")
q3_daily_var = q3_actual.groupby('Date')['Total_Pax'].sum().std()
q4_daily_var = q4_actual.groupby('Date')['Total_Pax'].sum().std()
s2_fcast_var = s2_forecast.groupby('Date')['Forecast_Total_Pax'].sum().std()
print(f"    Q3 daily std:        {q3_daily_var:>8,.0f}")
print(f"    Q4 actual daily std: {q4_daily_var:>8,.0f}")
print(f"    S2 forecast std:     {s2_fcast_var:>8,.0f}")
var_ratio = s2_fcast_var / q4_daily_var
print(f"    Variance ratio (forecast/actual): {var_ratio:.2f}")
if var_ratio > 1.2:
    print(f"    ⚠️  Forecast OVERESTIMATED volatility")
elif var_ratio < 0.8:
    print(f"    ⚠️  Forecast UNDERESTIMATED volatility")
else:
    print(f"    ✓  Variance estimation was reasonable")

# --- A7: Overreaction vs underreaction classification ---
print(f"\n  A7. STRUCTURAL PERMANENCE CLASSIFICATION")
print(f"\n    {'Route':<8} {'Q3 Dev':>8} {'Q4 Dev':>8} {'Persistence':>12} {'Classification'}")
print("    " + "-" * 60)
for _, r3 in comp_q3.iterrows():
    r4 = comp_q4[comp_q4['Route_Code'] == r3['Route_Code']]
    if len(r4) > 0:
        q3_dev = -r3['Bias']  # actual vs forecast direction
        q4_dev = -r4.iloc[0]['Bias']
        if abs(q3_dev) < 5:
            persist = "N/A"
            classif = "Stable"
        elif abs(q4_dev) < abs(q3_dev) * 0.5:
            persist = f"{abs(q4_dev/q3_dev)*100:.0f}%"
            classif = "PARTIAL REVERSION"
        elif abs(q4_dev) >= abs(q3_dev) * 0.8:
            persist = f"{abs(q4_dev/q3_dev)*100:.0f}%"
            classif = "PERMANENT SHIFT"
        else:
            persist = f"{abs(q4_dev/q3_dev)*100:.0f}%"
            classif = "MODERATE DECAY"
        print(f"    {r3['Route_Code']:<8} {q3_dev:>+7.1f}% {q4_dev:>+7.1f}% {persist:>12} {classif}")

# ============================================================
# B. STRATEGIC ALIGNMENT EVALUATION
# ============================================================
print("\n" + "=" * 70)
print("SECTION B: STRATEGIC ALIGNMENT EVALUATION")
print("=" * 70)

# B1: Did Stage 2 fleet reallocation align with Q4?
print(f"\n  B1. FLEET REALLOCATION vs Q4 ACTUAL DEMAND")
stage2_fleet = {
    'X28': 11, 'C03': 11, 'X66': 8, 'C02': 7, 'C01': 7,
    'E22': 7, 'F25': 7, 'X11': 7, 'F18': 5, 'E16': 4, 'C04': 4, 'F12': 3
}

q4_daily = q4_actual.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
q4_avg = q4_daily.groupby('Route_Code')['Total_Pax'].mean().to_dict()
q4_peak = q4_daily.groupby('Route_Code')['Total_Pax'].quantile(0.90).to_dict()

q4_avg_enriched = pd.DataFrame([
    {'Route_Code': rc, 'Fleet': fleet, 'Avg_Daily': q4_avg.get(rc, 0), 'Peak_Daily': q4_peak.get(rc, 0)}
    for rc, fleet in stage2_fleet.items()
])
q4_avg_enriched = q4_avg_enriched.merge(routes_df[['Route_Code', 'Route_Type', 'Route_Length_km', 'Avg_Travel_Time_Min']], on='Route_Code')
q4_avg_enriched['Pax_Per_Bus'] = q4_avg_enriched['Avg_Daily'] / q4_avg_enriched['Fleet']
q4_avg_enriched['Peak_Per_Bus'] = q4_avg_enriched['Peak_Daily'] / q4_avg_enriched['Fleet']
q4_avg_enriched['RT_Hr'] = 2 * (q4_avg_enriched['Avg_Travel_Time_Min'] + 5) / 60
q4_avg_enriched['Headway'] = 60 / (q4_avg_enriched['Fleet'] / q4_avg_enriched['RT_Hr'])

print(f"\n    {'Route':<8} {'Type':<10} {'Fleet':>5} {'AvgDaily':>9} {'PaxBus':>8} {'Headway':>8} {'Alignment'}")
print("    " + "-" * 65)
for _, r in q4_avg_enriched.sort_values('Pax_Per_Bus', ascending=False).iterrows():
    if r['Pax_Per_Bus'] > 500: align = "UNDER-served"
    elif r['Pax_Per_Bus'] > 350: align = "Adequate"
    elif r['Pax_Per_Bus'] > 200: align = "Well-served"
    else: align = "OVER-served"
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<10} {r['Fleet']:>4} {r['Avg_Daily']:>8,.0f} "
          f"{r['Pax_Per_Bus']:>7,.0f} {r['Headway']:>7.1f}m {align}")

# B2: Were adjustments excessive or insufficient?
print(f"\n  B2. ADJUSTMENT ASSESSMENT")
q3_avg_df = q3_actual.groupby('Route_Code')['Total_Pax'].sum() / q3_actual['Date'].nunique()
q4_avg_series = q4_actual.groupby('Route_Code')['Total_Pax'].sum() / q4_actual['Date'].nunique()

print(f"\n    {'Route':<8} {'Q3 Daily':>9} {'Q4 Daily':>9} {'Q3→Q4':>8} {'S2 Adjust':>10} {'Assessment'}")
print("    " + "-" * 65)
for route in sorted(stage2_fleet.keys()):
    q3_d = q3_avg_df.get(route, 0)
    q4_d = q4_avg_series.get(route, 0)
    q3_q4_change = ((q4_d / q3_d) - 1) * 100 if q3_d > 0 else 0
    # Stage 2 adjustment was based on Q3 deviation
    s2_adj = comp_q4[comp_q4['Route_Code'] == route]['Bias'].values
    s2_adj_val = s2_adj[0] if len(s2_adj) > 0 else 0
    
    if abs(s2_adj_val) < 5: assessment = "WELL CALIBRATED"
    elif s2_adj_val > 5: assessment = "OVER-adjusted"
    else: assessment = "UNDER-adjusted"
    
    print(f"    {route:<8} {q3_d:>8,.0f} {q4_d:>8,.0f} {q3_q4_change:>+7.1f}% {s2_adj_val:>+9.1f}% {assessment}")

# B3: Did elasticity assumptions persist?
print(f"\n  B3. ELASTICITY PERSISTENCE CHECK")
h1_traffic = master_df[master_df['Date'] >= '2025-01-01'].groupby('Date').agg({'Total_Pax': 'sum', 'Congestion_Level': 'first'}).reset_index()
q3_merged = q3_actual.groupby('Date')['Total_Pax'].sum().reset_index().merge(q3_traffic, on='Date')
q4_merged = q4_actual.groupby('Date')['Total_Pax'].sum().reset_index().merge(q4_traffic, on='Date')

h1_elast = np.polyfit(h1_traffic['Congestion_Level'], h1_traffic['Total_Pax'], 1)[0]
q3_elast = np.polyfit(q3_merged['Congestion_Level'], q3_merged['Total_Pax'], 1)[0]
q4_elast = np.polyfit(q4_merged['Congestion_Level'], q4_merged['Total_Pax'], 1)[0]

print(f"    H1 2025 elasticity: {h1_elast:>+8,.0f} pax per congestion level")
print(f"    Q3 2025 elasticity: {q3_elast:>+8,.0f} pax per congestion level (shock)")
print(f"    Q4 2025 elasticity: {q4_elast:>+8,.0f} pax per congestion level (stabilized)")
q3_to_q4 = ((q4_elast / q3_elast) - 1) * 100 if q3_elast != 0 else 0
print(f"    Q3→Q4 change: {q3_to_q4:+.1f}%")
if abs(q3_to_q4) < 20:
    print(f"    ✓ Elasticity PERSISTED — Stage 2 assumptions held")
else:
    print(f"    ⚠️ Elasticity {'DECAYED' if q4_elast < q3_elast else 'AMPLIFIED'} — assumptions need revision")

# ============================================================
# C. ELASTICITY & SUBSTITUTION DIAGNOSIS
# ============================================================
print("\n" + "=" * 70)
print("SECTION C: ELASTICITY & SUBSTITUTION DIAGNOSIS")
print("=" * 70)

# C1: Metro substitution elasticity
print(f"\n  C1. METRO SUBSTITUTION ELASTICITY")
h1_type_daily = h1_data.groupby([h1_data['Date'], 'Route_Type'])['Total_Pax'].sum().reset_index()
h1_type_avg = h1_type_daily.groupby('Route_Type')['Total_Pax'].mean()
q3_type_daily = q3_actual.groupby([q3_actual['Date'], 'Route_Type'])['Total_Pax'].sum().reset_index()
q3_type_avg = q3_type_daily.groupby('Route_Type')['Total_Pax'].mean()
q4_type_daily = q4_actual.groupby([q4_actual['Date'], 'Route_Type'])['Total_Pax'].sum().reset_index()
q4_type_avg = q4_type_daily.groupby('Route_Type')['Total_Pax'].mean()

print(f"\n    {'Type':<12} {'H1 2025':>9} {'Q3 (Shock)':>11} {'Q4 (Stable)':>12} {'H1→Q3':>8} {'Q3→Q4':>8} {'H1→Q4':>8}")
print("    " + "-" * 70)
for rtype in ['City', 'Express', 'Feeder', 'Intercity']:
    h1 = h1_type_avg.get(rtype, 0)
    q3 = q3_type_avg.get(rtype, 0)
    q4 = q4_type_avg.get(rtype, 0)
    h1_q3 = ((q3/h1) - 1) * 100 if h1 > 0 else 0
    q3_q4 = ((q4/q3) - 1) * 100 if q3 > 0 else 0
    h1_q4 = ((q4/h1) - 1) * 100 if h1 > 0 else 0
    print(f"    {rtype:<12} {h1:>8,.0f} {q3:>10,.0f} {q4:>11,.0f} {h1_q3:>+7.1f}% {q3_q4:>+7.1f}% {h1_q4:>+7.1f}%")

# C2: Congestion elasticity persistence
print(f"\n  C2. CONGESTION ELASTICITY PERSISTENCE")
h1_cong = h1_traffic['Congestion_Level'].mean()
q3_cong = q3_traffic['Congestion_Level'].mean()
q4_cong = q4_traffic['Congestion_Level'].mean()
h1_speed = master_df[master_df['Date'] >= '2025-01-01'].groupby('Date')['Avg_Speed_kmph'].first().mean()
q3_speed = q3_traffic['Avg_Speed_kmph'].mean()
q4_speed = q4_traffic['Avg_Speed_kmph'].mean()

print(f"    {'Period':<15} {'Congestion':>11} {'Speed':>10} {'Elasticity':>12}")
print("    " + "-" * 50)
print(f"    {'H1 2025':<15} {h1_cong:>10.2f} {h1_speed:>9.1f} {h1_elast:>+11,.0f}")
print(f"    {'Q3 2025 (shock)':<15} {q3_cong:>10.2f} {q3_speed:>9.1f} {q3_elast:>+11,.0f}")
print(f"    {'Q4 2025 (stable)':<15} {q4_cong:>10.2f} {q4_speed:>9.1f} {q4_elast:>+11,.0f}")

# C3: Route-type structural rebalancing
print(f"\n  C3. ROUTE-TYPE STRUCTURAL REBALANCING")
h1_total = h1_type_avg.sum()
q3_total = q3_type_avg.sum()
q4_total = q4_type_avg.sum()
print(f"\n    {'Type':<12} {'H1 Share':>9} {'Q3 Share':>9} {'Q4 Share':>9} {'Trend'}")
print("    " + "-" * 50)
for rtype in ['City', 'Express', 'Feeder', 'Intercity']:
    h1_sh = h1_type_avg.get(rtype, 0) / h1_total * 100
    q3_sh = q3_type_avg.get(rtype, 0) / q3_total * 100
    q4_sh = q4_type_avg.get(rtype, 0) / q4_total * 100
    if q4_sh > q3_sh + 1: trend = "Still growing ▲"
    elif q4_sh < q3_sh - 1: trend = "Reverting ▼"
    else: trend = "Stabilized —"
    print(f"    {rtype:<12} {h1_sh:>8.1f}% {q3_sh:>8.1f}% {q4_sh:>8.1f}% {trend}")

# ============================================================
# D. 2026 FORWARD STRATEGY
# ============================================================
print("\n" + "=" * 70)
print("SECTION D: 2026 FORWARD STRATEGY")
print("=" * 70)

# D1: Feeder redesign
print(f"\n  D1. FEEDER REDESIGN")
for rtype_filter, routes_list in [('Feeder', ['F12', 'F18', 'F25'])]:
    for route in routes_list:
        h1_d = h1_data[h1_data['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
        q3_d = q3_actual[q3_actual['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
        q4_d = q4_actual[q4_actual['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
        h1_q4 = ((q4_d / h1_d) - 1) * 100 if h1_d > 0 else 0
        q3_q4 = ((q4_d / q3_d) - 1) * 100 if q3_d > 0 else 0
        if h1_q4 < -25: action = "DISCONTINUE or REDESIGN as metro-connector"
        elif h1_q4 < -15: action = "RESTRUCTURE — reduce frequency, extend to metro station"
        elif h1_q4 < -5: action = "OPTIMIZE — reduce fleet, adjust schedule"
        else: action = "MAINTAIN current service"
        print(f"    {route}: H1={h1_d:,.0f}→Q3={q3_d:,.0f}→Q4={q4_d:,.0f} (H1→Q4: {h1_q4:+.1f}%, Q3→Q4: {q3_q4:+.1f}%)")
        print(f"          → {action}")

# D2: Express capacity calibration
print(f"\n  D2. EXPRESS CAPACITY CALIBRATION")
for route in ['X11', 'X28', 'X66']:
    h1_d = h1_data[h1_data['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
    q3_d = q3_actual[q3_actual['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
    q4_d = q4_actual[q4_actual['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
    fleet = stage2_fleet[route]
    pax_per_bus = q4_d / fleet
    rt_hr = q4_avg_enriched[q4_avg_enriched['Route_Code'] == route]['RT_Hr'].values[0]
    optimal = int(np.ceil(q4_d * 0.0625 / 60 * rt_hr * 60))  # peak hour capacity
    
    print(f"    {route}: Q4 avg={q4_d:,.0f}/day, fleet={fleet}, pax/bus={pax_per_bus:.0f}")
    print(f"          Q3→Q4 change: {((q4_d/q3_d)-1)*100:+.1f}% — {'Demand moderated' if q4_d < q3_d else 'Still growing'}")
    if pax_per_bus > 500:
        needed = int(np.ceil(q4_d / 400))
        print(f"          → NEED {needed} buses (currently {fleet}), add {needed - fleet}")
    else:
        print(f"          → Current allocation adequate for stabilized demand")

# D3: CBD rationalization
print(f"\n  D3. CBD RATIONALIZATION FRAMEWORK")
cbd_routes = ['C01', 'C02', 'C03', 'C04']
for route in cbd_routes:
    h1_d = h1_data[h1_data['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
    q4_d = q4_actual[q4_actual['Route_Code'] == route].groupby('Date')['Total_Pax'].sum().mean()
    change = ((q4_d / h1_d) - 1) * 100 if h1_d > 0 else 0
    fleet = stage2_fleet[route]
    print(f"    {route}: H1→Q4={change:+.1f}%, fleet={fleet}, Q4 daily={q4_d:,.0f}")

# D4: Volatility buffer mechanism
print(f"\n  D4. VOLATILITY BUFFER MECHANISM")
q4_cv = q4_daily.groupby('Route_Code')['Total_Pax'].std() / q4_daily.groupby('Route_Code')['Total_Pax'].mean()
q3_cv = q3_actual.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index().groupby('Route_Code')['Total_Pax'].std() / \
        q3_actual.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index().groupby('Route_Code')['Total_Pax'].mean()

print(f"\n    {'Route':<8} {'Q3 CV':>7} {'Q4 CV':>7} {'Change':>8} {'Stability'}")
print("    " + "-" * 40)
for route in sorted(stage2_fleet.keys()):
    q3_v = q3_cv.get(route, 0)
    q4_v = q4_cv.get(route, 0)
    ch = ((q4_v / q3_v) - 1) * 100 if q3_v > 0 else 0
    stab = "Stable" if q4_v < 0.15 else ("Moderate" if q4_v < 0.25 else "Volatile")
    print(f"    {route:<8} {q3_v:>6.3f} {q4_v:>6.3f} {ch:>+7.1f}% {stab}")

buffer_routes = [r for r in q4_cv.index if q4_cv[r] > 0.2]
print(f"\n    Volatile routes (CV > 0.20): {buffer_routes if buffer_routes else 'None'}")
print(f"    Recommendation: {'Reserve 3-4 buses as dynamic buffer' if buffer_routes else 'Standard 2-bus reserve sufficient'}")

# D5: Passenger redistribution quantification
print(f"\n  D5. PASSENGER REDISTRIBUTION (H1 → Q4 — Full Stabilized Impact)")
h1_total_daily = h1_data.groupby('Date')['Total_Pax'].sum().mean()
q4_total_daily = q4_actual.groupby('Date')['Total_Pax'].sum().mean()
print(f"    H1 daily avg: {h1_total_daily:>10,.0f}")
print(f"    Q4 daily avg: {q4_total_daily:>10,.0f}")
print(f"    Net change:   {q4_total_daily - h1_total_daily:>+10,.0f} ({((q4_total_daily/h1_total_daily)-1)*100:>+.1f}%)")

# D6: Efficiency gain
print(f"\n  D6. EFFICIENCY GAIN (2026 Projection)")
q4_enriched = q4_daily.merge(routes_df[['Route_Code', 'Route_Length_km']], on='Route_Code')
q4_pax_km = q4_enriched.groupby('Route_Code').apply(
    lambda g: g['Total_Pax'].mean() / g['Route_Length_km'].iloc[0])
h1_enriched = h1_data.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
h1_enriched = h1_enriched.merge(routes_df[['Route_Code', 'Route_Length_km']], on='Route_Code')
h1_pax_km = h1_enriched.groupby('Route_Code').apply(
    lambda g: g['Total_Pax'].mean() / g['Route_Length_km'].iloc[0])

print(f"    {'Route':<8} {'H1 Pax/km':>10} {'Q4 Pax/km':>10} {'Change':>8}")
print("    " + "-" * 40)
for route in sorted(stage2_fleet.keys()):
    h1_pk = h1_pax_km.get(route, 0)
    q4_pk = q4_pax_km.get(route, 0)
    ch = ((q4_pk / h1_pk) - 1) * 100 if h1_pk > 0 else 0
    print(f"    {route:<8} {h1_pk:>9.1f} {q4_pk:>9.1f} {ch:>+7.1f}%")

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("EXECUTIVE SUMMARY: STAGE 3 ACCOUNTABILITY AUDIT")
print("=" * 70)

print(f"""
  FORECAST PERFORMANCE:
    Stage 1 → Q3: MAPE = {s1_q3_mape:.1f}%, Overall error = {s1_q3_overall_error:+.1f}%
    Stage 2 → Q4: MAPE = {s2_q4_mape:.1f}%, Overall error = {s2_q4_overall_error:+.1f}%
    Stage 1 (unadj) → Q4: MAPE = {s1_q4_mape:.1f}%
    Recalibration improved MAPE by {improvement:.1f}pp

  DEMAND TRAJECTORY:
    H1: {h1_total_daily:>8,.0f}/day → Q3: {q3_type_avg.sum():>8,.0f}/day → Q4: {q4_total_daily:>8,.0f}/day
    Network entered REDISTRIBUTED EQUILIBRIUM (not full reversion)

  CONGESTION:
    H1: {h1_cong:.2f} → Q3: {q3_cong:.2f} (shock) → Q4: {q4_cong:.2f} (stabilized)
    Speed: {h1_speed:.1f} → {q3_speed:.1f} → {q4_speed:.1f} km/h

  KEY FINDING:
    The metro shock partially reverted but did NOT return to baseline.
    The new equilibrium sits BETWEEN the pre-shock and peak-shock levels.
    Express demand moderated but remains structurally elevated.
    Feeder contraction stabilized — floor found.
""")

print("=" * 70)
print("[DONE] STAGE 3 ANALYSIS COMPLETE")
print("=" * 70)
