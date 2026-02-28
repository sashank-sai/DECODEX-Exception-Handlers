"""
DECODE X 2026 - Stage 1: Corridor Overload & Capacity Waste Analysis
=====================================================================
Deep-dive into which corridors are overloaded, which have wasted capacity,
and where stop-level bottlenecks exist.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r'c:\Users\asus\Desktop\decodex'

# ============================================================
# 1. LOAD DATA
# ============================================================
print("=" * 70)
print("CORRIDOR OVERLOAD & CAPACITY WASTE ANALYSIS")
print("=" * 70)

master_df = pd.read_csv(f'{DATA_DIR}/master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])
forecast_df = pd.read_csv(f'{DATA_DIR}/forecast_h2_2025.csv')
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])
routes_df = pd.read_csv(f'{DATA_DIR}/Bus_Routes.csv')
mapping_df = pd.read_csv(f'{DATA_DIR}/Route_Stop_Mapping.csv')

print(f"  Master: {len(master_df):,} rows | Forecast: {len(forecast_df):,} rows")

# ============================================================
# 2. ROUTE-LEVEL EFFICIENCY METRICS
# ============================================================
print("\n" + "=" * 70)
print("SECTION A: ROUTE EFFICIENCY SCORECARD")
print("=" * 70)

# Use 2025 H1 data as the most recent actuals
recent = master_df[master_df['Date'] >= '2025-01-01'].copy()

route_metrics = recent.groupby(['Route_ID', 'Route_Code', 'Route_Type']).agg({
    'Total_Pax': ['sum', 'mean', 'std'],
    'Boarding_Count': 'sum',
    'Alighting_Count': 'sum',
    'Congestion_Level': 'mean',
    'Avg_Speed_kmph': 'mean',
    'Route_Length_km': 'first',
    'Avg_Travel_Time_Min': 'first',
    'Dwell_Time_Min': 'mean'
}).reset_index()

route_metrics.columns = [
    'Route_ID', 'Route_Code', 'Route_Type',
    'Total_Pax', 'Avg_Daily_Pax', 'Pax_StdDev',
    'Total_Board', 'Total_Alight',
    'Avg_Congestion', 'Avg_Speed',
    'Route_Length_km', 'Avg_Travel_Time',
    'Avg_Dwell_Time'
]

# Derived metrics
num_stops = mapping_df.groupby('Route_ID')['Stop_ID'].count().reset_index()
num_stops.columns = ['Route_ID', 'Num_Stops']
route_metrics = route_metrics.merge(num_stops, on='Route_ID')

# Pax per km (density)
route_metrics['Pax_Per_Km'] = route_metrics['Avg_Daily_Pax'] / route_metrics['Route_Length_km']
# Pax per stop
route_metrics['Pax_Per_Stop'] = route_metrics['Avg_Daily_Pax'] / route_metrics['Num_Stops']
# Coefficient of variation (demand volatility)
route_metrics['Demand_CV'] = route_metrics['Pax_StdDev'] / route_metrics['Avg_Daily_Pax']
# Effective speed (accounting for dwell time)
total_dwell = mapping_df.groupby('Route_ID')['Dwell_Time_Min'].sum().reset_index()
total_dwell.columns = ['Route_ID', 'Total_Route_Dwell']
route_metrics = route_metrics.merge(total_dwell, on='Route_ID')
route_metrics['Effective_Speed'] = route_metrics['Route_Length_km'] / (route_metrics['Avg_Travel_Time'] / 60)
# Board-to-Alight ratio (indicates directional imbalance)
route_metrics['Board_Alight_Ratio'] = route_metrics['Total_Board'] / route_metrics['Total_Alight']

route_metrics = route_metrics.sort_values('Avg_Daily_Pax', ascending=False)

print(f"\n{'Route':<8} {'Type':<12} {'Avg_Pax':>8} {'Pax/km':>8} {'Pax/Stop':>9} "
      f"{'CV':>6} {'Speed':>6} {'Stops':>6} {'B/A':>5}")
print("-" * 75)
for _, r in route_metrics.iterrows():
    print(f"  {r['Route_Code']:<6} {r['Route_Type']:<12} {r['Avg_Daily_Pax']:>7,.0f} "
          f"{r['Pax_Per_Km']:>7.1f} {r['Pax_Per_Stop']:>8.1f} "
          f"{r['Demand_CV']:>5.2f} {r['Effective_Speed']:>5.1f} "
          f"{r['Num_Stops']:>5d} {r['Board_Alight_Ratio']:>5.2f}")

# ============================================================
# 3. OVERLOAD DETECTION
# ============================================================
print("\n" + "=" * 70)
print("SECTION B: OVERLOADED CORRIDORS (DEMAND > CAPACITY)")
print("=" * 70)

# Define "overloaded" as routes where:
# 1. Pax/km is in the top quartile
# 2. Demand volatility (CV) is low (consistently high, not just spikes)
# 3. Forecast shows continued growth

pax_km_threshold = route_metrics['Pax_Per_Km'].quantile(0.75)
print(f"\n  Pax/km threshold (P75): {pax_km_threshold:.1f}")

# H2 2025 forecast growth per route
forecast_growth = forecast_df.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].mean().reset_index()
forecast_growth.columns = ['Route_Code', 'Route_Type', 'Forecast_Avg_Pax']

h2_2024 = master_df[(master_df['Date'] >= '2024-07-01') & (master_df['Date'] <= '2024-12-31')]
hist_avg = h2_2024.groupby(['Route_Code', 'Route_Type']).agg({'Total_Pax': 'sum'}).reset_index()
hist_days = h2_2024['Date'].nunique()
hist_avg['Hist_Daily_Avg'] = hist_avg['Total_Pax'] / hist_days
hist_avg = hist_avg[['Route_Code', 'Route_Type', 'Hist_Daily_Avg']]

growth_df = forecast_growth.merge(hist_avg, on=['Route_Code', 'Route_Type'])
growth_df['Growth_Pct'] = (growth_df['Forecast_Avg_Pax'] / growth_df['Hist_Daily_Avg'] - 1) * 100

# Combine into risk score
risk_df = route_metrics[['Route_Code', 'Route_Type', 'Avg_Daily_Pax', 'Pax_Per_Km', 
                          'Pax_Per_Stop', 'Demand_CV', 'Effective_Speed', 'Num_Stops',
                          'Route_Length_km']].merge(
    growth_df[['Route_Code', 'Growth_Pct', 'Forecast_Avg_Pax']], on='Route_Code'
)

# Normalize metrics for scoring (0-100)
for col in ['Pax_Per_Km', 'Pax_Per_Stop', 'Growth_Pct']:
    min_val = risk_df[col].min()
    max_val = risk_df[col].max()
    risk_df[f'{col}_Score'] = (risk_df[col] - min_val) / (max_val - min_val) * 100

# Overload risk score: weighted combination
risk_df['Overload_Risk'] = (
    0.40 * risk_df['Pax_Per_Km_Score'] +
    0.30 * risk_df['Pax_Per_Stop_Score'] +
    0.30 * risk_df['Growth_Pct_Score']
).round(1)

risk_df = risk_df.sort_values('Overload_Risk', ascending=False)

print(f"\n  OVERLOAD RISK RANKING (Higher = More at Risk)")
print(f"  {'Route':<8} {'Type':<12} {'Risk':>6} {'Pax/km':>8} {'Pax/Stp':>8} {'Growth':>8} {'Fcast_Avg':>10}")
print("  " + "-" * 65)
for _, r in risk_df.iterrows():
    flag = " <<<" if r['Overload_Risk'] >= 70 else (" !!" if r['Overload_Risk'] >= 50 else "")
    print(f"  {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Overload_Risk']:>5.1f} "
          f"{r['Pax_Per_Km']:>7.1f} {r['Pax_Per_Stop']:>7.1f} "
          f"{r['Growth_Pct']:>+6.1f}% {r['Forecast_Avg_Pax']:>9,.0f}{flag}")

# ============================================================
# 4. CAPACITY WASTE DETECTION
# ============================================================
print("\n" + "=" * 70)
print("SECTION C: UNDERUTILIZED CAPACITY (WASTE)")
print("=" * 70)

# Identify routes with LOW pax/km but HIGH infrastructure (long routes, many stops)
waste_df = risk_df.copy()
waste_df['Waste_Score'] = (
    100 - waste_df['Overload_Risk']  # inverse of overload = waste potential
).round(1)
waste_df = waste_df.sort_values('Waste_Score', ascending=False)

print(f"\n  CAPACITY WASTE RANKING (Higher = More Underutilized)")
print(f"  {'Route':<8} {'Type':<12} {'Waste':>6} {'Pax/km':>8} {'Length':>8} {'Stops':>6} {'Avg_Pax':>8}")
print("  " + "-" * 60)
for _, r in waste_df.iterrows():
    flag = " <<<" if r['Waste_Score'] >= 70 else (" !!" if r['Waste_Score'] >= 50 else "")
    print(f"  {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Waste_Score']:>5.1f} "
          f"{r['Pax_Per_Km']:>7.1f} {r['Route_Length_km']:>7.1f} "
          f"{r['Num_Stops']:>5d} {r['Avg_Daily_Pax']:>7,.0f}{flag}")

# ============================================================
# 5. STOP-LEVEL BOTTLENECK ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("SECTION D: STOP-LEVEL BOTTLENECKS")
print("=" * 70)

# Find stops that are disproportionately loaded relative to their route
stop_analysis = recent.groupby(['Route_ID', 'Route_Code', 'Route_Type', 
                                 'Stop_ID', 'Stop_Name', 'Zone', 'Stop_Type']).agg({
    'Total_Pax': ['sum', 'mean'],
    'Boarding_Count': 'mean',
    'Alighting_Count': 'mean',
    'Dwell_Time_Min': 'first',
    'Stop_Sequence': 'first'
}).reset_index()

stop_analysis.columns = ['Route_ID', 'Route_Code', 'Route_Type',
                          'Stop_ID', 'Stop_Name', 'Zone', 'Stop_Type',
                          'Total_Pax', 'Avg_Pax', 'Avg_Board', 'Avg_Alight',
                          'Dwell_Time', 'Sequence']

# Calculate each stop's share of its route's total
route_totals = stop_analysis.groupby('Route_ID')['Total_Pax'].sum().reset_index()
route_totals.columns = ['Route_ID', 'Route_Total_Pax']
stop_analysis = stop_analysis.merge(route_totals, on='Route_ID')
stop_analysis['Pax_Share'] = stop_analysis['Total_Pax'] / stop_analysis['Route_Total_Pax'] * 100

# Expected share (if evenly distributed)
route_stop_counts = stop_analysis.groupby('Route_ID')['Stop_ID'].count().reset_index()
route_stop_counts.columns = ['Route_ID', 'Route_Stop_Count']
stop_analysis = stop_analysis.merge(route_stop_counts, on='Route_ID')
stop_analysis['Expected_Share'] = 100 / stop_analysis['Route_Stop_Count']
stop_analysis['Share_Ratio'] = stop_analysis['Pax_Share'] / stop_analysis['Expected_Share']

# Pax per minute of dwell (throughput pressure)
stop_analysis['Pax_Per_Dwell_Min'] = stop_analysis['Avg_Pax'] / stop_analysis['Dwell_Time']

# Board-Alight imbalance at stop level
stop_analysis['Net_Flow'] = stop_analysis['Avg_Board'] - stop_analysis['Avg_Alight']
stop_analysis['Flow_Direction'] = stop_analysis['Net_Flow'].apply(
    lambda x: 'NET_BOARDING' if x > 10 else ('NET_ALIGHTING' if x < -10 else 'BALANCED')
)

# Top bottleneck stops (highest share ratio = disproportionately loaded)
bottlenecks = stop_analysis.sort_values('Share_Ratio', ascending=False).head(20)

print(f"\n  TOP 20 BOTTLENECK STOPS (Disproportionate Load)")
print(f"  {'Stop':<8} {'Route':<6} {'Zone':<25} {'Type':<12} {'Share':>6} {'Ratio':>6} "
      f"{'Avg_Pax':>8} {'Pax/DwMin':>10} {'Flow':<14}")
print("  " + "-" * 100)
for _, s in bottlenecks.iterrows():
    print(f"  {s['Stop_ID']:<8} {s['Route_Code']:<6} {s['Zone']:<25} {s['Stop_Type']:<12} "
          f"{s['Pax_Share']:>5.1f}% {s['Share_Ratio']:>5.2f}x "
          f"{s['Avg_Pax']:>7,.0f} {s['Pax_Per_Dwell_Min']:>9.0f} {s['Flow_Direction']:<14}")

# ============================================================
# 6. ZONE-LEVEL CORRIDOR PRESSURE
# ============================================================
print("\n" + "=" * 70)
print("SECTION E: ZONE CORRIDOR PRESSURE MATRIX")
print("=" * 70)

zone_pressure = recent.groupby('Zone').agg({
    'Total_Pax': ['sum', 'mean'],
    'Boarding_Count': 'sum',
    'Alighting_Count': 'sum',
    'Congestion_Level': 'mean',
    'Avg_Speed_kmph': 'mean'
}).reset_index()

zone_pressure.columns = ['Zone', 'Total_Pax', 'Avg_Pax', 'Total_Board', 
                           'Total_Alight', 'Avg_Congestion', 'Avg_Speed']

zone_pressure['Net_Flow'] = zone_pressure['Total_Board'] - zone_pressure['Total_Alight']
zone_pressure['Flow_Dir'] = zone_pressure['Net_Flow'].apply(
    lambda x: 'GENERATOR' if x > 0 else 'ATTRACTOR'
)

# Stops per zone
stops_per_zone = recent.groupby('Zone')['Stop_ID'].nunique().reset_index()
stops_per_zone.columns = ['Zone', 'Num_Stops']
zone_pressure = zone_pressure.merge(stops_per_zone, on='Zone')
zone_pressure['Pax_Per_Stop'] = zone_pressure['Avg_Pax'] / zone_pressure['Num_Stops'] * zone_pressure['Num_Stops']

zone_pressure = zone_pressure.sort_values('Total_Pax', ascending=False)

print(f"\n  {'Zone':<30} {'Total_Pax':>12} {'Avg_Pax':>8} {'Cong':>5} {'Speed':>6} "
      f"{'Net_Flow':>10} {'Role':<12} {'Stops':>6}")
print("  " + "-" * 95)
for _, z in zone_pressure.iterrows():
    print(f"  {z['Zone']:<30} {z['Total_Pax']:>11,.0f} {z['Avg_Pax']:>7.0f} "
          f"{z['Avg_Congestion']:>4.1f} {z['Avg_Speed']:>5.1f} "
          f"{z['Net_Flow']:>+9,.0f} {z['Flow_Dir']:<12} {z['Num_Stops']:>5d}")

# ============================================================
# 7. TIME-OF-WEEK OVERLOAD PATTERNS
# ============================================================
print("\n" + "=" * 70)
print("SECTION F: DAY-OF-WEEK DEMAND PATTERNS (H1 2025)")
print("=" * 70)

dow_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 
             4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
dow_route = recent.groupby(['DayOfWeek', 'Route_Code', 'Route_Type'])['Total_Pax'].mean().reset_index()
dow_route['DayName'] = dow_route['DayOfWeek'].map(dow_names)

# Find which route-day combos have the highest demand relative to that route's average
route_avgs = dow_route.groupby('Route_Code')['Total_Pax'].mean().reset_index()
route_avgs.columns = ['Route_Code', 'Route_Avg']
dow_route = dow_route.merge(route_avgs, on='Route_Code')
dow_route['Demand_Index'] = (dow_route['Total_Pax'] / dow_route['Route_Avg'] * 100).round(1)

# Peak demand days per route
print(f"\n  Peak Day by Route (Index: 100 = route average)")
print(f"  {'Route':<8} {'Type':<12} {'Peak_Day':<12} {'Peak_Demand':>12} {'Index':>7}")
print("  " + "-" * 55)
for route_code in sorted(dow_route['Route_Code'].unique()):
    rd = dow_route[dow_route['Route_Code'] == route_code]
    peak = rd.loc[rd['Total_Pax'].idxmax()]
    trough = rd.loc[rd['Total_Pax'].idxmin()]
    print(f"  {route_code:<8} {peak['Route_Type']:<12} {peak['DayName']:<12} "
          f"{peak['Total_Pax']:>11,.0f} {peak['Demand_Index']:>6.1f}")

# Weekend vs Weekday demand ratio per route
print(f"\n  Weekend/Weekday Ratio by Route")
print(f"  {'Route':<8} {'Type':<12} {'Weekday_Avg':>12} {'Weekend_Avg':>12} {'Ratio':>7}")
print("  " + "-" * 55)
for route_code in sorted(dow_route['Route_Code'].unique()):
    rd = dow_route[dow_route['Route_Code'] == route_code]
    weekday_avg = rd[~rd['DayOfWeek'].isin([4, 5])]['Total_Pax'].mean()
    weekend_avg = rd[rd['DayOfWeek'].isin([4, 5])]['Total_Pax'].mean()
    ratio = weekend_avg / weekday_avg if weekday_avg > 0 else 0
    rtype = rd['Route_Type'].iloc[0]
    print(f"  {route_code:<8} {rtype:<12} {weekday_avg:>11,.0f} {weekend_avg:>11,.0f} {ratio:>6.2f}")

# ============================================================
# 8. ROUTE SEGMENT LOAD PROFILE
# ============================================================
print("\n" + "=" * 70)
print("SECTION G: ROUTE LOAD PROFILE (Cumulative Boarding Pattern)")
print("=" * 70)

# For each route, show how boarding accumulates along the stop sequence
print(f"\n  Shows board/alight pattern along the route to find where buses fill up")

for route_id in sorted(recent['Route_ID'].unique()):
    rd = recent[recent['Route_ID'] == route_id].groupby(['Stop_Sequence', 'Stop_ID', 'Stop_Name', 'Zone']).agg({
        'Boarding_Count': 'mean',
        'Alighting_Count': 'mean',
        'Total_Pax': 'mean'
    }).reset_index().sort_values('Stop_Sequence')
    
    route_code = recent[recent['Route_ID'] == route_id]['Route_Code'].iloc[0]
    route_type = recent[recent['Route_ID'] == route_id]['Route_Type'].iloc[0]
    
    # Cumulative on-board estimate
    rd['Cum_Board'] = rd['Boarding_Count'].cumsum()
    rd['Cum_Alight'] = rd['Alighting_Count'].cumsum()
    rd['Est_Onboard'] = rd['Cum_Board'] - rd['Cum_Alight']
    
    peak_onboard = rd['Est_Onboard'].max()
    peak_seq = rd.loc[rd['Est_Onboard'].idxmax(), 'Stop_Sequence']
    peak_zone = rd.loc[rd['Est_Onboard'].idxmax(), 'Zone']
    
    print(f"\n  Route {route_code} ({route_type}) - Peak onboard: {peak_onboard:.0f} pax at stop #{peak_seq} ({peak_zone})")
    print(f"  {'Seq':>4} {'Board':>7} {'Alight':>7} {'Onboard':>8} {'Zone':<25} {'Bar'}")
    for _, stop in rd.iterrows():
        bar_len = int(stop['Est_Onboard'] / peak_onboard * 30) if peak_onboard > 0 else 0
        bar = '#' * bar_len
        print(f"  {stop['Stop_Sequence']:>4} {stop['Boarding_Count']:>6.0f} {stop['Alighting_Count']:>6.0f} "
              f"{stop['Est_Onboard']:>7.0f} {stop['Zone']:<25} {bar}")

# ============================================================
# 9. EXECUTIVE SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("EXECUTIVE SUMMARY: OVERLOAD & WASTE FINDINGS")
print("=" * 70)

# Top 3 overloaded
top_overload = risk_df.head(3)
print("\n  TOP 3 OVERLOADED CORRIDORS:")
for i, (_, r) in enumerate(top_overload.iterrows(), 1):
    print(f"    {i}. Route {r['Route_Code']} ({r['Route_Type']}): "
          f"Risk={r['Overload_Risk']:.0f}/100, Pax/km={r['Pax_Per_Km']:.1f}, "
          f"Forecast growth={r['Growth_Pct']:+.1f}%")

# Top 3 underutilized
top_waste = waste_df.head(3)
print("\n  TOP 3 UNDERUTILIZED CORRIDORS:")
for i, (_, r) in enumerate(top_waste.iterrows(), 1):
    print(f"    {i}. Route {r['Route_Code']} ({r['Route_Type']}): "
          f"Waste={r['Waste_Score']:.0f}/100, Pax/km={r['Pax_Per_Km']:.1f}, "
          f"Length={r['Route_Length_km']:.1f} km")

# Top 5 bottleneck stops
top_bottleneck = bottlenecks.head(5)
print("\n  TOP 5 BOTTLENECK STOPS:")
for i, (_, s) in enumerate(top_bottleneck.iterrows(), 1):
    print(f"    {i}. Stop {s['Stop_ID']} on Route {s['Route_Code']} ({s['Zone']}): "
          f"{s['Share_Ratio']:.2f}x expected load, {s['Pax_Per_Dwell_Min']:.0f} pax/dwell-min")

# Zone generators vs attractors
print("\n  ZONE FLOW CLASSIFICATION:")
for _, z in zone_pressure.iterrows():
    print(f"    {z['Zone']:<30} -> {z['Flow_Dir']} (net={z['Net_Flow']:+,.0f})")

print("\n" + "=" * 70)
print("[DONE] CORRIDOR ANALYSIS COMPLETE")
print("=" * 70)
