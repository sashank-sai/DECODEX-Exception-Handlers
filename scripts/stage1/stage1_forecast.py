"""
DECODE X 2026 - Stage 1: Baseline Demand Forecast
===================================================
Forecasts daily route-level demand for Jul 1 - Dec 31, 2025.

Approach:
  1. Decompose historical demand into: Growth Trend + Seasonal Pattern + Day-of-Week Effect
  2. Model congestion impact on ridership
  3. Generate synthetic congestion forecast for H2 2025
  4. Combine all components into daily route-level predictions
  5. Aggregate for corridor-level insights
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = r'c:\Users\asus\Desktop\decodex'
OUTPUT_DIR = DATA_DIR

# ============================================================
# 1. LOAD MASTER DATASET
# ============================================================
print("=" * 70)
print("BASELINE FORECAST: Jul 1 - Dec 31, 2025")
print("=" * 70)

master_df = pd.read_csv(f'{DATA_DIR}/master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])

print(f"  Loaded: {master_df.shape[0]:,} rows, {master_df['Date'].min().date()} to {master_df['Date'].max().date()}")

# ============================================================
# 2. DAILY ROUTE-LEVEL AGGREGATION (Historical)
# ============================================================
print("\n--- Step 2: Aggregating daily route-level demand ---")

daily_route = master_df.groupby(['Date', 'Route_ID', 'Route_Code', 'Route_Type']).agg({
    'Total_Pax': 'sum',
    'Boarding_Count': 'sum',
    'Alighting_Count': 'sum',
    'Congestion_Level': 'first',
    'Avg_Speed_kmph': 'first'
}).reset_index()

daily_route['Year'] = daily_route['Date'].dt.year
daily_route['Month'] = daily_route['Date'].dt.month
daily_route['DayOfWeek'] = daily_route['Date'].dt.dayofweek
daily_route['IsWeekend'] = daily_route['DayOfWeek'].isin([4, 5]).astype(int)  # Dubai weekend

# Season
def dubai_season(m):
    if m in [11, 12, 1, 2, 3]: return 'Winter_Peak'
    elif m in [6, 7, 8]: return 'Summer_Moderate'
    else: return 'Shoulder'

daily_route['Season'] = daily_route['Month'].apply(dubai_season)

print(f"  Daily route records: {len(daily_route):,}")
print(f"  Routes: {daily_route['Route_ID'].nunique()}")

# ============================================================
# 3. COMPONENT DECOMPOSITION PER ROUTE
# ============================================================
print("\n--- Step 3: Decomposing demand components per route ---")

forecasts = []

for route_id in sorted(daily_route['Route_ID'].unique()):
    route_data = daily_route[daily_route['Route_ID'] == route_id].copy()
    route_code = route_data['Route_Code'].iloc[0]
    route_type = route_data['Route_Type'].iloc[0]
    
    # ----- 3a. Growth Trend -----
    # Calculate monthly averages and fit linear growth
    monthly_avg = route_data.groupby([route_data['Date'].dt.to_period('M')])['Total_Pax'].mean().reset_index()
    monthly_avg.columns = ['Period', 'Avg_Pax']
    monthly_avg['Period_Num'] = range(len(monthly_avg))
    
    # Linear regression for trend
    x = monthly_avg['Period_Num'].values
    y = monthly_avg['Avg_Pax'].values
    slope, intercept = np.polyfit(x, y, 1)
    monthly_growth_rate = slope / np.mean(y) if np.mean(y) > 0 else 0
    
    # ----- 3b. Monthly Seasonal Multipliers -----
    # Calculate how each month deviates from the overall detrended average
    route_data['Detrended'] = route_data['Total_Pax'] / (1 + monthly_growth_rate * 
        ((route_data['Date'] - route_data['Date'].min()).dt.days / 30))
    
    overall_detrended_avg = route_data['Detrended'].mean()
    monthly_multipliers = {}
    for month in range(1, 13):
        month_data = route_data[route_data['Month'] == month]['Detrended']
        if len(month_data) > 0:
            monthly_multipliers[month] = month_data.mean() / overall_detrended_avg
        else:
            monthly_multipliers[month] = 1.0
    
    # ----- 3c. Day-of-Week Multipliers -----
    dow_avg = route_data.groupby('DayOfWeek')['Detrended'].mean()
    overall_dow_avg = dow_avg.mean()
    dow_multipliers = (dow_avg / overall_dow_avg).to_dict()
    
    # ----- 3d. Congestion Elasticity -----
    # How does ridership change per unit of congestion?
    cong_avg = route_data.groupby('Congestion_Level')['Total_Pax'].mean()
    if len(cong_avg) > 1:
        cong_levels = cong_avg.index.values
        cong_pax = cong_avg.values
        cong_slope, cong_intercept = np.polyfit(cong_levels, cong_pax, 1)
    else:
        cong_slope, cong_intercept = 0, route_data['Total_Pax'].mean()
    
    # ----- 3e. Generate Forecast for Jul 1 - Dec 31, 2025 -----
    forecast_dates = pd.date_range('2025-07-01', '2025-12-31', freq='D')
    
    # Project the trend forward from the last known data point
    last_known_date = route_data['Date'].max()
    last_known_period = len(monthly_avg) - 1
    base_value = intercept + slope * last_known_period  # trend value at last known point
    
    for fdate in forecast_dates:
        # Months ahead from last known period
        months_ahead = (fdate.year - last_known_date.year) * 12 + (fdate.month - last_known_date.month)
        
        # Trend component
        trend_value = base_value + slope * months_ahead
        
        # Seasonal multiplier
        seasonal_mult = monthly_multipliers.get(fdate.month, 1.0)
        
        # Day-of-week multiplier
        dow_mult = dow_multipliers.get(fdate.dayofweek, 1.0)
        
        # Forecast congestion (use historical monthly average congestion)
        hist_cong = route_data[route_data['Month'] == fdate.month]['Congestion_Level']
        expected_cong = hist_cong.mean() if len(hist_cong) > 0 else 3
        
        # Combine: Trend * Seasonal * DOW
        forecast_pax = trend_value * seasonal_mult * dow_mult
        
        # Small congestion adjustment
        cong_adjustment = cong_slope * (expected_cong - route_data['Congestion_Level'].mean())
        forecast_pax += cong_adjustment * 0.3  # damped congestion effect
        
        # Floor at 0
        forecast_pax = max(0, round(forecast_pax))
        
        forecasts.append({
            'Date': fdate,
            'Route_ID': route_id,
            'Route_Code': route_code,
            'Route_Type': route_type,
            'Forecast_Total_Pax': forecast_pax,
            'Trend_Component': round(trend_value),
            'Seasonal_Multiplier': round(seasonal_mult, 3),
            'DOW_Multiplier': round(dow_mult, 3),
            'Expected_Congestion': round(expected_cong, 1),
            'Month': fdate.month,
            'DayOfWeek': fdate.dayofweek,
            'IsWeekend': 1 if fdate.dayofweek in [4, 5] else 0,
            'Season': dubai_season(fdate.month)
        })
    
    print(f"  Route {route_code} ({route_type:10s}): trend_slope={slope:+.1f}/mo, "
          f"seasonal_range=[{min(monthly_multipliers.values()):.2f}-{max(monthly_multipliers.values()):.2f}], "
          f"cong_elasticity={cong_slope:+.1f}")

# ============================================================
# 4. ASSEMBLE FORECAST DATASET
# ============================================================
print("\n--- Step 4: Assembling forecast dataset ---")

forecast_df = pd.DataFrame(forecasts)

print(f"  Forecast records: {len(forecast_df):,}")
print(f"  Date range: {forecast_df['Date'].min().date()} to {forecast_df['Date'].max().date()}")
print(f"  Routes covered: {forecast_df['Route_ID'].nunique()}")

# ============================================================
# 5. FORECAST SUMMARY & VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("FORECAST SUMMARY")
print("=" * 70)

# 5a. Total forecast demand
total_forecast = forecast_df['Forecast_Total_Pax'].sum()
print(f"\n  Total forecast demand (Jul-Dec 2025): {total_forecast:,.0f} pax")

# Compare with same period last year
same_period_2024 = daily_route[
    (daily_route['Date'] >= '2024-07-01') & (daily_route['Date'] <= '2024-12-31')
]['Total_Pax'].sum()
print(f"  Same period 2024 (actual):            {same_period_2024:,.0f} pax")
print(f"  Implied growth rate:                  {(total_forecast/same_period_2024 - 1)*100:+.1f}%")

# Full year 2025 projection
h1_actual = daily_route[
    (daily_route['Date'] >= '2025-01-01') & (daily_route['Date'] <= '2025-06-30')
]['Total_Pax'].sum()
full_year_2025 = h1_actual + total_forecast
print(f"\n  H1 2025 actual:                       {h1_actual:,.0f} pax")
print(f"  H2 2025 forecast:                     {total_forecast:,.0f} pax")
print(f"  Full year 2025 projection:            {full_year_2025:,.0f} pax")
print(f"  vs 2024 ({daily_route[daily_route['Year']==2024]['Total_Pax'].sum():,.0f}): "
      f"{(full_year_2025/daily_route[daily_route['Year']==2024]['Total_Pax'].sum()-1)*100:+.1f}%")

# 5b. Monthly forecast breakdown
print("\n--- Monthly Forecast Breakdown ---")
monthly_forecast = forecast_df.groupby('Month').agg({
    'Forecast_Total_Pax': ['sum', 'mean']
}).round(0)
monthly_forecast.columns = ['Total_Pax', 'Daily_Avg']
month_names = {7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
for month, row in monthly_forecast.iterrows():
    print(f"  {month_names[month]} 2025: Total={row['Total_Pax']:>10,.0f}  Daily_Avg={row['Daily_Avg']:>8,.0f}")

# 5c. Route-level forecast
print("\n--- Route-Level Forecast (H2 2025) ---")
route_forecast = forecast_df.groupby(['Route_Code', 'Route_Type']).agg({
    'Forecast_Total_Pax': ['sum', 'mean']
}).round(0)
route_forecast.columns = ['Total_Pax', 'Daily_Avg']
route_forecast = route_forecast.sort_values('Total_Pax', ascending=False)
for (rcode, rtype), row in route_forecast.iterrows():
    print(f"  {rcode} ({rtype:10s}): Total={row['Total_Pax']:>10,.0f}  Daily_Avg={row['Daily_Avg']:>7,.0f}")

# 5d. Seasonal split
print("\n--- Seasonal Forecast Split ---")
season_forecast = forecast_df.groupby('Season')['Forecast_Total_Pax'].agg(['sum', 'mean']).round(0)
season_forecast.columns = ['Total_Pax', 'Daily_Avg']
for season, row in season_forecast.iterrows():
    print(f"  {season:20s}: Total={row['Total_Pax']:>10,.0f}  Daily_Avg={row['Daily_Avg']:>7,.0f}")

# 5e. Weekday vs Weekend forecast
print("\n--- Weekday vs Weekend Forecast ---")
daytype_forecast = forecast_df.groupby('IsWeekend')['Forecast_Total_Pax'].agg(['sum', 'mean']).round(0)
daytype_forecast.index = ['Weekday', 'Weekend']
daytype_forecast.columns = ['Total_Pax', 'Daily_Avg']
for dtype, row in daytype_forecast.iterrows():
    print(f"  {dtype:10s}: Total={row['Total_Pax']:>10,.0f}  Daily_Avg={row['Daily_Avg']:>7,.0f}")

# 5f. Route Type forecast comparison
print("\n--- Route Type Forecast vs Historical ---")
for rtype in ['City', 'Express', 'Feeder', 'Intercity']:
    hist_daily = daily_route[
        (daily_route['Route_Type'] == rtype) &
        (daily_route['Date'] >= '2024-07-01') &
        (daily_route['Date'] <= '2024-12-31')
    ]['Total_Pax'].mean()
    
    fcast_daily = forecast_df[forecast_df['Route_Type'] == rtype]['Forecast_Total_Pax'].mean()
    
    change = (fcast_daily / hist_daily - 1) * 100 if hist_daily > 0 else 0
    print(f"  {rtype:12s}: Hist_Daily_Avg={hist_daily:>7,.0f}  Fcast_Daily_Avg={fcast_daily:>7,.0f}  Change={change:+.1f}%")

# ============================================================
# 6. PEAK DEMAND DAYS (TOP 10)
# ============================================================
print("\n--- Top 10 Peak Demand Days (Forecast) ---")
daily_total = forecast_df.groupby('Date')['Forecast_Total_Pax'].sum().reset_index()
daily_total = daily_total.sort_values('Forecast_Total_Pax', ascending=False).head(10)
for _, row in daily_total.iterrows():
    d = row['Date']
    dow_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][d.dayofweek]
    print(f"  {d.strftime('%Y-%m-%d')} ({dow_name}): {row['Forecast_Total_Pax']:>8,.0f}")

# ============================================================
# 7. CAPACITY RISK FLAGS
# ============================================================
print("\n" + "=" * 70)
print("CAPACITY RISK FLAGS")
print("=" * 70)

# Historical 95th percentile by route as capacity threshold
print("\nRoutes exceeding historical 95th percentile demand:")
for route_id in sorted(daily_route['Route_ID'].unique()):
    hist_route = daily_route[daily_route['Route_ID'] == route_id]
    p95 = hist_route['Total_Pax'].quantile(0.95)
    route_code = hist_route['Route_Code'].iloc[0]
    route_type = hist_route['Route_Type'].iloc[0]
    
    fcast_route = forecast_df[forecast_df['Route_ID'] == route_id]
    days_above = (fcast_route['Forecast_Total_Pax'] > p95).sum()
    pct_above = days_above / len(fcast_route) * 100
    
    if days_above > 0:
        max_fcast = fcast_route['Forecast_Total_Pax'].max()
        print(f"  {route_code} ({route_type:10s}): {days_above:3d} days above P95 ({pct_above:.0f}%), "
              f"P95={p95:,.0f}, Max_Forecast={max_fcast:,.0f}, Overshoot={max_fcast/p95*100-100:+.1f}%")

# ============================================================
# 8. SAVE FORECAST
# ============================================================
print("\n" + "=" * 70)
print("SAVING FORECAST")
print("=" * 70)

output_path = f'{OUTPUT_DIR}/forecast_h2_2025.csv'
forecast_df.to_csv(output_path, index=False)
print(f"  Saved to: {output_path}")
print(f"  Shape: {forecast_df.shape}")

print("\n" + "=" * 70)
print("[DONE] BASELINE FORECAST COMPLETE")
print("=" * 70)
