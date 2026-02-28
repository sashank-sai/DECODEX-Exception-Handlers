"""
DECODE X 2026 - Data Visualizations v2
========================================
Updated: Forecast/Actual bar order swapped, inference annotations on all charts.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(r'c:\Users\asus\Desktop\decodex')
CHART_DIR = DATA_DIR / 'charts'
CHART_DIR.mkdir(exist_ok=True)

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')
COLORS = {
    'City': '#2196F3', 'Express': '#F44336', 'Feeder': '#4CAF50', 'Intercity': '#FF9800',
    'primary': '#1976D2', 'danger': '#D32F2F', 'success': '#388E3C', 'warning': '#F57C00',
    'dark': '#263238'
}
FONT = {'family': 'sans-serif', 'size': 11}
matplotlib.rc('font', **FONT)

master_df = pd.read_csv(DATA_DIR / 'master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])
forecast_df = pd.read_csv(DATA_DIR / 'forecast_h2_2025.csv')
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])

def add_inference(ax, text, x=0.02, y=0.02, fontsize=9):
    """Add inference text box at bottom of chart."""
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fontsize,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9),
            style='italic', wrap=True)

print("Generating visualizations v2...\n")

# ============================================================
# CHART 1: Monthly Demand Trend
# ============================================================
fig, ax = plt.subplots(figsize=(14, 6))
monthly = master_df.groupby(master_df['Date'].dt.to_period('M'))['Total_Pax'].sum()
monthly.index = monthly.index.to_timestamp()
ax.plot(monthly.index, monthly.values, color=COLORS['primary'], linewidth=2, label='Actual')

fcast_monthly = forecast_df.groupby(forecast_df['Date'].dt.to_period('M'))['Forecast_Total_Pax'].sum()
fcast_monthly.index = fcast_monthly.to_timestamp().index
ax.plot(fcast_monthly.index, fcast_monthly.values, color=COLORS['danger'], linewidth=2, 
        linestyle='--', label='Forecast', marker='o', markersize=4)

for year in [2022, 2023, 2024, 2025]:
    ax.axvspan(pd.Timestamp(f'{year}-11-01'), pd.Timestamp(f'{year+1}-03-31'), alpha=0.08, color='blue',
               label='Winter Peak' if year == 2022 else '')
    ax.axvspan(pd.Timestamp(f'{year}-06-01'), pd.Timestamp(f'{year}-08-31'), alpha=0.08, color='red',
               label='Summer Low' if year == 2022 else '')

ax.set_title('Monthly Passenger Demand: Historical + Forecast', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax.legend(loc='upper left')
ax.set_xlim(pd.Timestamp('2022-01-01'), pd.Timestamp('2026-01-01'))

add_inference(ax, 
    "INFERENCE: Demand follows a clear annual cycle — winter peaks (blue zones) consistently\n"
    "reach 30-40% above summer troughs (red zones). Each year's peak exceeds the previous,\n"
    "confirming compounding growth. Jan 2025 set the all-time high at 1.07M passengers.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '01_monthly_demand_trend.png', dpi=150)
plt.close()
print("  [1/12] Monthly demand trend")

# ============================================================
# CHART 2: Yearly Growth
# ============================================================
fig, ax = plt.subplots(figsize=(8, 6))
yearly = master_df.groupby('Year')['Total_Pax'].sum()
bars = ax.bar(yearly.index.astype(str), yearly.values, color=COLORS['primary'], width=0.6, edgecolor='white')

for i in range(1, len(yearly)):
    growth = (yearly.values[i] - yearly.values[i-1]) / yearly.values[i-1] * 100
    label = f'+{growth:.1f}%' if growth > 0 else f'{growth:.1f}%'
    ax.annotate(label, xy=(i, yearly.values[i]), fontsize=12, fontweight='bold',
                ha='center', va='bottom', color=COLORS['success'])

for bar, val in zip(bars, yearly.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f'{val/1e6:.1f}M',
            ha='center', va='center', fontsize=13, fontweight='bold', color='white')

ax.set_title('Yearly Total Passengers (Growth Accelerating)', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
ax.text(3, yearly.values[-1]*0.7, '* 2025: H1 only\n(Jan-Jun)', fontsize=9, style='italic', color='gray')

add_inference(ax,
    "INFERENCE: Growth is accelerating — from +9.2% to +13.1%.\n"
    "2025 H1 annualizes to ~11.1M (+7.9% over 2024).\n"
    "The network added ~2M annual riders in two years.",
    x=0.05, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '02_yearly_growth.png', dpi=150)
plt.close()
print("  [2/12] Yearly growth")

# ============================================================
# CHART 3: Seasonal Demand
# ============================================================
fig, ax = plt.subplots(figsize=(9, 6))

def dubai_season(m):
    if m in [11, 12, 1, 2, 3]: return 'Winter Peak\n(Nov-Mar)'
    elif m in [6, 7, 8]: return 'Summer Low\n(Jun-Aug)'
    else: return 'Shoulder\n(Apr-May, Sep-Oct)'

master_df['Season_Label'] = master_df['Date'].dt.month.apply(dubai_season)
season_order = ['Winter Peak\n(Nov-Mar)', 'Shoulder\n(Apr-May, Sep-Oct)', 'Summer Low\n(Jun-Aug)']
season_data = master_df.groupby('Season_Label')['Total_Pax'].mean().reindex(season_order)
season_colors = ['#1565C0', '#FF8F00', '#C62828']

bars = ax.bar(season_data.index, season_data.values, color=season_colors, width=0.6, edgecolor='white')
for bar, val in zip(bars, season_data.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.0f}',
            ha='center', va='bottom', fontsize=13, fontweight='bold')

ax.set_title('Seasonal Demand Pattern (Avg Pax per Stop-Day)', fontsize=14, fontweight='bold')
ax.set_ylabel('Avg Passengers')

add_inference(ax,
    "INFERENCE: Winter demand (189.5 avg) is 31% higher than\n"
    "summer (145.1). This is Dubai's strongest demand driver —\n"
    "pleasant weather + tourism peaks drive ridership up sharply.",
    x=0.35, y=0.35)

plt.tight_layout()
plt.savefig(CHART_DIR / '03_seasonal_demand.png', dpi=150)
plt.close()
print("  [3/12] Seasonal demand")

# ============================================================
# CHART 4: Route Type Comparison
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))

route_type_data = master_df.groupby('Route_Type').agg({'Total_Pax': ['sum', 'mean', 'count']}).reset_index()
route_type_data.columns = ['Route_Type', 'Total', 'Avg', 'Records']
type_order = ['City', 'Express', 'Feeder', 'Intercity']
type_colors = [COLORS[t] for t in type_order]
route_type_data = route_type_data.set_index('Route_Type').reindex(type_order)

axes[0].barh(route_type_data.index, route_type_data['Total'], color=type_colors, edgecolor='white')
axes[0].set_title('Total Volume', fontweight='bold')
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
for i, v in enumerate(route_type_data['Total']): axes[0].text(v, i, f' {v/1e6:.1f}M', va='center', fontweight='bold')

axes[1].barh(route_type_data.index, route_type_data['Avg'], color=type_colors, edgecolor='white')
axes[1].set_title('Avg Pax per Stop-Day', fontweight='bold')
for i, v in enumerate(route_type_data['Avg']): axes[1].text(v, i, f' {v:.0f}', va='center', fontweight='bold')

route_counts = master_df.groupby('Route_Type')['Route_ID'].nunique().reindex(type_order)
axes[2].barh(route_counts.index, route_counts.values, color=type_colors, edgecolor='white')
axes[2].set_title('Number of Routes', fontweight='bold')
for i, v in enumerate(route_counts.values): axes[2].text(v, i, f' {v}', va='center', fontweight='bold', fontsize=12)

fig.suptitle('Route Type Comparison', fontsize=14, fontweight='bold', y=1.02)

fig.text(0.5, -0.02, 
    "INFERENCE: Express routes have the highest per-stop intensity (197 avg) with only 3 routes — they are under-provisioned.\n"
    "City routes are the backbone (12.9M total). Intercity carries the least and may have excess capacity.",
    ha='center', fontsize=9, style='italic',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9))

plt.tight_layout()
plt.savefig(CHART_DIR / '04_route_type_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [4/12] Route type comparison")

# ============================================================
# CHART 5: Congestion Paradox
# ============================================================
fig, ax = plt.subplots(figsize=(10, 6.5))
daily_total = master_df.groupby('Date').agg({
    'Total_Pax': 'sum', 'Congestion_Level': 'first', 'Avg_Speed_kmph': 'first'
}).reset_index()

scatter = ax.scatter(daily_total['Congestion_Level'], daily_total['Total_Pax'],
                     c=daily_total['Avg_Speed_kmph'], cmap='RdYlGn', s=15, alpha=0.5)
plt.colorbar(scatter, ax=ax, label='Avg Speed (km/h)')

z = np.polyfit(daily_total['Congestion_Level'], daily_total['Total_Pax'], 1)
p = np.poly1d(z)
x_trend = np.linspace(daily_total['Congestion_Level'].min(), daily_total['Congestion_Level'].max(), 100)
ax.plot(x_trend, p(x_trend), color=COLORS['danger'], linewidth=2, linestyle='--', label='Trend')

ax.set_title('Congestion Paradox: Ridership INCREASES with Congestion', fontsize=13, fontweight='bold')
ax.set_xlabel('Congestion Level')
ax.set_ylabel('Daily Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e3:.0f}K'))
ax.legend()

add_inference(ax,
    "INFERENCE: Modal shift effect — when roads congest, car users switch\n"
    "to buses, raising ridership by ~20%. But bus speeds also halve (40 to\n"
    "21 km/h), creating overcrowding + delays. This justifies bus-priority lanes.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '05_congestion_paradox.png', dpi=150)
plt.close()
print("  [5/12] Congestion paradox")

# ============================================================
# CHART 6: Zone Demand
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))
zone_data = master_df.groupby('Zone')['Total_Pax'].agg(['sum', 'mean']).reset_index()
zone_data.columns = ['Zone', 'Total', 'Avg']
zone_data = zone_data.sort_values('Total', ascending=True)
zone_data['Short'] = zone_data['Zone'].str.replace('Res_','').str.replace('CBD_','').str.replace('Core_','').str.replace('Ind_','').str.replace('Coastal_','')

colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(zone_data)))
bars = ax.barh(zone_data['Short'], zone_data['Total'], color=colors, edgecolor='white', height=0.6)
for bar, (_, row) in zip(bars, zone_data.iterrows()):
    ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
            f'  {row["Total"]/1e6:.1f}M  (avg: {row["Avg"]:.0f})', va='center', fontsize=10, fontweight='bold')

ax.set_title('Zone Demand Ranking (Total Pax, All Years)', fontsize=14, fontweight='bold')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))
ax.set_xlabel('Total Passengers')

add_inference(ax,
    "INFERENCE: Downtown leads in volume (8.7M), but Coastal Marina\n"
    "has the highest per-stop intensity (199 avg) with only 5 stops —\n"
    "the most capacity-constrained zone, needing urgent intervention.",
    x=0.35, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '06_zone_demand.png', dpi=150)
plt.close()
print("  [6/12] Zone demand")

# ============================================================
# CHART 7: Weekday vs Weekend
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))
master_df['IsWeekend'] = master_df['Date'].dt.dayofweek.isin([4, 5]).astype(int)
daytype = master_df.groupby(['Route_Code', 'Route_Type', 'IsWeekend'])['Total_Pax'].mean().reset_index()
weekday = daytype[daytype['IsWeekend'] == 0].set_index('Route_Code')['Total_Pax']
weekend = daytype[daytype['IsWeekend'] == 1].set_index('Route_Code')['Total_Pax']

route_codes = sorted(weekday.index)
x = np.arange(len(route_codes))
width = 0.35

ax.bar(x - width/2, [weekday[r] for r in route_codes], width,
       label='Weekday (Sun-Thu)', color=COLORS['primary'], edgecolor='white')
ax.bar(x + width/2, [weekend[r] for r in route_codes], width,
       label='Weekend (Fri-Sat)', color=COLORS['warning'], edgecolor='white')

ax.set_xticks(x)
ax.set_xticklabels(route_codes, fontsize=10)
ax.set_title('Weekday vs Weekend Demand by Route', fontsize=14, fontweight='bold')
ax.set_ylabel('Avg Passengers per Stop-Day')
ax.legend()

type_map = master_df.groupby('Route_Code')['Route_Type'].first().to_dict()
for label in ax.get_xticklabels():
    rtype = type_map.get(label.get_text(), '')
    label.set_color(COLORS.get(rtype, 'black'))
    label.set_fontweight('bold')

add_inference(ax,
    "INFERENCE: All routes show higher weekday demand — this is a commuter network.\n"
    "Express routes drop ~8% on weekends (steepest), City routes only ~3-5%. Weekend\n"
    "service can be safely reduced on Express routes to redeploy buses to weekday peaks.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '07_weekday_weekend.png', dpi=150)
plt.close()
print("  [7/12] Weekday vs weekend")

# ============================================================
# CHART 8: Top 10 Busiest Stops
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))
top_stops = master_df.groupby(['Stop_ID', 'Zone', 'Stop_Type'])['Total_Pax'].sum().reset_index()
top_stops = top_stops.sort_values('Total_Pax', ascending=True).tail(10)

zone_colors = {
    'Coastal_Marina': '#00BCD4', 'CBD_Downtown': '#673AB7', 'Core_Deira': '#E91E63',
    'CBD_BusinessBay': '#FF5722', 'Res_AlQusais': '#4CAF50',
    'Res_InternationalCity': '#CDDC39', 'Ind_JebelAli': '#795548'
}
bar_colors = [zone_colors.get(z, '#607D8B') for z in top_stops['Zone']]

bars = ax.barh(range(len(top_stops)), top_stops['Total_Pax'], color=bar_colors, edgecolor='white', height=0.7)
ax.set_yticks(range(len(top_stops)))
labels = [f"Stop {row['Stop_ID']} ({row['Stop_Type']})" for _, row in top_stops.iterrows()]
ax.set_yticklabels(labels, fontsize=10)

for bar, (_, row) in zip(bars, top_stops.iterrows()):
    ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
            f'  {row["Total_Pax"]/1e6:.2f}M  [{row["Zone"].split("_")[-1]}]',
            va='center', fontsize=9, fontweight='bold')

ax.set_title('Top 10 Busiest Stops (Total Passengers, All Years)', fontsize=14, fontweight='bold')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))

from matplotlib.patches import Patch
legend_patches = [Patch(color=c, label=z.replace('_', ' ')) for z, c in zone_colors.items()]
ax.legend(handles=legend_patches, loc='lower right', fontsize=8, ncol=2)

add_inference(ax,
    "INFERENCE: Coastal Marina (3 stops in top 10) and CBD Downtown (5 stops)\n"
    "dominate. Stop 52 (Marina, regular stop) beats even Metro Link interchanges.\n"
    "Mid-route stops carry more load than terminals — demand is distributed, not endpoint-heavy.",
    x=0.3, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '08_top_stops.png', dpi=150)
plt.close()
print("  [8/12] Top stops")

# ============================================================
# CHART 9: Overload Risk Score
# ============================================================
fig, ax = plt.subplots(figsize=(10, 7))
recent = master_df[master_df['Date'] >= '2025-01-01']
route_daily = recent.groupby(['Date', 'Route_ID', 'Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()
route_avg = route_daily.groupby(['Route_Code', 'Route_Type'])['Total_Pax'].mean().reset_index()
routes_info = pd.read_csv(DATA_DIR / 'Bus_Routes.csv')
route_avg = route_avg.merge(routes_info[['Route_Code', 'Route_Length_km']], on='Route_Code')
route_avg['Pax_Per_Km'] = route_avg['Total_Pax'] / route_avg['Route_Length_km']
min_pk, max_pk = route_avg['Pax_Per_Km'].min(), route_avg['Pax_Per_Km'].max()
route_avg['Risk'] = ((route_avg['Pax_Per_Km'] - min_pk) / (max_pk - min_pk) * 100).round(0)
route_avg = route_avg.sort_values('Risk', ascending=True)

bar_colors = [COLORS.get(rt, '#607D8B') for rt in route_avg['Route_Type']]
bars = ax.barh(route_avg['Route_Code'], route_avg['Risk'], color=bar_colors, edgecolor='white', height=0.6)

ax.axvline(x=70, color=COLORS['danger'], linestyle='--', alpha=0.7, linewidth=1.5)
ax.axvline(x=40, color=COLORS['warning'], linestyle='--', alpha=0.7, linewidth=1.5)
ax.text(75, len(route_avg)-1, 'CRITICAL', color=COLORS['danger'], fontweight='bold', fontsize=9)
ax.text(45, len(route_avg)-1, 'WARNING', color=COLORS['warning'], fontweight='bold', fontsize=9)
ax.text(10, len(route_avg)-1, 'OK', color=COLORS['success'], fontweight='bold', fontsize=9)

for bar, (_, row) in zip(bars, route_avg.iterrows()):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{row["Risk"]:.0f}  ({row["Pax_Per_Km"]:.1f} pax/km)', va='center', fontsize=9, fontweight='bold')

ax.set_title('Route Overload Risk Score (Pax Density)', fontsize=14, fontweight='bold')
ax.set_xlabel('Risk Score (0-100)')
ax.set_xlim(0, 115)

legend_patches = [Patch(color=COLORS[t], label=t) for t in ['City', 'Express', 'Feeder', 'Intercity']]
ax.legend(handles=legend_patches, loc='center right')

add_inference(ax,
    "INFERENCE: ALL 3 Express routes are above WARNING level — this is a\n"
    "systemic category failure, not isolated. X28 (18.8 pax/km) is in CRITICAL\n"
    "zone. Feeder/Intercity have headroom to donate capacity to Express corridors.",
    x=0.3, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '09_overload_risk.png', dpi=150)
plt.close()
print("  [9/12] Overload risk")

# ============================================================
# CHART 10: Forecast vs Historical — SWAPPED ORDER
# ============================================================
fig, ax = plt.subplots(figsize=(12, 6))

h2_2024 = master_df[(master_df['Date'] >= '2024-07-01') & (master_df['Date'] <= '2024-12-31')]
h2_2024_monthly = h2_2024.groupby(h2_2024['Date'].dt.month)['Total_Pax'].sum()
h2_2025_monthly = forecast_df.groupby(forecast_df['Date'].dt.month)['Forecast_Total_Pax'].sum()

months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
x = np.arange(len(months))
width = 0.35

# SWAPPED: Forecast (budget) FIRST, then Actual
bars1 = ax.bar(x - width/2, h2_2025_monthly.values, width, label='H2 2025 (Forecast)',
               color=COLORS['danger'], edgecolor='white', alpha=0.9)
bars2 = ax.bar(x + width/2, h2_2024_monthly.values, width, label='H2 2024 (Actual)',
               color=COLORS['primary'], edgecolor='white', alpha=0.8)

# Growth labels on forecast bars
for i in range(len(months)):
    growth = (h2_2025_monthly.values[i] / h2_2024_monthly.values[i] - 1) * 100
    ax.text(i - width/2, h2_2025_monthly.values[i], f'+{growth:.0f}%',
            ha='center', va='bottom', fontsize=10, fontweight='bold', color=COLORS['danger'])

ax.set_xticks(x)
ax.set_xticklabels(months, fontsize=12)
ax.set_title('H2 2025 Forecast vs H2 2024 Actual (Monthly Comparison)', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e3:.0f}K'))
ax.legend(fontsize=11)

add_inference(ax,
    "INFERENCE: Forecast (red, left) consistently exceeds actuals (blue, right) by\n"
    "+7-8% every month — growth is broad-based, not event-driven. December is the peak\n"
    "month in both years. Nov-Dec 2025 will be the most capacity-critical months.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '10_forecast_vs_actual.png', dpi=150)
plt.close()
print("  [10/12] Forecast vs actual (SWAPPED)")

# ============================================================
# CHART 11: Fleet Reallocation — Current vs Proposed (Grouped)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

# Route data: (label, current_fleet, proposed_fleet)
fleet_data = [
    ('X28\n(Exp)',    7, 10), ('C03\n(City)',  8, 10), ('C02\n(City)',  5,  7),
    ('E22\n(Inter)',  6,  8), ('F25\n(Feed)',  7,  9), ('X11\n(Exp)',   5,  5),
    ('F18\n(Feed)',   8,  7), ('C01\n(City)',  8,  7), ('E16\n(Inter)', 5,  4),
    ('X66\n(Exp)',    8,  6), ('C04\n(City)',  7,  4), ('F12\n(Feed)',  7,  4),
]

labels = [d[0] for d in fleet_data]
current = [d[1] for d in fleet_data]
proposed = [d[2] for d in fleet_data]
deltas = [d[2] - d[1] for d in fleet_data]

x = np.arange(len(labels))
width = 0.35

# Current fleet bars (left, blue)
bars_curr = ax.bar(x - width/2, current, width, label='Current Fleet',
                   color='#90CAF9', edgecolor='white', linewidth=1.2)
# Proposed fleet bars (right, colored by change)
proposed_colors = [COLORS['success'] if d > 0 else (COLORS['danger'] if d < 0 else '#9E9E9E') for d in deltas]
bars_prop = ax.bar(x + width/2, proposed, width, label='Proposed Fleet',
                   color=proposed_colors, edgecolor='white', linewidth=1.2)

# Labels on current bars
for bar, val in zip(bars_curr, current):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, str(val),
            ha='center', va='bottom', fontsize=11, fontweight='bold', color=COLORS['primary'])

# Labels on proposed bars with delta annotation
for bar, val, delta in zip(bars_prop, proposed, deltas):
    # Proposed count
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, str(val),
            ha='center', va='bottom', fontsize=11, fontweight='bold',
            color=COLORS['success'] if delta > 0 else (COLORS['danger'] if delta < 0 else '#666'))
    # Delta badge above
    if delta != 0:
        delta_str = f'+{delta}' if delta > 0 else str(delta)
        badge_color = COLORS['success'] if delta > 0 else COLORS['danger']
        ax.annotate(delta_str, xy=(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6),
                    fontsize=10, fontweight='bold', ha='center', va='bottom', color='white',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=badge_color, edgecolor='none', alpha=0.9))

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_title('Fleet Reallocation: Current vs Proposed (Budget-Neutral, Total = 81 Buses)',
             fontsize=14, fontweight='bold')
ax.set_ylabel('Number of Buses')
ax.set_ylim(0, 13)
ax.axhline(y=0, color='black', linewidth=0.5)

from matplotlib.patches import Patch
legend_patches = [
    Patch(color='#90CAF9', label='Current Fleet'),
    Patch(color=COLORS['success'], label='Proposed (Increase)'),
    Patch(color=COLORS['danger'], label='Proposed (Decrease)'),
    Patch(color='#9E9E9E', label='Proposed (No Change)')
]
ax.legend(handles=legend_patches, loc='upper right', fontsize=9)

add_inference(ax,
    "INFERENCE: 11 buses redistributed with zero new purchases. X28 goes from 7 to 10 buses\n"
    "(headway drops 20 to 12 min). C04 and F12 drop from 7 to 4 each (low-density routes).\n"
    "Blue = current, colored = proposed. Badges show the change.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '11_fleet_reallocation.png', dpi=150)
plt.close()
print("  [11/12] Fleet reallocation (with current counts)")

# ============================================================
# CHART 12: Day-of-Week Heatmap
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

dow_names = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri\n(Wknd)', 5: 'Sat\n(Wknd)', 6: 'Sun'}
recent = master_df[master_df['Date'] >= '2025-01-01']
recent_daily = recent.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
recent_daily['DayOfWeek'] = recent_daily['Date'].dt.dayofweek

heatmap_data = recent_daily.groupby(['Route_Code', 'DayOfWeek'])['Total_Pax'].mean().reset_index()
heatmap_pivot = heatmap_data.pivot(index='Route_Code', columns='DayOfWeek', values='Total_Pax')
route_order = heatmap_pivot.sum(axis=1).sort_values(ascending=True).index
heatmap_pivot = heatmap_pivot.reindex(route_order)

sns.heatmap(heatmap_pivot, cmap='YlOrRd', annot=True, fmt='.0f', linewidths=0.5,
            xticklabels=[dow_names[i] for i in range(7)], ax=ax, cbar_kws={'label': 'Avg Daily Pax'})

ax.set_title('Day-of-Week Demand Heatmap by Route (H1 2025)', fontsize=14, fontweight='bold')
ax.set_ylabel('Route')
ax.set_xlabel('')

fig.text(0.5, -0.01,
    "INFERENCE: Wednesday is the peak day for most routes (darkest cells). Friday/Saturday (Dubai weekend) show a\n"
    "visible drop across all routes, especially Express (-8%). Timetabling should use 3 tiers: Peak (Sun-Thu), Reduced (Fri), Minimal (Sat).",
    ha='center', fontsize=9, style='italic',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9))

plt.tight_layout()
plt.savefig(CHART_DIR / '12_dow_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [12/12] Day-of-week heatmap")

# ============================================================
print(f"\n{'='*50}")
print(f"All 12 charts saved to: {CHART_DIR}")
print(f"{'='*50}")
for c in sorted(CHART_DIR.glob('*.png')): print(f"  {c.name}")
print(f"\nTotal: {len(list(CHART_DIR.glob('*.png')))} charts ready")
