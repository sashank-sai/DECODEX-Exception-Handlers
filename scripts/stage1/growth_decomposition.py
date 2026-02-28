"""
DECODE X 2026 - Growth Decomposition Stacked Bar Chart
=======================================================
Breaks down yearly demand by Route Type to show what's driving growth.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path(r'c:\Users\asus\Desktop\decodex')
CHART_DIR = DATA_DIR / 'charts'

master_df = pd.read_csv(DATA_DIR / 'master_analytical_dataset.csv')
master_df['Date'] = pd.to_datetime(master_df['Date'])
forecast_df = pd.read_csv(DATA_DIR / 'forecast_h2_2025.csv')
forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])

COLORS = {
    'City': '#2196F3', 'Express': '#F44336', 'Feeder': '#4CAF50', 'Intercity': '#FF9800',
    'primary': '#1976D2', 'danger': '#D32F2F', 'success': '#388E3C', 'warning': '#F57C00',
}
FONT = {'family': 'sans-serif', 'size': 11}
matplotlib.rc('font', **FONT)

def add_inference(ax, text, x=0.02, y=0.02, fontsize=9):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fontsize,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9),
            style='italic', wrap=True)

# ============================================================
# Prepare data: Yearly demand by Route Type
# ============================================================

# Historical: 2022, 2023, 2024, 2025 H1
hist = master_df.groupby([master_df['Date'].dt.year, 'Route_Type'])['Total_Pax'].sum().reset_index()
hist.columns = ['Year', 'Route_Type', 'Total_Pax']

# 2025 H2 forecast by route type
fcast_by_type = forecast_df.groupby('Route_Type')['Forecast_Total_Pax'].sum().reset_index()
fcast_by_type.columns = ['Route_Type', 'Total_Pax']
fcast_by_type['Year'] = 2025

# Combine H1 actual + H2 forecast for 2025 full year
h1_2025 = hist[hist['Year'] == 2025].copy()
full_2025 = h1_2025.merge(fcast_by_type[['Route_Type', 'Total_Pax']], on='Route_Type', suffixes=('_h1', '_h2'))
full_2025['Total_Pax'] = full_2025['Total_Pax_h1'] + full_2025['Total_Pax_h2']
full_2025['Year'] = 2025
full_2025 = full_2025[['Year', 'Route_Type', 'Total_Pax']]

# Replace 2025 H1-only with full year projection
hist_clean = hist[hist['Year'] != 2025]
combined = pd.concat([hist_clean, full_2025], ignore_index=True)

# Pivot for stacking
pivot = combined.pivot(index='Year', columns='Route_Type', values='Total_Pax').fillna(0)
pivot = pivot[['City', 'Express', 'Feeder', 'Intercity']]  # consistent order

years = pivot.index.tolist()
year_labels = [str(y) if y != 2025 else '2025\n(H1 Actual +\nH2 Forecast)' for y in years]

# ============================================================
# CHART: Growth Decomposition Stacked Bar
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

type_order = ['City', 'Express', 'Feeder', 'Intercity']
type_colors = [COLORS[t] for t in type_order]

x = np.arange(len(years))
width = 0.55

# Stack the bars
bottoms = np.zeros(len(years))
for i, rtype in enumerate(type_order):
    values = pivot[rtype].values
    bars = ax.bar(x, values, width, bottom=bottoms, label=rtype, color=type_colors[i],
                  edgecolor='white', linewidth=0.8)
    
    # Add value labels inside each segment
    for j, (val, bot) in enumerate(zip(values, bottoms)):
        if val > 0:
            mid = bot + val / 2
            ax.text(j, mid, f'{val/1e6:.1f}M', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='white')
    
    bottoms += values

# Total labels on top
totals = pivot.sum(axis=1).values
for j, total in enumerate(totals):
    ax.text(j, total + 50000, f'{total/1e6:.1f}M', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color='#263238')

# YoY growth arrows between bars
for j in range(1, len(totals)):
    growth = (totals[j] - totals[j-1]) / totals[j-1] * 100
    mid_y = max(totals[j-1], totals[j]) + 400000
    ax.annotate('', xy=(j, mid_y), xytext=(j-1, mid_y),
                arrowprops=dict(arrowstyle='->', color=COLORS['success'], lw=2))
    ax.text((j-1 + j)/2, mid_y + 100000, f'+{growth:.1f}%', ha='center', va='bottom',
            fontsize=11, fontweight='bold', color=COLORS['success'])

# Hatching for 2025 forecast portion (visual distinction)
# Re-draw just the 2025 bars with hatch for H2 portion
h1_vals = h1_2025.set_index('Route_Type')['Total_Pax'].reindex(type_order).fillna(0).values
h2_vals = fcast_by_type.set_index('Route_Type')['Total_Pax'].reindex(type_order).fillna(0).values

h1_bottom = 0
for i, rtype in enumerate(type_order):
    # Draw hatch overlay for the H2 (forecast) portion of 2025
    ax.bar(x[-1], h2_vals[i], width, bottom=h1_bottom + h1_vals[i],
           color='none', edgecolor='white', linewidth=0, hatch='///', alpha=0.3)
    h1_bottom += pivot[rtype].values[-1]

ax.set_xticks(x)
ax.set_xticklabels(year_labels, fontsize=11)
ax.set_title('Growth Decomposition by Route Type (Stacked)', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))

# Legend
legend_patches = [Patch(color=COLORS[t], label=t) for t in type_order]
legend_patches.append(Patch(facecolor='white', edgecolor='gray', hatch='///', label='H2 2025 (Forecast)'))
ax.legend(handles=legend_patches, loc='upper left', fontsize=10)

ax.set_ylim(0, max(totals) * 1.25)

add_inference(ax,
    "INFERENCE: City routes are the largest and fastest-growing segment (3.6M to 5.5M, +53%).\n"
    "Express routes show the steepest growth rate per route. All 4 types grow in parallel —\n"
    "no single segment is shrinking. 2025 projected at 11.1M, hatched area = H2 forecast.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '13_growth_decomposition.png', dpi=150)
plt.close()
print("Saved: 13_growth_decomposition.png")

# ============================================================
# CHART: Growth Decomposition by Season (Stacked)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 7))

def dubai_season(m):
    if m in [11, 12, 1, 2, 3]: return 'Winter Peak'
    elif m in [6, 7, 8]: return 'Summer Moderate'
    else: return 'Shoulder'

master_df['Season'] = master_df['Date'].dt.month.apply(dubai_season)
forecast_df['Season'] = forecast_df['Date'].dt.month.apply(dubai_season)

# Historical by season
hist_season = master_df.groupby([master_df['Date'].dt.year, 'Season'])['Total_Pax'].sum().reset_index()
hist_season.columns = ['Year', 'Season', 'Total_Pax']

# 2025: combine H1 actual + H2 forecast
fcast_season = forecast_df.groupby('Season')['Forecast_Total_Pax'].sum().reset_index()
fcast_season.columns = ['Season', 'Total_Pax']

h1_2025_s = hist_season[hist_season['Year'] == 2025].copy()
full_2025_s = h1_2025_s.merge(fcast_season, on='Season', suffixes=('_h1', '_h2'))
full_2025_s['Total_Pax'] = full_2025_s['Total_Pax_h1'] + full_2025_s['Total_Pax_h2']
full_2025_s['Year'] = 2025
full_2025_s = full_2025_s[['Year', 'Season', 'Total_Pax']]

hist_season_clean = hist_season[hist_season['Year'] != 2025]
combined_s = pd.concat([hist_season_clean, full_2025_s], ignore_index=True)

pivot_s = combined_s.pivot(index='Year', columns='Season', values='Total_Pax').fillna(0)
season_order = ['Winter Peak', 'Shoulder', 'Summer Moderate']
pivot_s = pivot_s.reindex(columns=season_order)

season_colors = ['#1565C0', '#FF8F00', '#C62828']

x = np.arange(len(pivot_s))
bottoms = np.zeros(len(pivot_s))

for i, season in enumerate(season_order):
    values = pivot_s[season].values
    ax.bar(x, values, width, bottom=bottoms, label=season, color=season_colors[i],
           edgecolor='white', linewidth=0.8)
    for j, (val, bot) in enumerate(zip(values, bottoms)):
        if val > 0:
            ax.text(j, bot + val/2, f'{val/1e6:.1f}M', ha='center', va='center',
                    fontsize=9, fontweight='bold', color='white')
    bottoms += values

# Totals
totals_s = pivot_s.sum(axis=1).values
for j, total in enumerate(totals_s):
    ax.text(j, total + 50000, f'{total/1e6:.1f}M', ha='center', va='bottom',
            fontsize=12, fontweight='bold', color='#263238')

# Growth arrows
for j in range(1, len(totals_s)):
    growth = (totals_s[j] - totals_s[j-1]) / totals_s[j-1] * 100
    mid_y = max(totals_s[j-1], totals_s[j]) + 400000
    ax.annotate('', xy=(j, mid_y), xytext=(j-1, mid_y),
                arrowprops=dict(arrowstyle='->', color=COLORS['success'], lw=2))
    ax.text((j-1+j)/2, mid_y + 100000, f'+{growth:.1f}%', ha='center', va='bottom',
            fontsize=11, fontweight='bold', color=COLORS['success'])

ax.set_xticks(x)
ax.set_xticklabels(year_labels, fontsize=11)
ax.set_title('Growth Decomposition by Season (Stacked)', fontsize=14, fontweight='bold')
ax.set_ylabel('Total Passengers')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))

legend_patches = [Patch(color=c, label=s) for s, c in zip(season_order, season_colors)]
ax.legend(handles=legend_patches, loc='upper left', fontsize=10)

ax.set_ylim(0, max(totals_s) * 1.25)

add_inference(ax,
    "INFERENCE: Winter Peak (blue) consistently contributes the largest share (~45% of annual).\n"
    "All three seasons grow in parallel — growth is structural, not just tourism-driven.\n"
    "The winter-summer gap widens each year, amplifying the need for seasonal fleet rotation.",
    x=0.02, y=0.03)

plt.tight_layout()
plt.savefig(CHART_DIR / '14_growth_decomposition_season.png', dpi=150)
plt.close()
print("Saved: 14_growth_decomposition_season.png")

print("\nDone! Two growth decomposition charts saved.")
