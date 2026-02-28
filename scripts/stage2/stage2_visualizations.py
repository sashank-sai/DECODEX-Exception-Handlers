"""
DECODE X 2026 — Stage 2 Visualizations
========================================
Charts for structural break detection, forecast recalibration, and revised fleet.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.patches import Patch
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(r'c:\Users\asus\Desktop\decodex')
CHART_DIR = DATA_DIR / 'charts'
CHART_DIR.mkdir(exist_ok=True)

plt.style.use('seaborn-v0_8-darkgrid')
COLORS = {
    'City': '#2196F3', 'Express': '#F44336', 'Feeder': '#4CAF50', 'Intercity': '#FF9800',
    'primary': '#1976D2', 'danger': '#D32F2F', 'success': '#388E3C', 'warning': '#F57C00',
}
matplotlib.rc('font', family='sans-serif', size=11)

# Load data
master_df = pd.read_csv(DATA_DIR / 'master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])
forecast_df = pd.read_csv(DATA_DIR / 'forecast_h2_2025.csv')
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])
shock_ride = pd.read_csv(DATA_DIR / 'Shock_Ridership_2025_Q3.csv')
shock_ride['Date'] = pd.to_datetime(shock_ride['Date'])
shock_ride['Total_Pax'] = shock_ride['Boarding_Count'] + shock_ride['Alighting_Count']
routes_df = pd.read_csv(DATA_DIR / 'Bus_Routes.csv')
shock_ride = shock_ride.merge(routes_df[['Route_ID', 'Route_Length_km']].drop_duplicates(), on='Route_ID', how='left')

def add_inference(ax, text, x=0.02, y=0.02, fontsize=9):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fontsize,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9),
            style='italic', wrap=True)

print("Generating Stage 2 charts...\n")

# ============================================================
# CHART S2-1: Forecast vs Actual Deviation by Route (Waterfall)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

q3_fcast = forecast_df[(forecast_df['Date'] >= '2025-07-01') & (forecast_df['Date'] <= '2025-09-30')]
q3_fcast_route = q3_fcast.groupby(['Route_Code', 'Route_Type'])['Forecast_Total_Pax'].sum().reset_index()
q3_actual_route = shock_ride.groupby(['Route_Code', 'Route_Type'])['Total_Pax'].sum().reset_index()
comp = q3_fcast_route.merge(q3_actual_route, on=['Route_Code', 'Route_Type'], suffixes=('_fcast', '_actual'))
comp['Dev%'] = ((comp['Total_Pax'] / comp['Forecast_Total_Pax']) - 1) * 100
comp = comp.sort_values('Dev%')

colors = [COLORS['danger'] if d < -5 else (COLORS['success'] if d > 5 else '#9E9E9E') for d in comp['Dev%']]
bars = ax.bar(comp['Route_Code'] + '\n(' + comp['Route_Type'].str[:4] + ')', comp['Dev%'],
              color=colors, edgecolor='white', width=0.65)

ax.axhline(y=0, color='black', linewidth=0.8)
ax.axhspan(-5, 5, alpha=0.1, color='gray', label='Acceptable ±5%')

for bar, (_, row) in zip(bars, comp.iterrows()):
    val = row['Dev%']
    y_pos = val + 1 if val >= 0 else val - 1
    va = 'bottom' if val >= 0 else 'top'
    ax.text(bar.get_x() + bar.get_width()/2, y_pos, f'{val:+.1f}%',
            ha='center', va=va, fontsize=11, fontweight='bold')

ax.set_title('Stage 1 Forecast vs Q3 Actual: Route-Level Deviation', fontsize=14, fontweight='bold')
ax.set_ylabel('Deviation from Forecast (%)')
ax.set_ylim(-35, 65)

legend_patches = [
    Patch(color=COLORS['success'], label='EXCEEDED forecast (>+5%)'),
    Patch(color=COLORS['danger'], label='BELOW forecast (<-5%)'),
    Patch(facecolor='gray', alpha=0.2, label='Acceptable range (±5%)'),
]
ax.legend(handles=legend_patches, loc='upper left', fontsize=10)

add_inference(ax,
    "INFERENCE: Metro Phase 2 created a dramatic structural break. Express routes surged\n"
    "+47-51% above forecast (riders shifted FROM metro-parallel bus routes TO express).\n"
    "Feeder routes contracted -7 to -22% (riders switched directly to Metro).",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / 's2_01_forecast_deviation.png', dpi=150)
plt.close()
print("  [1/6] Forecast deviation")

# ============================================================
# CHART S2-2: Demand Redistribution (Before/After Metro)
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Before: H1 2025
h1 = master_df[master_df['Date'] >= '2025-01-01']
h1_type = h1.groupby([h1['Date'], 'Route_Type'])['Total_Pax'].sum().reset_index()
h1_type_avg = h1_type.groupby('Route_Type')['Total_Pax'].mean()

# After: Q3 2025
q3_type = shock_ride.groupby([shock_ride['Date'], 'Route_Type'])['Total_Pax'].sum().reset_index()
q3_type_avg = q3_type.groupby('Route_Type')['Total_Pax'].mean()

type_order = ['City', 'Express', 'Feeder', 'Intercity']
type_colors = [COLORS[t] for t in type_order]

# Pie 1: H1 2025
h1_vals = [h1_type_avg.get(t, 0) for t in type_order]
axes[0].pie(h1_vals, labels=type_order, colors=type_colors, autopct='%1.1f%%',
            pctdistance=0.8, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
axes[0].set_title('Pre-Metro (H1 2025)', fontsize=13, fontweight='bold')
axes[0].text(0, -1.4, f'Total: {sum(h1_vals):,.0f}/day', ha='center', fontsize=10, style='italic')

# Pie 2: Q3 2025
q3_vals = [q3_type_avg.get(t, 0) for t in type_order]
axes[1].pie(q3_vals, labels=type_order, colors=type_colors, autopct='%1.1f%%',
            pctdistance=0.8, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
axes[1].set_title('Post-Metro (Q3 2025)', fontsize=13, fontweight='bold')
axes[1].text(0, -1.4, f'Total: {sum(q3_vals):,.0f}/day', ha='center', fontsize=10, style='italic')

fig.suptitle('Demand Redistribution: Metro Phase 2 Impact', fontsize=14, fontweight='bold', y=1.02)

fig.text(0.5, -0.04,
    "INFERENCE: Express share jumped from 24.2% to 31.0% (+7pp), while Feeder dropped from 24.4% to 18.5% (-6pp).\n"
    "Total daily demand is roughly stable (+1.3%), but the INTERNAL mix has permanently shifted.",
    ha='center', fontsize=9, style='italic',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9))

plt.tight_layout()
plt.savefig(CHART_DIR / 's2_02_demand_redistribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [2/6] Demand redistribution")

# ============================================================
# CHART S2-3: Monthly Timeline with Structural Break
# ============================================================
fig, ax = plt.subplots(figsize=(14, 6))

# Historical monthly
monthly = master_df.groupby(master_df['Date'].dt.to_period('M'))['Total_Pax'].sum()
monthly.index = monthly.index.to_timestamp()
ax.plot(monthly.index, monthly.values, color=COLORS['primary'], linewidth=2, label='Historical Actual')

# Stage 1 forecast (full H2)
fcast_monthly = forecast_df.groupby(forecast_df['Date'].dt.to_period('M'))['Forecast_Total_Pax'].sum()
fcast_monthly.index = fcast_monthly.index.to_timestamp()
ax.plot(fcast_monthly.index, fcast_monthly.values, color='#9E9E9E', linewidth=2,
        linestyle='--', label='Stage 1 Forecast', alpha=0.6)

# Q3 actuals (shock)
q3_monthly = shock_ride.groupby(shock_ride['Date'].dt.to_period('M'))['Total_Pax'].sum()
q3_monthly.index = q3_monthly.index.to_timestamp()
ax.plot(q3_monthly.index, q3_monthly.values, color=COLORS['danger'], linewidth=3,
        label='Q3 Actual (Post-Metro)', marker='o', markersize=8)

# Revised forecast (Q4)
revised_df = pd.read_csv(DATA_DIR / 'revised_forecast_q4_2025.csv')
revised_df['Date'] = pd.to_datetime(revised_df['Date'])
rev_monthly = revised_df.groupby(revised_df['Date'].dt.to_period('M'))['Forecast_Total_Pax'].sum()
rev_monthly.index = rev_monthly.index.to_timestamp()
ax.plot(rev_monthly.index, rev_monthly.values, color=COLORS['success'], linewidth=2,
        linestyle='--', label='Revised Q4 Forecast', marker='s', markersize=6)

# Structural break line
ax.axvline(x=pd.Timestamp('2025-07-01'), color='red', linewidth=2, linestyle='-.',
           alpha=0.7, label='Metro Phase 2 Launch')
ax.text(pd.Timestamp('2025-07-15'), ax.get_ylim()[1]*0.95, 'METRO\nPHASE 2', color='red',
        fontsize=10, fontweight='bold', va='top')

ax.set_title('Demand Timeline: Structural Break at Metro Phase 2 Launch', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))
ax.legend(loc='upper left', fontsize=9)
ax.set_xlim(pd.Timestamp('2024-01-01'), pd.Timestamp('2026-01-01'))

add_inference(ax,
    "INFERENCE: Q3 actuals (red) are significantly ABOVE Stage 1 forecast (gray dashed).\n"
    "The revised Q4 forecast (green dashed) accounts for the metro-driven demand shift.\n"
    "December 2025 is now projected at ~1.2M passengers — 10% above original forecast.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / 's2_03_timeline_break.png', dpi=150)
plt.close()
print("  [3/6] Timeline with break")

# ============================================================
# CHART S2-4: Express Surge vs Feeder Contraction
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

# Level shift by route
h1_daily = master_df[master_df['Date'] >= '2025-01-01'].groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
h1_avg = h1_daily.groupby('Route_Code')['Total_Pax'].mean()
q3_daily = shock_ride.groupby(['Date', 'Route_Code'])['Total_Pax'].sum().reset_index()
q3_avg = q3_daily.groupby('Route_Code')['Total_Pax'].mean()

routes_sorted = q3_avg.sort_values().index
route_types = {r['Route_Code']: r['Route_Type'] for _, r in routes_df.iterrows()}

x = np.arange(len(routes_sorted))
width = 0.35

h1_bars = ax.bar(x - width/2, [h1_avg.get(r, 0) for r in routes_sorted], width,
                 label='Pre-Metro (H1 2025)', color='#90CAF9', edgecolor='white')
q3_bars = ax.bar(x + width/2, [q3_avg.get(r, 0) for r in routes_sorted], width,
                 label='Post-Metro (Q3 2025)',
                 color=[COLORS.get(route_types.get(r, ''), '#999') for r in routes_sorted],
                 edgecolor='white')

# Change arrows
for i, route in enumerate(routes_sorted):
    change = ((q3_avg.get(route, 0) / h1_avg.get(route, 1)) - 1) * 100
    color = COLORS['success'] if change > 5 else (COLORS['danger'] if change < -5 else '#666')
    ax.text(i + width/2, q3_avg.get(route, 0) + 50, f'{change:+.0f}%',
            ha='center', va='bottom', fontsize=9, fontweight='bold', color=color)

ax.set_xticks(x)
labels = [f'{r}\n({route_types.get(r, "")[:4]})' for r in routes_sorted]
ax.set_xticklabels(labels, fontsize=9)
ax.set_title('Pre-Metro vs Post-Metro: Route-Level Demand Shift', fontsize=14, fontweight='bold')
ax.set_ylabel('Avg Daily Passengers')
ax.legend(fontsize=10)

add_inference(ax,
    "INFERENCE: Express routes (X11, X28, X66) surged +29-32%. Feeder routes (F18, F12, F25)\n"
    "contracted -18 to -31%. City routes remained stable (+1-5%). This is a permanent demand\n"
    "redistribution — riders switched from feeder buses to Metro, increasing Express pressure.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / 's2_04_express_vs_feeder.png', dpi=150)
plt.close()
print("  [4/6] Express vs feeder")

# ============================================================
# CHART S2-5: Revised Fleet Allocation (Stage 1 vs Stage 2)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

fleet_data = [
    ('X28\n(Exp)', 10, 11), ('C03\n(City)', 10, 11), ('X66\n(Exp)', 6, 8),
    ('C02\n(City)', 7, 7), ('C01\n(City)', 7, 7), ('E22\n(Inter)', 8, 7),
    ('F25\n(Feed)', 9, 7), ('X11\n(Exp)', 5, 7),
    ('F18\n(Feed)', 7, 5), ('E16\n(Inter)', 4, 4), ('C04\n(City)', 4, 4),
    ('F12\n(Feed)', 4, 3),
]

labels = [d[0] for d in fleet_data]
s1_alloc = [d[1] for d in fleet_data]
s2_alloc = [d[2] for d in fleet_data]
deltas = [d[2] - d[1] for d in fleet_data]

x = np.arange(len(labels))
width = 0.35

bars1 = ax.bar(x - width/2, s1_alloc, width, label='Stage 1 Allocation',
               color='#90CAF9', edgecolor='white')
stage2_colors = [COLORS['success'] if d > 0 else (COLORS['danger'] if d < 0 else '#9E9E9E') for d in deltas]
bars2 = ax.bar(x + width/2, s2_alloc, width, label='Stage 2 Revised',
               color=stage2_colors, edgecolor='white')

for bar, val in zip(bars1, s1_alloc):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, str(val),
            ha='center', va='bottom', fontsize=10, fontweight='bold', color=COLORS['primary'])

for bar, val, delta in zip(bars2, s2_alloc, deltas):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15, str(val),
            ha='center', va='bottom', fontsize=10, fontweight='bold',
            color=COLORS['success'] if delta > 0 else (COLORS['danger'] if delta < 0 else '#666'))
    if delta != 0:
        ds = f'+{delta}' if delta > 0 else str(delta)
        bc = COLORS['success'] if delta > 0 else COLORS['danger']
        ax.annotate(ds, xy=(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.6),
                    fontsize=9, fontweight='bold', ha='center', va='bottom', color='white',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=bc, edgecolor='none', alpha=0.9))

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_title('Fleet Reallocation: Stage 1 vs Stage 2 Revision (Total = 81 Buses)', fontsize=14, fontweight='bold')
ax.set_ylabel('Number of Buses')
ax.set_ylim(0, 14)

legend_patches = [
    Patch(color='#90CAF9', label='Stage 1 Allocation'),
    Patch(color=COLORS['success'], label='Stage 2: Increased'),
    Patch(color=COLORS['danger'], label='Stage 2: Decreased'),
    Patch(color='#9E9E9E', label='Stage 2: No Change'),
]
ax.legend(handles=legend_patches, loc='upper right', fontsize=9)

add_inference(ax,
    "INFERENCE: Metro Phase 2 shifts 6 more buses to Express routes. X11 jumps from 5 to 7\n"
    "(headway: 17→12 min), X66 from 6 to 8 (24→18 min). Feeder F25 loses 2, F18 loses 2.\n"
    "The fleet is now heavily Express-oriented to match the post-metro demand reality.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / 's2_05_fleet_revision.png', dpi=150)
plt.close()
print("  [5/6] Fleet revision")

# ============================================================
# CHART S2-6: Shift Classification Summary
# ============================================================
fig, ax = plt.subplots(figsize=(12, 8))

shift_data = {
    'X66': {'level': +32.2, 'vol': -2.2, 'type': 'Express'},
    'X11': {'level': +28.6, 'vol': -12.9, 'type': 'Express'},
    'X28': {'level': +28.9, 'vol': -0.3, 'type': 'Express'},
    'C04': {'level': +4.7, 'vol': -14.2, 'type': 'City'},
    'C03': {'level': +2.7, 'vol': -11.3, 'type': 'City'},
    'C01': {'level': +0.9, 'vol': -9.5, 'type': 'City'},
    'C02': {'level': +0.7, 'vol': -11.7, 'type': 'City'},
    'E16': {'level': -7.8, 'vol': -4.9, 'type': 'Intercity'},
    'E22': {'level': -8.6, 'vol': -4.3, 'type': 'Intercity'},
    'F25': {'level': -18.2, 'vol': -4.4, 'type': 'Feeder'},
    'F12': {'level': -20.2, 'vol': -13.6, 'type': 'Feeder'},
    'F18': {'level': -31.2, 'vol': -17.5, 'type': 'Feeder'},
}

for route, data in shift_data.items():
    color = COLORS.get(data['type'], '#999')
    ax.scatter(data['level'], data['vol'], c=color, s=200, edgecolors='white', linewidth=1.5, zorder=5)
    ax.annotate(route, (data['level'], data['vol']), fontsize=10, fontweight='bold',
                xytext=(8, 5), textcoords='offset points')

ax.axhline(y=0, color='gray', linewidth=0.5, linestyle='--')
ax.axvline(x=0, color='gray', linewidth=0.5, linestyle='--')

# Quadrant labels
ax.text(30, 5, 'Demand ↑\nVolatility ↑', fontsize=9, color='#999', ha='center', style='italic')
ax.text(30, -15, 'Demand ↑\nVolatility ↓', fontsize=9, color='#999', ha='center', style='italic')
ax.text(-25, 5, 'Demand ↓\nVolatility ↑', fontsize=9, color='#999', ha='center', style='italic')
ax.text(-25, -15, 'Demand ↓\nVolatility ↓', fontsize=9, color='#999', ha='center', style='italic')

ax.set_xlabel('Level Shift (% change in avg daily demand)', fontsize=11)
ax.set_ylabel('Volatility Shift (% change in demand CV)', fontsize=11)
ax.set_title('Structural Break Classification: Level vs Volatility Shift by Route', fontsize=14, fontweight='bold')

legend_patches = [Patch(color=COLORS[t], label=t) for t in ['City', 'Express', 'Feeder', 'Intercity']]
ax.legend(handles=legend_patches, loc='upper left', fontsize=10)

add_inference(ax,
    "INFERENCE: Express routes cluster in bottom-right (demand ↑, volatility ↓) — steady surge.\n"
    "Feeder routes cluster left (demand ↓) — structural contraction. City routes are near origin\n"
    "(stable). All routes show LOWER volatility post-metro — the new pattern is predictable.",
    x=0.3, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / 's2_06_shift_classification.png', dpi=150)
plt.close()
print("  [6/6] Shift classification")

print(f"\n{'='*50}")
print(f"All 6 Stage 2 charts saved to: {CHART_DIR}")
print(f"{'='*50}")
for c in sorted(CHART_DIR.glob('s2_*.png')): print(f"  {c.name}")
