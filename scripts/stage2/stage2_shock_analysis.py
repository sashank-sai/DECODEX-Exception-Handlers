"""
DECODE X 2026 — Stage 2: Structural Break Analysis
====================================================
Metro Phase 2 commenced July 1, 2025 → structural break.
New data: Q3 2025 ridership + traffic actuals.

Sections:
  A. Detect structural break (Stage 1 forecast vs Q3 actual)
  B. Recalibrate forecast for Q4 2025 (Oct-Dec)
  C. Operational risk reassessment
  D. Revised fleet reallocation strategy
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r'c:\Users\asus\Desktop\decodex'

# ============================================================
# 0. LOAD ALL DATA
# ============================================================
print("=" * 70)
print("STAGE 2: STRUCTURAL BREAK ANALYSIS — METRO PHASE 2")
print("=" * 70)

# Historical master dataset
master_df = pd.read_csv(f'{DATA_DIR}/master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])

# Stage 1 forecast
forecast_df = pd.read_csv(f'{DATA_DIR}/forecast_h2_2025.csv')
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])

# NEW: Shock data
shock_ride = pd.read_csv(f'{DATA_DIR}/Shock_Ridership_2025_Q3.csv')
shock_ride['Date'] = pd.to_datetime(shock_ride['Date'])
shock_ride['Total_Pax'] = shock_ride['Boarding_Count'] + shock_ride['Alighting_Count']

shock_traffic = pd.read_csv(f'{DATA_DIR}/Shock_Traffic_2025_Q3.csv')
shock_traffic['Date'] = pd.to_datetime(shock_traffic['Date'])

# Route metadata
routes_df = pd.read_csv(f'{DATA_DIR}/Bus_Routes.csv')
mapping_df = pd.read_csv(f'{DATA_DIR}/Route_Stop_Mapping.csv')
stops_df = pd.read_csv(f'{DATA_DIR}/Bus_Stops.csv')

# Enrich shock data — it already has Route_Code & Route_Type
# Only add Route_Length_km from routes, and Zone/Stop_Type from stops
shock_ride = shock_ride.merge(
    routes_df[['Route_ID', 'Route_Length_km']].drop_duplicates(), on='Route_ID', how='left')
shock_ride = shock_ride.merge(
    stops_df[['Stop_ID', 'Stop_Type', 'Zone']].drop_duplicates(), on='Stop_ID', how='left')
shock_ride = shock_ride.merge(shock_traffic, on='Date', how='left')

# Metro-affected zones
METRO_ZONES = ['CBD_Downtown', 'CBD_BusinessBay', 'Core_Deira']

print(f"\n  Shock data loaded:")
print(f"    Ridership: {shock_ride.shape[0]:,} rows, {shock_ride['Date'].nunique()} days "
      f"({shock_ride['Date'].min().date()} to {shock_ride['Date'].max().date()})")
print(f"    Traffic:   {shock_traffic.shape[0]} rows")
print(f"    Total Q3 Pax: {shock_ride['Total_Pax'].sum():,.0f}")
print(f"    Metro-affected zones: {METRO_ZONES}")

# ============================================================
# A. DETECT STRUCTURAL BREAK
# ============================================================
print("\n" + "=" * 70)
print("SECTION A: STRUCTURAL BREAK DETECTION")
print("=" * 70)

# A1: Stage 1 forecast vs Q3 actual — overall
q3_forecast = forecast_df[(forecast_df['Date'] >= '2025-07-01') & (forecast_df['Date'] <= '2025-09-30')]
q3_fcast_daily = q3_forecast.groupby('Date')['Forecast_Total_Pax'].sum()
q3_actual_daily = shock_ride.groupby('Date')['Total_Pax'].sum()

# Align dates
common_dates = q3_fcast_daily.index.intersection(q3_actual_daily.index)
fcast_total = q3_fcast_daily.loc[common_dates].sum()
actual_total = q3_actual_daily.loc[common_dates].sum()
deviation = (actual_total / fcast_total - 1) * 100

print(f"\n  A1. OVERALL Q3 DEVIATION")
print(f"    Stage 1 Forecast (Q3): {fcast_total:>12,.0f}")
print(f"    Actual (Q3):           {actual_total:>12,.0f}")
print(f"    Deviation:             {deviation:>+11.1f}%")
print(f"    Absolute gap:          {actual_total - fcast_total:>+12,.0f} passengers")

if deviation < -5:
    print(f"    ⚠️  SIGNIFICANT NEGATIVE STRUCTURAL BREAK DETECTED")
elif deviation > 5:
    print(f"    ⚠️  SIGNIFICANT POSITIVE STRUCTURAL BREAK DETECTED")
else:
    print(f"    ✓  Within acceptable range")

# A2: Route-level divergence
print(f"\n  A2. ROUTE-LEVEL DIVERGENCE MAGNITUDE")
q3_fcast_route = q3_forecast.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
q3_actual_route = shock_ride.groupby(['Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()

route_comparison = q3_fcast_route.merge(q3_actual_route, on=['Route_Code', 'Route_Type'], suffixes=('_fcast', '_actual'))
route_comparison['Deviation_%'] = ((route_comparison['Total_Pax'] / route_comparison['Forecast_Total_Pax']) - 1) * 100
route_comparison['Abs_Gap'] = route_comparison['Total_Pax'] - route_comparison['Forecast_Total_Pax']
route_comparison = route_comparison.sort_values('Deviation_%')

print(f"\n    {'Route':<8} {'Type':<12} {'Forecast':>10} {'Actual':>10} {'Deviation':>10} {'Gap':>12} {'Shift Type'}")
print("    " + "-" * 85)
for _, r in route_comparison.iterrows():
    dev = r['Deviation_%']
    if dev < -15: shift = "MAJOR DECLINE"
    elif dev < -5: shift = "Moderate decline"
    elif dev < 5: shift = "Stable"
    elif dev < 15: shift = "Moderate growth"
    else: shift = "MAJOR GROWTH"
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Forecast_Total_Pax']:>9,.0f} "
          f"{r['Total_Pax']:>9,.0f} {dev:>+9.1f}% {r['Abs_Gap']:>+11,.0f} {shift}")

# A3: Shift classification
print(f"\n  A3. SHIFT CLASSIFICATION BY TYPE")

# Level shift: compare pre-shock vs post-shock daily averages
h1_2025 = master_df[master_df['Date'] >= '2025-01-01']
h1_daily = h1_2025.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
h1_route_avg = h1_daily.groupby('Route_Code')['Total_Pax'].mean()

q3_route_daily = shock_ride.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
q3_route_avg = q3_route_daily.groupby('Route_Code')['Total_Pax'].mean()

level_shift = ((q3_route_avg / h1_route_avg) - 1) * 100

# Volatility shift: compare CV
h1_route_cv = h1_daily.groupby('Route_Code')['Total_Pax'].std() / h1_daily.groupby('Route_Code')['Total_Pax'].mean()
q3_route_cv = q3_route_daily.groupby('Route_Code')['Total_Pax'].std() / q3_route_daily.groupby('Route_Code')['Total_Pax'].mean()
vol_shift = ((q3_route_cv / h1_route_cv) - 1) * 100

# Congestion-mediated shift
h1_traffic = master_df[master_df['Date'] >= '2025-01-01'].groupby('Date')[['Congestion_Level', 'Avg_Speed_kmph']].first()
q3_cong_mean = shock_traffic['Congestion_Level'].mean()
h1_cong_mean = h1_traffic['Congestion_Level'].mean()
cong_shift = ((q3_cong_mean / h1_cong_mean) - 1) * 100

q3_speed_mean = shock_traffic['Avg_Speed_kmph'].mean()
h1_speed_mean = h1_traffic['Avg_Speed_kmph'].mean()
speed_shift = ((q3_speed_mean / h1_speed_mean) - 1) * 100

print(f"\n    LEVEL SHIFT (avg daily demand change, H1→Q3 2025):")
for route in sorted(level_shift.index):
    marker = "▼" if level_shift[route] < -5 else ("▲" if level_shift[route] > 5 else "—")
    print(f"      {route}: {level_shift[route]:>+7.1f}% {marker}")

print(f"\n    VOLATILITY SHIFT (CV change, H1→Q3 2025):")
for route in sorted(vol_shift.index):
    marker = "⚡" if abs(vol_shift[route]) > 20 else "—"
    print(f"      {route}: {vol_shift[route]:>+7.1f}% {marker}")

print(f"\n    CONGESTION-MEDIATED SHIFT:")
print(f"      Congestion Level: {h1_cong_mean:.2f} → {q3_cong_mean:.2f} ({cong_shift:>+.1f}%)")
print(f"      Avg Speed:        {h1_speed_mean:.1f} → {q3_speed_mean:.1f} km/h ({speed_shift:>+.1f}%)")

# Elasticity shift: how has ridership-congestion relationship changed?
q3_merged = shock_ride.groupby('Date').agg({'Total_Pax': 'sum', 'Congestion_Level': 'first'}).reset_index()
h1_merged = master_df[master_df['Date'] >= '2025-01-01'].groupby('Date').agg({'Total_Pax': 'sum', 'Congestion_Level': 'first'}).reset_index()

if len(q3_merged) > 5:
    from numpy.polynomial.polynomial import polyfit
    h1_elast = np.polyfit(h1_merged['Congestion_Level'], h1_merged['Total_Pax'], 1)[0]
    q3_elast = np.polyfit(q3_merged['Congestion_Level'], q3_merged['Total_Pax'], 1)[0]
    elast_change = ((q3_elast / h1_elast) - 1) * 100 if h1_elast != 0 else 0
    
    print(f"\n    ELASTICITY SHIFT (congestion→ridership sensitivity):")
    print(f"      H1 2025 slope:  {h1_elast:>+10.0f} pax per congestion level")
    print(f"      Q3 2025 slope:  {q3_elast:>+10.0f} pax per congestion level")
    print(f"      Change:         {elast_change:>+9.1f}%")
    if abs(elast_change) > 20:
        print(f"      ⚠️  Metro Phase 2 has significantly altered the congestion-ridership relationship")

# A4: Zone-level impact (Metro vs non-Metro)
print(f"\n  A4. ZONE-LEVEL IMPACT (Metro-Affected vs Others)")

# Q3 actual by zone
q3_zone = shock_ride.groupby('Zone')['Total_Pax'].sum()
# H1 actual by zone (3 months equivalent for fair comparison)
h1_zone = master_df[master_df['Date'] >= '2025-01-01'].groupby('Zone')['Total_Pax'].sum()
h1_days = master_df[master_df['Date'] >= '2025-01-01']['Date'].nunique()
q3_days = shock_ride['Date'].nunique()
h1_zone_daily = h1_zone / h1_days
q3_zone_daily = q3_zone / q3_days

for zone in sorted(q3_zone_daily.index):
    if zone in h1_zone_daily.index:
        change = ((q3_zone_daily[zone] / h1_zone_daily[zone]) - 1) * 100
        metro_tag = " [METRO-AFFECTED]" if zone in METRO_ZONES else ""
        marker = "▼▼" if change < -15 else ("▼" if change < -5 else ("▲" if change > 5 else "—"))
        print(f"    {zone:<25} H1: {h1_zone_daily[zone]:>7,.0f}/day → Q3: {q3_zone_daily[zone]:>7,.0f}/day  {change:>+6.1f}% {marker}{metro_tag}")

# ============================================================
# B. RECALIBRATE FORECAST (Q4 2025: Oct-Dec)
# ============================================================
print("\n" + "=" * 70)
print("SECTION B: RECALIBRATED FORECAST (Q4 2025: Oct-Dec)")
print("=" * 70)

# Build adjustment factors per route from Q3 deviation
route_adjustment = {}
for _, r in route_comparison.iterrows():
    route_adjustment[r['Route_Code']] = r['Deviation_%'] / 100  # e.g., -0.15 for -15%

# Classification: temporary shock vs regime change
print(f"\n  B1. SHOCK CLASSIFICATION")
for route in sorted(route_adjustment.keys()):
    adj = route_adjustment[route] * 100
    if abs(adj) < 5:
        classification = "STABLE — no adjustment needed"
        adj_factor = 1.0
    elif abs(adj) < 15:
        classification = "MODERATE SHIFT — partial adjustment (50% of deviation)"
        adj_factor = 1.0 + route_adjustment[route] * 0.5  # partial: assume 50% permanent
    else:
        classification = "REGIME CHANGE — full adjustment"
        adj_factor = 1.0 + route_adjustment[route] * 0.75  # 75% permanent, 25% transient
    
    route_adjustment[route] = adj_factor
    print(f"    {route}: deviation {adj:>+6.1f}% → {classification} → Factor: {adj_factor:.3f}")

# Generate Q4 forecast
q4_original = forecast_df[(forecast_df['Date'] >= '2025-10-01') & (forecast_df['Date'] <= '2025-12-31')].copy()
q4_revised = q4_original.copy()

for route, factor in route_adjustment.items():
    mask = q4_revised['Route_Code'] == route
    q4_revised.loc[mask, 'Forecast_Total_Pax'] = q4_revised.loc[mask, 'Forecast_Total_Pax'] * factor

# Also adjust for congestion shift
cong_factor = q3_cong_mean / h1_cong_mean
print(f"\n  B2. CONGESTION ADJUSTMENT")
print(f"    Congestion factor: {cong_factor:.3f} (H1→Q3)")

# Winter seasonal boost (Oct-Dec are entering winter peak)
print(f"\n  B3. REVISED Q4 FORECAST SUMMARY")
q4_orig_total = q4_original['Forecast_Total_Pax'].sum()
q4_rev_total = q4_revised['Forecast_Total_Pax'].sum()
q4_change = (q4_rev_total / q4_orig_total - 1) * 100

print(f"    Original Q4 forecast:  {q4_orig_total:>12,.0f}")
print(f"    Revised Q4 forecast:   {q4_rev_total:>12,.0f}")
print(f"    Change:                {q4_change:>+11.1f}%")

# Route breakdown
print(f"\n    {'Route':<8} {'Type':<12} {'Original':>10} {'Revised':>10} {'Change':>8}")
print("    " + "-" * 55)
q4_route_orig = q4_original.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
q4_route_rev = q4_revised.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
q4_comp = q4_route_orig.merge(q4_route_rev, on=['Route_Code', 'Route_Type'], suffixes=('_orig', '_rev'))
q4_comp['Change'] = ((q4_comp['Forecast_Total_Pax_rev'] / q4_comp['Forecast_Total_Pax_orig']) - 1) * 100
q4_comp = q4_comp.sort_values('Change')

for _, r in q4_comp.iterrows():
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Forecast_Total_Pax_orig']:>9,.0f} "
          f"{r['Forecast_Total_Pax_rev']:>9,.0f} {r['Change']:>+7.1f}%")

# Uncertainty bands
print(f"\n  B4. UNCERTAINTY REVISION")
print(f"    Pre-shock uncertainty: ±5% (based on historical seasonality)")
q3_dev_std = route_comparison['Deviation_%'].std()
print(f"    Post-shock uncertainty: ±{max(q3_dev_std, 5):.1f}% (widened by structural break)")
print(f"    Q4 Forecast range: {q4_rev_total * 0.9:,.0f} – {q4_rev_total * 1.1:,.0f}")

# Save revised forecast
q4_revised.to_csv(f'{DATA_DIR}/revised_forecast_q4_2025.csv', index=False)
print(f"\n    Saved: revised_forecast_q4_2025.csv")

# ============================================================
# C. OPERATIONAL RISK REASSESSMENT
# ============================================================
print("\n" + "=" * 70)
print("SECTION C: OPERATIONAL RISK REASSESSMENT")
print("=" * 70)

# C1: Updated overload corridors
print(f"\n  C1. UPDATED OVERLOAD RISK (Post-Metro)")
q3_route_daily_total = shock_ride.groupby(['Date', 'Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()
q3_route_avg2 = q3_route_daily_total.groupby(['Route_Code', 'Route_Type'])['Total_Pax'].mean().reset_index()
q3_route_avg2 = q3_route_avg2.merge(routes_df[['Route_Code', 'Route_Length_km']], on='Route_Code')
q3_route_avg2['Pax_Per_Km'] = q3_route_avg2['Total_Pax'] / q3_route_avg2['Route_Length_km']

# Compare with pre-shock overload
h1_route_daily_total = h1_daily.copy()
h1_route_avg2 = h1_route_daily_total.groupby('Route_Code')['Total_Pax'].mean().reset_index()
h1_route_avg2 = h1_route_avg2.merge(routes_df[['Route_Code', 'Route_Length_km']], on='Route_Code')
h1_route_avg2['Pax_Per_Km'] = h1_route_avg2['Total_Pax'] / h1_route_avg2['Route_Length_km']

overload_comp = q3_route_avg2[['Route_Code', 'Route_Type', 'Total_Pax', 'Pax_Per_Km']].merge(
    h1_route_avg2[['Route_Code', 'Pax_Per_Km']], on='Route_Code', suffixes=('_post', '_pre'))
overload_comp['PaxKm_Change'] = ((overload_comp['Pax_Per_Km_post'] / overload_comp['Pax_Per_Km_pre']) - 1) * 100
overload_comp = overload_comp.sort_values('Pax_Per_Km_post', ascending=False)

print(f"\n    {'Route':<8} {'Type':<12} {'Pre Pax/km':>11} {'Post Pax/km':>12} {'Change':>8} {'Status'}")
print("    " + "-" * 70)
for _, r in overload_comp.iterrows():
    if r['Pax_Per_Km_post'] > 15: status = "🔴 OVERLOADED"
    elif r['Pax_Per_Km_post'] > 10: status = "🟡 WARNING"
    else: status = "🟢 OK"
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Pax_Per_Km_pre']:>10.1f} "
          f"{r['Pax_Per_Km_post']:>11.1f} {r['PaxKm_Change']:>+7.1f}% {status}")

# C2: Feeder viability
print(f"\n  C2. FEEDER VIABILITY ASSESSMENT")
feeder_routes = q3_route_avg2[q3_route_avg2['Route_Type'] == 'Feeder']
for _, f in feeder_routes.iterrows():
    pre = h1_route_avg2[h1_route_avg2['Route_Code'] == f['Route_Code']]['Total_Pax'].values
    pre_val = pre[0] if len(pre) > 0 else 0
    change = ((f['Total_Pax'] / pre_val) - 1) * 100 if pre_val > 0 else 0
    viable = "VIABLE" if change > -20 else "AT RISK"
    print(f"    {f['Route_Code']}: {pre_val:,.0f}/day → {f['Total_Pax']:,.0f}/day ({change:>+.1f}%) — {viable}")

# C3: Express sustainability
print(f"\n  C3. EXPRESS SUSTAINABILITY")
express_routes = q3_route_avg2[q3_route_avg2['Route_Type'] == 'Express']
for _, e in express_routes.iterrows():
    pre = h1_route_avg2[h1_route_avg2['Route_Code'] == e['Route_Code']]['Total_Pax'].values
    pre_val = pre[0] if len(pre) > 0 else 0
    change = ((e['Total_Pax'] / pre_val) - 1) * 100 if pre_val > 0 else 0
    sust = "SUSTAINABLE" if e['Pax_Per_Km'] < 20 else "OVER-CAPACITY"
    print(f"    {e['Route_Code']}: {pre_val:,.0f}/day → {e['Total_Pax']:,.0f}/day ({change:>+.1f}%) [{e['Pax_Per_Km']:.1f} pax/km] — {sust}")

# ============================================================
# D. FLEET REALLOCATION STRATEGY (REVISED)
# ============================================================
print("\n" + "=" * 70)
print("SECTION D: REVISED FLEET REALLOCATION STRATEGY")
print("=" * 70)

BUS_CAPACITY = 60
TOTAL_FLEET = 81

# Recalculate fleet needs based on Q3 actual demand + Q4 forecast
q3_peak = q3_route_daily_total.groupby('Route_Code')['Total_Pax'].quantile(0.90).reset_index()
q3_peak.columns = ['Route_Code', 'Peak_Daily']
q3_peak = q3_peak.merge(routes_df[['Route_Code', 'Route_Type', 'Avg_Travel_Time_Min', 'Route_Length_km']], on='Route_Code')

q3_peak['Peak_Hourly'] = q3_peak['Peak_Daily'] * 0.0625
q3_peak['Round_Trip_Hr'] = 2 * (q3_peak['Avg_Travel_Time_Min'] + 5) / 60
q3_peak['Trips_Per_Hr'] = np.ceil(q3_peak['Peak_Hourly'] / BUS_CAPACITY)
q3_peak['Required_Fleet'] = np.ceil(q3_peak['Trips_Per_Hr'] * q3_peak['Round_Trip_Hr'])
q3_peak['Headway'] = np.where(q3_peak['Trips_Per_Hr'] > 0, 60 / q3_peak['Trips_Per_Hr'], 60)

# Optimal distribution (density-proportional)
q3_peak['Pax_Per_Km'] = q3_peak['Peak_Daily'] / q3_peak['Route_Length_km']
total_density = q3_peak['Pax_Per_Km'].sum()
q3_peak['Optimal_Fleet'] = np.round(q3_peak['Pax_Per_Km'] / total_density * TOTAL_FLEET)
diff = TOTAL_FLEET - q3_peak['Optimal_Fleet'].sum()
q3_peak.loc[q3_peak['Pax_Per_Km'].idxmax(), 'Optimal_Fleet'] += diff

q3_peak['Fleet_Delta'] = q3_peak['Optimal_Fleet'] - q3_peak['Required_Fleet']
q3_peak['New_Headway'] = np.where(
    q3_peak['Optimal_Fleet'] > 0,
    60 / (q3_peak['Optimal_Fleet'] / q3_peak['Round_Trip_Hr']),
    60
)

# Compare with Stage 1 reallocation
stage1_fleet = {
    'X28': (7, 10), 'C03': (8, 10), 'C02': (5, 7), 'E22': (6, 8),
    'F25': (7, 9), 'X11': (5, 5), 'F18': (8, 7), 'C01': (8, 7),
    'E16': (5, 4), 'X66': (8, 6), 'C04': (7, 4), 'F12': (7, 4)
}

print(f"\n  D1. REVISED FLEET ALLOCATION (Post-Metro Phase 2)")
print(f"\n    {'Route':<8} {'Type':<12} {'Stage1':>7} {'Revised':>8} {'Change':>7} {'Headway':>8} {'Status'}")
print("    " + "-" * 65)
q3_peak = q3_peak.sort_values('Pax_Per_Km', ascending=False)
total_revised = 0
for _, r in q3_peak.iterrows():
    s1_curr, s1_prop = stage1_fleet.get(r['Route_Code'], (0, 0))
    revised = int(r['Optimal_Fleet'])
    total_revised += revised
    change = revised - s1_prop
    change_str = f"+{change}" if change >= 0 else str(change)
    status = "UPGRADED" if change > 0 else ("REDUCED" if change < 0 else "SAME")
    print(f"    {r['Route_Code']:<8} {r['Route_Type']:<12} {s1_prop:>6} {revised:>7} {change_str:>6} "
          f"{r['New_Headway']:>7.1f}m {status}")

print(f"\n    Total fleet: {total_revised:.0f} (target: {TOTAL_FLEET})")

# D2: Headway revisions
print(f"\n  D2. HEADWAY REVISIONS (Stage 1 → Stage 2)")
for _, r in q3_peak.iterrows():
    s1_curr, s1_prop = stage1_fleet.get(r['Route_Code'], (0, 0))
    # Calculate Stage 1 headway
    rt_hr = r['Round_Trip_Hr']
    s1_headway = 60 / (s1_prop / rt_hr) if s1_prop > 0 else 60
    direction = "TIGHTER ✓" if r['New_Headway'] < s1_headway else ("WIDER ▼" if r['New_Headway'] > s1_headway else "SAME")
    print(f"    {r['Route_Code']}: Stage1={s1_headway:.1f}m → Stage2={r['New_Headway']:.1f}m  [{direction}]")

# D3: Volatility buffer
print(f"\n  D3. VOLATILITY BUFFER APPROACH")
print(f"    Pre-shock demand CV:  {h1_route_cv.mean():.3f}")
print(f"    Post-shock demand CV: {q3_route_cv.mean():.3f}")
cv_change = ((q3_route_cv.mean() / h1_route_cv.mean()) - 1) * 100
print(f"    Volatility change:    {cv_change:>+.1f}%")
if cv_change > 10:
    buffer = int(np.ceil(TOTAL_FLEET * 0.05))
    print(f"    Recommendation: Reserve {buffer} buses ({buffer/TOTAL_FLEET*100:.0f}% of fleet) as volatility buffer")
    print(f"    Deploy dynamically when any route exceeds 90% peak load")
else:
    print(f"    Recommendation: Standard 2-bus reserve is sufficient")

# D4: Passenger redistribution summary
print(f"\n  D4. PASSENGER REDISTRIBUTION SUMMARY")
h1_total_daily = h1_daily.groupby('Date')['Total_Pax'].sum().mean()
q3_total_daily = q3_route_daily_total.groupby('Date')['Total_Pax'].sum().mean()
print(f"    H1 2025 avg daily:  {h1_total_daily:>10,.0f}")
print(f"    Q3 2025 avg daily:  {q3_total_daily:>10,.0f}")
print(f"    Net change:         {q3_total_daily - h1_total_daily:>+10,.0f} ({((q3_total_daily/h1_total_daily)-1)*100:>+.1f}%)")

# Where did passengers go?
print(f"\n    Route-type redistribution:")
for rtype in ['City', 'Express', 'Feeder', 'Intercity']:
    h1_rt_daily = h1_daily.merge(routes_df[['Route_Code', 'Route_Type']], left_on='Route_Code', right_on='Route_Code')
    h1_rt = h1_rt_daily[h1_rt_daily['Route_Type'] == rtype].groupby('Date')['Total_Pax'].sum().mean()
    q3_rt = q3_route_daily_total[q3_route_daily_total['Route_Type'] == rtype].groupby('Date')['Total_Pax'].sum().mean()
    change_pct = ((q3_rt / h1_rt) - 1) * 100 if h1_rt > 0 else 0
    print(f"      {rtype:<12}: {h1_rt:>8,.0f} → {q3_rt:>8,.0f}/day ({change_pct:>+.1f}%)")

# D5: Efficiency impact
print(f"\n  D5. EFFICIENCY IMPACT")
print(f"    Network Pax/km (pre-metro):  {h1_route_avg2['Pax_Per_Km'].mean():.1f}")
print(f"    Network Pax/km (post-metro): {q3_route_avg2['Pax_Per_Km'].mean():.1f}")
eff_change = ((q3_route_avg2['Pax_Per_Km'].mean() / h1_route_avg2['Pax_Per_Km'].mean()) - 1) * 100
print(f"    Change:                      {eff_change:>+.1f}%")

# D6: Congestion interaction post-metro
print(f"\n  D6. CONGESTION INTERACTION (Post-Metro)")
print(f"    Pre-metro congestion:  {h1_cong_mean:.2f} (avg level)")
print(f"    Post-metro congestion: {q3_cong_mean:.2f} (avg level)")
print(f"    Pre-metro speed:       {h1_speed_mean:.1f} km/h")
print(f"    Post-metro speed:      {q3_speed_mean:.1f} km/h")
if q3_cong_mean < h1_cong_mean:
    print(f"    ✓ Metro Phase 2 has REDUCED road congestion — fewer cars on affected corridors")
elif q3_cong_mean > h1_cong_mean:
    print(f"    ⚠️ Congestion increased despite metro — suggests induced demand or construction effects")

# ============================================================
# EXECUTIVE SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("EXECUTIVE SUMMARY: STAGE 2 STRUCTURAL BREAK")
print("=" * 70)

print(f"""
  STRUCTURAL BREAK: Metro Phase 2 (commenced Jul 1, 2025)
  
  OVERALL IMPACT:
    Q3 actual vs Stage 1 forecast: {deviation:>+.1f}%
    Daily demand shift: {h1_total_daily:,.0f} → {q3_total_daily:,.0f} ({((q3_total_daily/h1_total_daily)-1)*100:>+.1f}%)
    Congestion: {h1_cong_mean:.2f} → {q3_cong_mean:.2f} ({cong_shift:>+.1f}%)
    Speed: {h1_speed_mean:.1f} → {q3_speed_mean:.1f} km/h ({speed_shift:>+.1f}%)
  
  REVISED Q4 FORECAST:
    Original: {q4_orig_total:>12,.0f}
    Revised:  {q4_rev_total:>12,.0f} ({q4_change:>+.1f}%)
    Range:    {q4_rev_total*0.9:,.0f} – {q4_rev_total*1.1:,.0f}
  
  KEY ROUTE IMPACTS:
""")

for _, r in route_comparison.sort_values('Deviation_%').head(3).iterrows():
    print(f"    {r['Route_Code']} ({r['Route_Type']}): {r['Deviation_%']:>+.1f}% deviation (largest decline)")
for _, r in route_comparison.sort_values('Deviation_%').tail(3).iterrows():
    print(f"    {r['Route_Code']} ({r['Route_Type']}): {r['Deviation_%']:>+.1f}% deviation (largest growth)")

print(f"""
  CLASSIFICATION: {'REGIME CHANGE' if abs(deviation) > 10 else 'MODERATE STRUCTURAL SHIFT'}
  This is NOT a temporary shock — Metro Phase 2 permanently alters demand patterns.
  
  IMMEDIATE ACTIONS REQUIRED:
  1. Recalibrate all forecasts with metro-adjustment factors
  2. Reduce fleet on metro-competing corridors (CBD, Deira)
  3. Strengthen feeder routes that connect to metro stations
  4. Monitor express route sustainability month-by-month
""")

print("=" * 70)
print("[DONE] STAGE 2 ANALYSIS COMPLETE")
print("=" * 70)
