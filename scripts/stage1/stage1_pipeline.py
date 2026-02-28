"""
DECODE X 2026 - Stage 1: Data Integration & Baseline Analysis
=============================================================
Master merge of all 5 CSVs + initial diagnostic metrics.
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# 1. LOAD ALL DATASETS
# ============================================================
print("=" * 60)
print("STEP 1: Loading all datasets...")
print("=" * 60)

routes_df = pd.read_csv(os.path.join(DATA_DIR, 'Bus_Routes.csv'))
stops_df = pd.read_csv(os.path.join(DATA_DIR, 'Bus_Stops.csv'))
mapping_df = pd.read_csv(os.path.join(DATA_DIR, 'Route_Stop_Mapping.csv'))
ridership_df = pd.read_csv(os.path.join(DATA_DIR, 'Train_Ridership_2022_to_2025H1.csv'))
traffic_df = pd.read_csv(os.path.join(DATA_DIR, 'Train_Traffic_2022_to_2025H1.csv'))

print(f"  Routes:          {routes_df.shape}")
print(f"  Stops:           {stops_df.shape}")
print(f"  Route-Stop Map:  {mapping_df.shape}")
print(f"  Ridership:       {ridership_df.shape}")
print(f"  Traffic:         {traffic_df.shape}")

# ============================================================
# 2. CREATE TARGET METRIC
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Creating Total_Pax metric...")
print("=" * 60)

ridership_df['Total_Pax'] = ridership_df['Boarding_Count'] + ridership_df['Alighting_Count']
ridership_df['Date'] = pd.to_datetime(ridership_df['Date'])
traffic_df['Date'] = pd.to_datetime(traffic_df['Date'])

print(f"  Total_Pax range: {ridership_df['Total_Pax'].min()} to {ridership_df['Total_Pax'].max()}")
print(f"  Total_Pax mean:  {ridership_df['Total_Pax'].mean():.1f}")
print(f"  Date range:      {ridership_df['Date'].min().date()} to {ridership_df['Date'].max().date()}")

# ============================================================
# 3. MASTER MERGE
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Master Merge (5 datasets -> 1 analytical table)...")
print("=" * 60)

rows_before = len(ridership_df)

# 3a. Merge Ridership + Stop details (on Stop_ID)
master_df = ridership_df.merge(
    stops_df[['Stop_ID', 'Stop_Name', 'Latitude', 'Longitude', 'Stop_Type', 'Zone']],
    on='Stop_ID',
    how='left'
)
print(f"  After Stop merge:    {master_df.shape[0]} rows (lost {rows_before - master_df.shape[0]})")

# 3b. Merge + Route details (on Route_ID)
master_df = master_df.merge(
    routes_df[['Route_ID', 'Route_Code', 'Route_Length_km', 'Avg_Travel_Time_Min', 'Route_Type']],
    on='Route_ID',
    how='left'
)
print(f"  After Route merge:   {master_df.shape[0]} rows (lost {rows_before - master_df.shape[0]})")

# 3c. Merge + Route-Stop Mapping (on Route_ID + Stop_ID)
master_df = master_df.merge(
    mapping_df[['Route_ID', 'Stop_ID', 'Stop_Sequence', 'Dwell_Time_Min']],
    on=['Route_ID', 'Stop_ID'],
    how='left'
)
print(f"  After Mapping merge: {master_df.shape[0]} rows (lost {rows_before - master_df.shape[0]})")

# 3d. Merge + Traffic/Congestion (on Date)
master_df = master_df.merge(
    traffic_df[['Date', 'Congestion_Level', 'Avg_Speed_kmph']],
    on='Date',
    how='left'
)
print(f"  After Traffic merge: {master_df.shape[0]} rows (lost {rows_before - master_df.shape[0]})")

# ============================================================
# 4. INTEGRITY CHECK
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Integrity Checks...")
print("=" * 60)

print(f"  Final master rows:     {len(master_df)}")
print(f"  Original ridership:    {rows_before}")
print(f"  Row difference:        {len(master_df) - rows_before}")
print(f"  Null counts per column:")
null_counts = master_df.isnull().sum()
for col, count in null_counts.items():
    if count > 0:
        print(f"    {col}: {count} ({count/len(master_df)*100:.1f}%)")
if null_counts.sum() == 0:
    print(f"    [OK] No null values found!")

print(f"\n  Unique Routes:  {master_df['Route_ID'].nunique()}")
print(f"  Unique Stops:   {master_df['Stop_ID'].nunique()}")
print(f"  Unique Dates:   {master_df['Date'].nunique()}")
print(f"  Route Types:    {master_df['Route_Type'].unique().tolist()}")
print(f"  Zones:          {master_df['Zone'].unique().tolist()}")
print(f"  Stop Types:     {master_df['Stop_Type'].unique().tolist()}")

# ============================================================
# 5. FEATURE ENGINEERING FOR ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: Feature Engineering...")
print("=" * 60)

master_df['Year'] = master_df['Date'].dt.year
master_df['Month'] = master_df['Date'].dt.month
master_df['DayOfWeek'] = master_df['Date'].dt.dayofweek  # 0=Mon, 6=Sun
master_df['IsWeekend'] = master_df['DayOfWeek'].isin([4, 5]).astype(int)  # Fri-Sat for Dubai
master_df['Quarter'] = master_df['Date'].dt.quarter

# Season classification (Dubai context)
def dubai_season(month):
    if month in [11, 12, 1, 2, 3]:
        return 'Winter_Peak'
    elif month in [6, 7, 8]:
        return 'Summer_Moderate'
    else:
        return 'Shoulder'

master_df['Season'] = master_df['Month'].apply(dubai_season)

# Year-Month for time series
master_df['YearMonth'] = master_df['Date'].dt.to_period('M')

print(f"  Added: Year, Month, DayOfWeek, IsWeekend, Quarter, Season, YearMonth")
print(f"  Weekend definition: Friday + Saturday (Dubai standard)")
print(f"  Seasons: Winter_Peak (Nov-Mar), Summer_Moderate (Jun-Aug), Shoulder (Apr-May, Sep-Oct)")

# ============================================================
# 6. INITIAL DIAGNOSTIC METRICS
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: Initial Diagnostic Metrics")
print("=" * 60)

# 6a. Yearly growth
print("\n--- 6a. Yearly Total Pax Growth ---")
yearly = master_df.groupby('Year')['Total_Pax'].agg(['sum', 'mean', 'count'])
yearly.columns = ['Total_Pax', 'Avg_Pax_Per_Record', 'Records']
for year, row in yearly.iterrows():
    print(f"  {year}: Total={row['Total_Pax']:,.0f}  Avg={row['Avg_Pax_Per_Record']:.1f}  Records={row['Records']:,}")

# Year-over-year growth
yearly_totals = yearly['Total_Pax'].values
for i in range(1, len(yearly_totals)):
    growth = (yearly_totals[i] - yearly_totals[i-1]) / yearly_totals[i-1] * 100
    print(f"  {yearly.index[i-1]}->{yearly.index[i]} growth: {growth:+.1f}%")

# 6b. Seasonal patterns
print("\n--- 6b. Seasonal Demand Patterns ---")
seasonal = master_df.groupby('Season')['Total_Pax'].agg(['sum', 'mean', 'count'])
seasonal.columns = ['Total_Pax', 'Avg_Pax', 'Records']
for season, row in seasonal.iterrows():
    print(f"  {season:20s}: Total={row['Total_Pax']:>12,.0f}  Avg={row['Avg_Pax']:.1f}")

# 6c. Weekday vs Weekend
print("\n--- 6c. Weekday vs Weekend ---")
daytype = master_df.groupby('IsWeekend')['Total_Pax'].agg(['sum', 'mean', 'count'])
daytype.index = ['Weekday', 'Weekend']
daytype.columns = ['Total_Pax', 'Avg_Pax', 'Records']
for dtype, row in daytype.iterrows():
    print(f"  {dtype:10s}: Total={row['Total_Pax']:>12,.0f}  Avg={row['Avg_Pax']:.1f}")

# 6d. Route-type comparison
print("\n--- 6d. Route Type Analysis ---")
routetype = master_df.groupby('Route_Type')['Total_Pax'].agg(['sum', 'mean', 'count'])
routetype.columns = ['Total_Pax', 'Avg_Pax', 'Records']
routetype = routetype.sort_values('Total_Pax', ascending=False)
for rtype, row in routetype.iterrows():
    print(f"  {rtype:12s}: Total={row['Total_Pax']:>12,.0f}  Avg={row['Avg_Pax']:.1f}")

# 6e. Zone-level demand
print("\n--- 6e. Zone-Level Demand ---")
zone = master_df.groupby('Zone')['Total_Pax'].agg(['sum', 'mean', 'count'])
zone.columns = ['Total_Pax', 'Avg_Pax', 'Records']
zone = zone.sort_values('Total_Pax', ascending=False)
for z, row in zone.iterrows():
    print(f"  {z:30s}: Total={row['Total_Pax']:>12,.0f}  Avg={row['Avg_Pax']:.1f}")

# 6f. Congestion impact
print("\n--- 6f. Congestion Level Impact on Ridership ---")
congestion = master_df.groupby('Congestion_Level').agg({
    'Total_Pax': ['sum', 'mean'],
    'Avg_Speed_kmph': 'mean',
    'Boarding_Count': 'mean',
    'Alighting_Count': 'mean'
}).round(2)
congestion.columns = ['Total_Pax', 'Avg_Pax', 'Avg_Speed', 'Avg_Board', 'Avg_Alight']
for level, row in congestion.iterrows():
    print(f"  Level {level}: Pax_Avg={row['Avg_Pax']:.1f}  Speed={row['Avg_Speed']:.1f} km/h  Board={row['Avg_Board']:.1f}  Alight={row['Avg_Alight']:.1f}")

# 6g. Top 10 busiest stops
print("\n--- 6g. Top 10 Busiest Stops ---")
top_stops = master_df.groupby(['Stop_ID', 'Stop_Name', 'Zone', 'Stop_Type'])['Total_Pax'].sum().reset_index()
top_stops = top_stops.sort_values('Total_Pax', ascending=False).head(10)
for _, row in top_stops.iterrows():
    print(f"  Stop {row['Stop_ID']:2d} ({row['Stop_Type']:12s}|{row['Zone']:25s}): {row['Total_Pax']:>10,.0f} pax")

# 6h. Top 10 busiest routes
print("\n--- 6h. Top 10 Busiest Routes ---")
top_routes = master_df.groupby(['Route_ID', 'Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()
top_routes = top_routes.sort_values('Total_Pax', ascending=False).head(10)
for _, row in top_routes.iterrows():
    print(f"  Route {row['Route_Code']} ({row['Route_Type']:10s}): {row['Total_Pax']:>12,.0f} pax")

# 6i. Monthly trend
print("\n--- 6i. Monthly Demand Trend (last 12 months of data) ---")
monthly = master_df.groupby('YearMonth')['Total_Pax'].sum()
for ym, total in monthly.tail(12).items():
    print(f"  {ym}: {total:>10,.0f}")

# ============================================================
# 7. SAVE MASTER DATASET
# ============================================================
print("\n" + "=" * 60)
print("STEP 7: Saving master dataset...")
print("=" * 60)

output_path = os.path.join(DATA_DIR, 'master_analytical_dataset.csv')
master_df.to_csv(output_path, index=False)
print(f"  Saved to: {output_path}")
print(f"  Shape: {master_df.shape}")
print(f"  Columns: {master_df.columns.tolist()}")

print("\n" + "=" * 60)
print("[DONE] STAGE 1 DATA PIPELINE COMPLETE")
print("=" * 60)
