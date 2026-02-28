"""
DECODE X 2026 - Stage 1: Fleet Reallocation & Headway Optimization
===================================================================
Concrete proposals for shifting fleet capacity from underutilized to
overloaded corridors, with headway adjustments by time-of-week.

Uses findings from corridor analysis:
  - Overloaded: X28 (89), X11 (68), X66 (60), C02 (53) — all Express
  - Underutilized: F18 (88), E16 (75), F12 (75), C04 (74)
  - Bottleneck zone: Coastal_Marina
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
print("FLEET REALLOCATION & HEADWAY OPTIMIZATION PROPOSALS")
print("=" * 70)

master_df = pd.read_csv(f'{DATA_DIR}/master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])
forecast_df = pd.read_csv(f'{DATA_DIR}/forecast_h2_2025.csv')
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])
routes_df = pd.read_csv(f'{DATA_DIR}/Bus_Routes.csv')
mapping_df = pd.read_csv(f'{DATA_DIR}/Route_Stop_Mapping.csv')

# Recent data (H1 2025)
recent = master_df[master_df['Date'] >= '2025-01-01'].copy()

# ============================================================
# 2. CURRENT SERVICE PROFILE (BASELINE)
# ============================================================
print("\n" + "=" * 70)
print("SECTION 1: CURRENT SERVICE PROFILE (BASELINE)")
print("=" * 70)

# Calculate current implied headway and fleet size
# Assumptions based on typical Dubai RTA operations:
OPERATING_HOURS = 18  # 5 AM to 11 PM
BUS_CAPACITY = 60     # standard articulated bus
ASSUMED_FLEET_TOTAL = 50  # total fleet across all routes

# For each route, estimate current service level
route_profile = routes_df.copy()
num_stops = mapping_df.groupby('Route_ID')['Stop_ID'].count().reset_index()
num_stops.columns = ['Route_ID', 'Num_Stops']
total_dwell = mapping_df.groupby('Route_ID')['Dwell_Time_Min'].sum().reset_index()
total_dwell.columns = ['Route_ID', 'Total_Dwell_Min']
route_profile = route_profile.merge(num_stops, on='Route_ID').merge(total_dwell, on='Route_ID')

# Round trip time = 2 * (Avg_Travel_Time + buffer)
route_profile['Round_Trip_Min'] = 2 * (route_profile['Avg_Travel_Time_Min'] + 5)  # 5 min turnaround

# Daily demand from H1 2025
daily_demand = recent.groupby(['Route_ID']).agg({
    'Total_Pax': 'mean',
    'Boarding_Count': 'mean',
    'Alighting_Count': 'mean'
}).reset_index()
daily_demand.columns = ['Route_ID', 'Daily_Pax_Avg', 'Daily_Board_Avg', 'Daily_Alight_Avg']
# These are per-stop averages, multiply by number of stops is wrong
# Instead, get the daily route total directly
daily_route_total = recent.groupby(['Date', 'Route_ID'])['Total_Pax'].sum().reset_index()
daily_route_avg = daily_route_total.groupby('Route_ID')['Total_Pax'].mean().reset_index()
daily_route_avg.columns = ['Route_ID', 'Daily_Total_Pax']

route_profile = route_profile.merge(daily_route_avg, on='Route_ID')

# Peak hour demand (assume peak hours handle 25% of daily in 4 hours = 6.25% hourly)
route_profile['Peak_Hourly_Pax'] = route_profile['Daily_Total_Pax'] * 0.0625

# Required trips per hour to meet peak demand
route_profile['Required_Trips_Per_Hr'] = np.ceil(
    route_profile['Peak_Hourly_Pax'] / BUS_CAPACITY
)

# Required fleet per route (buses needed = trips_per_hr * round_trip_hrs)
route_profile['Round_Trip_Hr'] = route_profile['Round_Trip_Min'] / 60
route_profile['Required_Fleet'] = np.ceil(
    route_profile['Required_Trips_Per_Hr'] * route_profile['Round_Trip_Hr']
)

# Current headway (minutes between buses)
route_profile['Current_Headway_Min'] = np.where(
    route_profile['Required_Trips_Per_Hr'] > 0,
    60 / route_profile['Required_Trips_Per_Hr'],
    60
)

# Load factor (what pct of capacity is used)
route_profile['Peak_Load_Factor'] = (
    route_profile['Peak_Hourly_Pax'] / 
    (route_profile['Required_Trips_Per_Hr'] * BUS_CAPACITY)
)

route_profile = route_profile.sort_values('Daily_Total_Pax', ascending=False)

print(f"\n  Assumptions: {OPERATING_HOURS}h operating day, {BUS_CAPACITY}-pax bus capacity")
print(f"\n  {'Route':<8} {'Type':<12} {'Daily_Pax':>10} {'Peak_Hr_Pax':>12} "
      f"{'Trips/Hr':>9} {'Fleet':>6} {'Headway':>8} {'Load%':>7}")
print("  " + "-" * 78)
total_fleet = 0
for _, r in route_profile.iterrows():
    total_fleet += r['Required_Fleet']
    print(f"  {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Daily_Total_Pax']:>9,.0f} "
          f"{r['Peak_Hourly_Pax']:>11,.0f} "
          f"{r['Required_Trips_Per_Hr']:>8.0f} {r['Required_Fleet']:>5.0f} "
          f"{r['Current_Headway_Min']:>7.1f}m {r['Peak_Load_Factor']:>6.0%}")

print(f"\n  Total fleet required (baseline): {total_fleet:.0f} buses")

# ============================================================
# 3. FORECAST-BASED FLEET REQUIREMENTS (H2 2025)
# ============================================================
print("\n" + "=" * 70)
print("SECTION 2: FORECAST-BASED FLEET REQUIREMENTS (H2 2025)")
print("=" * 70)

# H2 2025 daily averages per route
fcast_daily = forecast_df.groupby(['Route_Code', 'Route_ID', 'Route_Type'])['Forecast_Total_Pax'].mean().reset_index()
fcast_daily.columns = ['Route_Code', 'Route_ID', 'Route_Type', 'Fcast_Daily_Pax']

fcast_profile = fcast_daily.merge(
    route_profile[['Route_ID', 'Route_Code', 'Round_Trip_Min', 'Round_Trip_Hr', 
                    'Num_Stops', 'Route_Length_km', 'Daily_Total_Pax']],
    on=['Route_ID', 'Route_Code']
)

fcast_profile['Fcast_Peak_Hourly'] = fcast_profile['Fcast_Daily_Pax'] * 0.0625
fcast_profile['Fcast_Trips_Per_Hr'] = np.ceil(fcast_profile['Fcast_Peak_Hourly'] / BUS_CAPACITY)
fcast_profile['Fcast_Fleet'] = np.ceil(fcast_profile['Fcast_Trips_Per_Hr'] * fcast_profile['Round_Trip_Hr'])
fcast_profile['Fcast_Headway'] = np.where(
    fcast_profile['Fcast_Trips_Per_Hr'] > 0,
    60 / fcast_profile['Fcast_Trips_Per_Hr'],
    60
)
fcast_profile['Demand_Growth'] = (fcast_profile['Fcast_Daily_Pax'] / fcast_profile['Daily_Total_Pax'] - 1) * 100
fcast_profile['Fleet_Change'] = fcast_profile['Fcast_Fleet'] - route_profile.set_index('Route_ID').loc[fcast_profile['Route_ID']]['Required_Fleet'].values

fcast_profile = fcast_profile.sort_values('Fcast_Daily_Pax', ascending=False)

print(f"\n  {'Route':<8} {'Type':<12} {'Curr_Pax':>9} {'Fcast_Pax':>10} {'Growth':>8} "
      f"{'Curr_Fleet':>11} {'Fcast_Fleet':>12} {'Change':>7} {'Headway':>8}")
print("  " + "-" * 90)
total_fcast_fleet = 0
for _, r in fcast_profile.iterrows():
    curr_fleet = route_profile[route_profile['Route_ID'] == r['Route_ID']]['Required_Fleet'].values[0]
    total_fcast_fleet += r['Fcast_Fleet']
    change_str = f"+{r['Fleet_Change']:.0f}" if r['Fleet_Change'] >= 0 else f"{r['Fleet_Change']:.0f}"
    print(f"  {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Daily_Total_Pax']:>8,.0f} "
          f"{r['Fcast_Daily_Pax']:>9,.0f} {r['Demand_Growth']:>+6.1f}% "
          f"{curr_fleet:>10.0f} {r['Fcast_Fleet']:>11.0f} {change_str:>6} "
          f"{r['Fcast_Headway']:>7.1f}m")

print(f"\n  Total forecast fleet: {total_fcast_fleet:.0f} buses (vs {total_fleet:.0f} baseline)")
print(f"  Net additional buses needed: {total_fcast_fleet - total_fleet:.0f}")

# ============================================================
# 4. REALLOCATION PROPOSALS
# ============================================================
print("\n" + "=" * 70)
print("SECTION 3: FLEET REALLOCATION PROPOSALS")
print("=" * 70)

# Strategy: redistribute from underutilized to overloaded WITHOUT increasing total fleet
# Overloaded (need more): Express routes X28, X11, X66
# Underutilized (can give): F18, E16, F12, C04

# Build reallocation matrix
print("\n  STRATEGY: Budget-neutral reallocation (no new buses added)")
print("  Principle: Move buses from low Pax/km routes to high Pax/km routes\n")

# Current fleet allocation
current_fleet = route_profile[['Route_ID', 'Route_Code', 'Route_Type', 
                                 'Required_Fleet', 'Daily_Total_Pax',
                                 'Peak_Hourly_Pax', 'Current_Headway_Min',
                                 'Route_Length_km']].copy()
current_fleet.columns = ['Route_ID', 'Route_Code', 'Route_Type',
                          'Current_Fleet', 'Current_Pax', 'Peak_Hr_Pax',
                          'Current_Headway', 'Length_km']

# Pax per km per bus (efficiency metric)
current_fleet['Efficiency'] = current_fleet['Current_Pax'] / (
    current_fleet['Current_Fleet'] * current_fleet['Length_km']
)

# Calculate optimal redistribution
# Method: Allocate fleet proportional to Pax/km (demand density)
current_fleet['Pax_Per_Km'] = current_fleet['Current_Pax'] / current_fleet['Length_km']
total_pax_km = current_fleet['Pax_Per_Km'].sum()
current_fleet['Optimal_Share'] = current_fleet['Pax_Per_Km'] / total_pax_km
current_fleet['Optimal_Fleet'] = np.round(current_fleet['Optimal_Share'] * total_fleet)

# Ensure total matches
diff = total_fleet - current_fleet['Optimal_Fleet'].sum()
if diff != 0:
    # Add/subtract from highest demand route
    idx = current_fleet['Pax_Per_Km'].idxmax()
    current_fleet.loc[idx, 'Optimal_Fleet'] += diff

current_fleet['Fleet_Delta'] = current_fleet['Optimal_Fleet'] - current_fleet['Current_Fleet']

# Recalculate headway with new fleet
current_fleet['New_Trips_Per_Hr'] = current_fleet['Optimal_Fleet'] / (
    route_profile.set_index('Route_ID').loc[current_fleet['Route_ID']]['Round_Trip_Hr'].values
)
current_fleet['New_Headway'] = np.where(
    current_fleet['New_Trips_Per_Hr'] > 0,
    60 / current_fleet['New_Trips_Per_Hr'],
    60
)

# New load factor
current_fleet['New_Load_Factor'] = current_fleet['Peak_Hr_Pax'] / (
    current_fleet['New_Trips_Per_Hr'] * BUS_CAPACITY
)

current_fleet = current_fleet.sort_values('Fleet_Delta', ascending=False)

print(f"  {'Route':<8} {'Type':<12} {'Curr':>5} {'Opt':>5} {'Delta':>6} "
      f"{'Curr_Hdwy':>10} {'New_Hdwy':>9} {'New_Load':>9} {'Action'}")
print("  " + "-" * 85)

donors = []
receivers = []
for _, r in current_fleet.iterrows():
    delta_str = f"+{r['Fleet_Delta']:.0f}" if r['Fleet_Delta'] >= 0 else f"{r['Fleet_Delta']:.0f}"
    if r['Fleet_Delta'] > 0:
        action = "<<< ADD BUSES"
        receivers.append(r)
    elif r['Fleet_Delta'] < 0:
        action = "    REDUCE --->"
        donors.append(r)
    else:
        action = "    No change"
    
    print(f"  {r['Route_Code']:<8} {r['Route_Type']:<12} {r['Current_Fleet']:>4.0f} "
          f"{r['Optimal_Fleet']:>4.0f} {delta_str:>5} "
          f"{r['Current_Headway']:>9.1f}m {r['New_Headway']:>8.1f}m "
          f"{r['New_Load_Factor']:>8.0%} {action}")

print(f"\n  Total fleet unchanged: {current_fleet['Optimal_Fleet'].sum():.0f} buses")
print(f"  Buses redistributed: {current_fleet[current_fleet['Fleet_Delta'] > 0]['Fleet_Delta'].sum():.0f}")

# ============================================================
# 5. HEADWAY MODIFICATION SCHEDULE
# ============================================================
print("\n" + "=" * 70)
print("SECTION 4: HEADWAY MODIFICATION SCHEDULE")
print("=" * 70)

print("\n  Time-of-week headway recommendations (in minutes)")
print("  Based on day-of-week demand patterns from H1 2025 data\n")

# Calculate relative demand by DayOfWeek for each route
dow_names = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
recent['DayOfWeek'] = recent['Date'].dt.dayofweek

dow_demand = recent.groupby(['DayOfWeek', 'Route_ID', 'Route_Code']).agg({
    'Total_Pax': 'sum'
}).reset_index()
# Average across dates
dow_days = recent.groupby('DayOfWeek')['Date'].nunique().reset_index()
dow_days.columns = ['DayOfWeek', 'NumDays']
dow_demand = dow_demand.merge(dow_days, on='DayOfWeek')
dow_demand['Daily_Avg'] = dow_demand['Total_Pax'] / dow_demand['NumDays']

# Get route average across all days
route_overall = dow_demand.groupby('Route_Code')['Daily_Avg'].mean().reset_index()
route_overall.columns = ['Route_Code', 'Overall_Avg']
dow_demand = dow_demand.merge(route_overall, on='Route_Code')
dow_demand['Demand_Index'] = dow_demand['Daily_Avg'] / dow_demand['Overall_Avg']

# Convert to headway: base headway / demand_index
# Higher demand = lower headway (more frequent)
for route_code in sorted(current_fleet['Route_Code'].unique()):
    rf = current_fleet[current_fleet['Route_Code'] == route_code].iloc[0]
    base_headway = rf['New_Headway']
    
    rd = dow_demand[dow_demand['Route_Code'] == route_code].sort_values('DayOfWeek')
    
    print(f"  Route {route_code} ({rf['Route_Type']}) - Base headway: {base_headway:.1f} min")
    print(f"    {'Day':<6} {'Demand_Idx':>11} {'Peak_Headway':>13} {'Off-Peak_Headway':>17}")
    for _, d in rd.iterrows():
        peak_hw = base_headway / d['Demand_Index']
        offpeak_hw = peak_hw * 1.5  # off-peak is 50% less frequent
        dow = dow_names[d['DayOfWeek']]
        print(f"    {dow:<6} {d['Demand_Index']:>10.2f} {peak_hw:>12.0f} min {offpeak_hw:>15.0f} min")
    print()

# ============================================================
# 6. SEASONAL ADJUSTMENT RECOMMENDATIONS
# ============================================================
print("=" * 70)
print("SECTION 5: SEASONAL FLEET ADJUSTMENT")
print("=" * 70)

# Winter needs more, summer needs less
def dubai_season(m):
    if m in [11, 12, 1, 2, 3]: return 'Winter_Peak'
    elif m in [6, 7, 8]: return 'Summer_Moderate'
    else: return 'Shoulder'

recent['Season'] = recent['Month'].apply(dubai_season) if 'Month' in recent.columns else recent['Date'].dt.month.apply(dubai_season)

season_demand = recent.groupby(['Season', 'Route_ID', 'Route_Code', 'Route_Type']).agg({
    'Total_Pax': 'sum'
}).reset_index()
season_days = recent.groupby('Season')['Date'].nunique().reset_index()
season_days.columns = ['Season', 'NumDays']
season_demand = season_demand.merge(season_days, on='Season')
season_demand['Daily_Avg'] = season_demand['Total_Pax'] / season_demand['NumDays']

overall_avg = season_demand.groupby('Route_Code')['Daily_Avg'].mean().reset_index()
overall_avg.columns = ['Route_Code', 'Overall_Avg']
season_demand = season_demand.merge(overall_avg, on='Route_Code')
season_demand['Season_Factor'] = season_demand['Daily_Avg'] / season_demand['Overall_Avg']

print(f"\n  Fleet multiplier by season (1.0 = baseline)")
print(f"\n  {'Route':<8} {'Type':<12} {'Winter':>8} {'Shoulder':>10} {'Summer':>8} {'Action'}")
print("  " + "-" * 65)

for route_code in sorted(season_demand['Route_Code'].unique()):
    rd = season_demand[season_demand['Route_Code'] == route_code]
    rtype = rd['Route_Type'].iloc[0]
    winter = rd[rd['Season'] == 'Winter_Peak']['Season_Factor'].values
    shoulder = rd[rd['Season'] == 'Shoulder']['Season_Factor'].values
    summer = rd[rd['Season'] == 'Summer_Moderate']['Season_Factor'].values
    
    w = winter[0] if len(winter) > 0 else 1.0
    sh = shoulder[0] if len(shoulder) > 0 else 1.0
    su = summer[0] if len(summer) > 0 else 1.0
    
    swing = (w - su) * 100
    action = f"Swing {swing:.0f}% capacity winter->summer"
    
    print(f"  {route_code:<8} {rtype:<12} {w:>7.2f}x {sh:>9.2f}x {su:>7.2f}x {action}")

# ============================================================
# 7. IMPACT ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("SECTION 6: EXPECTED IMPACT OF REALLOCATION")
print("=" * 70)

# Calculate improvement metrics
print(f"\n  BEFORE Reallocation:")
overload_before = current_fleet[current_fleet['Current_Headway'] > 15]['Route_Code'].tolist()
print(f"    Routes with headway > 15 min: {overload_before}")
avg_headway_before = current_fleet['Current_Headway'].mean()
print(f"    Average headway: {avg_headway_before:.1f} min")
headway_cv_before = current_fleet['Current_Headway'].std() / current_fleet['Current_Headway'].mean()
print(f"    Headway variation (CV): {headway_cv_before:.3f}")

print(f"\n  AFTER Reallocation:")
overload_after = current_fleet[current_fleet['New_Headway'] > 15]['Route_Code'].tolist()
print(f"    Routes with headway > 15 min: {overload_after}")
avg_headway_after = current_fleet['New_Headway'].mean()
print(f"    Average headway: {avg_headway_after:.1f} min")
headway_cv_after = current_fleet['New_Headway'].std() / current_fleet['New_Headway'].mean()
print(f"    Headway variation (CV): {headway_cv_after:.3f}")

print(f"\n  NET IMPROVEMENT:")
print(f"    Headway CV reduction: {(headway_cv_before - headway_cv_after)/headway_cv_before*100:.1f}% (more uniform service)")
print(f"    Fleet size: UNCHANGED ({total_fleet:.0f} buses)")
print(f"    High-demand routes get shorter headways")
print(f"    Low-demand routes extend headways modestly")

# ============================================================
# 8. EXECUTIVE RECOMMENDATION SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SECTION 7: EXECUTIVE RECOMMENDATIONS")
print("=" * 70)

print("""
  RECOMMENDATION 1: IMMEDIATE FLEET REALLOCATION (Budget-Neutral)
  ---------------------------------------------------------------
  Redistribute buses from underutilized Feeder/Intercity routes to
  overloaded Express routes. Net zero cost — same total fleet size.
  
  Key moves:""")
for _, r in current_fleet[current_fleet['Fleet_Delta'] != 0].sort_values('Fleet_Delta').iterrows():
    direction = "ADD" if r['Fleet_Delta'] > 0 else "REMOVE"
    print(f"    {direction} {abs(r['Fleet_Delta']):.0f} bus(es) {'to' if r['Fleet_Delta'] > 0 else 'from'} "
          f"Route {r['Route_Code']} ({r['Route_Type']})")

print("""
  RECOMMENDATION 2: TIME-VARIABLE HEADWAYS
  -----------------------------------------
  Implement split schedules: tighter headways on peak weekdays
  (Sun-Thu), relaxed headways on weekends (Fri-Sat). This achieves
  ~7-8% capacity gain on peak days without additional buses.
  
  Priority: Express routes X28, X11, X66 (highest overload risk)

  RECOMMENDATION 3: SEASONAL FLEET ROTATION
  ------------------------------------------
  Winter Peak (Nov-Mar): Deploy full fleet + request 10-15% surge
  Summer Moderate (Jun-Aug): Redeploy 10-15% of fleet to maintenance
  Swing range: ~18-20% capacity difference between seasons.
  
  RECOMMENDATION 4: COASTAL MARINA BOTTLENECK MITIGATION
  -------------------------------------------------------
  All top 20 bottleneck stops are in Coastal_Marina zone.
  Options:
    a) Increase dwell time at Stops 31, 33, 43, 52 (allow faster boarding)
    b) Add express bypass services skipping intermediate stops
    c) Deploy larger-capacity buses on routes C01, C03, C04 through this zone
  
  RECOMMENDATION 5: MONITOR & PREPARE FOR SHOCK
  -----------------------------------------------
  The 7 PM shock may introduce:
    - Budget constraints (making Rec 1 even more critical)
    - Demand shifts (requiring re-calibration of Rec 3)
    - New routes or service requirements
  Keep the model flexible for rapid re-optimization.
""")

print("=" * 70)
print("[DONE] FLEET REALLOCATION ANALYSIS COMPLETE")
print("=" * 70)
