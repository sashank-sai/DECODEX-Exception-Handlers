"""
DECODE X 2026 — Stage 3 Visualizations
========================================
Polished charts for the accountability audit.
Uses hardcoded results from stage3_output.txt to avoid data/path issues.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import Patch, FancyBboxPatch
from pathlib import Path

plt.style.use('seaborn-v0_8-darkgrid')
matplotlib.rc('font', family='sans-serif', size=11)

CHART_DIR = Path(r'c:\Users\asus\Desktop\decodex\charts\stage3')
CHART_DIR.mkdir(parents=True, exist_ok=True)

BLUE = '#1976D2'
RED = '#D32F2F'
GREEN = '#388E3C'
ORANGE = '#F57C00'
GRAY = '#9E9E9E'
COLORS = {'City': '#2196F3', 'Express': '#F44336', 'Feeder': '#4CAF50', 'Intercity': '#FF9800'}

def add_inference(ax, text, x=0.5, y=0.97, fontsize=9, ha='center', va='top'):
    ax.text(x, y, text, transform=ax.transAxes, fontsize=fontsize,
            verticalalignment=va, horizontalalignment=ha,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9),
            style='italic', wrap=True)

print("Generating Stage 3 charts...\n")

# ============================================================
# CHART S3-01: Forecast MAPE Comparison (S1 vs S2)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

routes =   ['C01', 'C02', 'C03', 'C04', 'E16', 'E22', 'F12', 'F18', 'F25', 'X11', 'X28', 'X66']
rtypes =   ['City','City','City','City','Inter','Inter','Feed','Feed','Feed','Exp','Exp','Exp']
s1_mape =  [13.8, 13.7, 14.9, 17.0, 6.0, 5.0, 9.7, 28.5, 7.2, 33.0, 32.0, 33.9]
s2_mape =  [2.2, 1.8, 1.2, 4.4, 5.1, 3.2, 15.8, 10.2, 18.3, 12.1, 10.3, 12.1]

x = np.arange(len(routes))
w = 0.35

bars1 = ax.bar(x - w/2, s1_mape, w, label='Stage 1 MAPE (pre-metro)',
               color='#EF9A9A', edgecolor='white', zorder=3)
bars2 = ax.bar(x + w/2, s2_mape, w, label='Stage 2 MAPE (recalibrated)',
               color='#81C784', edgecolor='white', zorder=3)

# Value labels
for bar, val in zip(bars1, s1_mape):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold', color=RED)
for bar, val in zip(bars2, s2_mape):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold', color=GREEN)

# Improvement arrows
for i in range(len(routes)):
    improvement = s1_mape[i] - s2_mape[i]
    if improvement > 0:
        ax.annotate(f'-{improvement:.0f}pp', xy=(x[i], max(s1_mape[i], s2_mape[i]) + 3),
                    fontsize=7, ha='center', color=GREEN, fontweight='bold')

ax.axhline(y=5, color=GRAY, linewidth=1, linestyle=':', alpha=0.7, label='Acceptable threshold (5%)')

labels = [f'{r}\n({t})' for r, t in zip(routes, rtypes)]
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel('MAPE (%)', fontsize=12)
ax.set_title('Forecast Performance Audit: Stage 1 vs Stage 2 MAPE by Route', fontsize=14, fontweight='bold')
ax.set_ylim(0, 40)
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

add_inference(ax,
    "INFERENCE: Recalibration halved overall MAPE (17.9% to 8.1%, +6.5pp improvement). City routes achieved\n"
    "near-perfect accuracy (1-4% MAPE). Express and Feeder routes still show 10-18% error — the shock\n"
    "partially reverted, causing Stage 2 to OVERREACT on these route types.",
    x=0.5, y=0.97)

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_01_mape_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [1/6] MAPE comparison")

# ============================================================
# CHART S3-02: Demand Trajectory H1 → Q3 → Q4 by Route Type
# ============================================================
fig, ax = plt.subplots(figsize=(13, 7))

types = ['City', 'Express', 'Feeder', 'Intercity']
h1_vals = [12008, 7542, 7609, 4013]
q3_vals = [12267, 9792, 5824, 3683]
q4_vals = [13994, 9686, 6357, 4138]

x = np.arange(len(types))
w = 0.25

bars_h1 = ax.bar(x - w, h1_vals, w, label='H1 2025 (Baseline)', color='#90CAF9', edgecolor='white')
bars_q3 = ax.bar(x, q3_vals, w, label='Q3 2025 (Metro Shock)', color='#EF9A9A', edgecolor='white')
bars_q4 = ax.bar(x + w, q4_vals, w, label='Q4 2025 (Stabilized)', color='#A5D6A7', edgecolor='white')

# Labels and change annotations
for i in range(len(types)):
    ax.text(x[i] - w, h1_vals[i] + 80, f'{h1_vals[i]:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax.text(x[i], q3_vals[i] + 80, f'{q3_vals[i]:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax.text(x[i] + w, q4_vals[i] + 80, f'{q4_vals[i]:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # H1→Q4 net change
    net = ((q4_vals[i] / h1_vals[i]) - 1) * 100
    color = GREEN if net > 0 else RED
    ax.annotate(f'Net: {net:+.1f}%', xy=(x[i], max(h1_vals[i], q3_vals[i], q4_vals[i]) + 500),
                fontsize=9, ha='center', fontweight='bold', color=color,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.8))

ax.set_xticks(x)
ax.set_xticklabels(types, fontsize=12, fontweight='bold')
ax.set_ylabel('Avg Daily Passengers', fontsize=12)
ax.set_title('Demand Trajectory: Baseline → Metro Shock → Stabilized Equilibrium', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}K'))
ax.set_ylim(0, 16000)
ax.legend(fontsize=10, loc='upper right', framealpha=0.9)

add_inference(ax,
    "INFERENCE: Express surged +29.8% in Q3 then moderated -1.1% in Q4 — demand plateaued at +28.4% above\n"
    "baseline. Feeder contracted -23.5% then recovered +9.1% — floor found at -16.5%. City grew steadily\n"
    "throughout (+16.5% net). The network entered a REDISTRIBUTED EQUILIBRIUM, not a full reversion.",
    x=0.5, y=0.97)

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_02_demand_trajectory.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [2/6] Demand trajectory")

# ============================================================
# CHART S3-03: Structural Permanence (Q3 Dev vs Q4 Dev)
# ============================================================
fig, ax = plt.subplots(figsize=(12, 8))

permanence = {
    'C01': (13.8, -2.2, 'City'), 'C02': (13.7, 1.8, 'City'),
    'C03': (14.9, -1.2, 'City'), 'C04': (17.0, -4.4, 'City'),
    'E16': (6.0, -5.1, 'Intercity'), 'E22': (5.0, -3.2, 'Intercity'),
    'F12': (-9.7, -15.8, 'Feeder'), 'F18': (-28.5, -10.2, 'Feeder'),
    'F25': (-7.2, -18.3, 'Feeder'),
    'X11': (33.0, -12.1, 'Express'), 'X28': (32.0, -10.3, 'Express'),
    'X66': (33.9, -12.1, 'Express'),
}

# Quadrant shading
ax.axhspan(0, 40, xmin=0.5, xmax=1.0, alpha=0.04, color='green')    # top-right: persistent positive
ax.axhspan(-25, 0, xmin=0.5, xmax=1.0, alpha=0.04, color='orange')  # bottom-right: overreaction
ax.axhspan(0, 40, xmin=0.0, xmax=0.5, alpha=0.04, color='blue')     # top-left: recovery
ax.axhspan(-25, 0, xmin=0.0, xmax=0.5, alpha=0.04, color='red')     # bottom-left: deepening decline

ax.axhline(y=0, color='#424242', linewidth=1, alpha=0.5)
ax.axvline(x=0, color='#424242', linewidth=1, alpha=0.5)

# Perfect calibration line (Q4 dev = 0)
ax.axhline(y=0, color=GREEN, linewidth=1.5, linestyle='--', alpha=0.4, label='Perfect calibration')

offsets = {
    'C01': (8, 8), 'C02': (-40, -10), 'C03': (8, -12), 'C04': (-40, 8),
    'E16': (8, 8), 'E22': (8, -12),
    'F12': (8, 8), 'F18': (8, 5), 'F25': (-45, 5),
    'X11': (8, 8), 'X28': (8, -14), 'X66': (-40, 5),
}

for route, (q3d, q4d, rtype) in permanence.items():
    color = COLORS.get(rtype, GRAY)
    ax.scatter(q3d, q4d, c=color, s=250, edgecolors='white', linewidth=2, zorder=5)
    ox, oy = offsets.get(route, (8, 5))
    ax.annotate(route, (q3d, q4d), fontsize=10, fontweight='bold', color='#263238',
                xytext=(ox, oy), textcoords='offset points',
                arrowprops=dict(arrowstyle='-', color='gray', lw=0.8, alpha=0.5),
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='gray', alpha=0.7))

# Quadrant labels
ax.text(30, 2, 'Persistent Positive\n(under-forecast persists)', fontsize=9, color='#1B5E20',
        ha='center', fontweight='bold', alpha=0.5)
ax.text(30, -18, 'OVERREACTION\n(over-corrected)', fontsize=9, color=ORANGE,
        ha='center', fontweight='bold', alpha=0.5)
ax.text(-20, 2, 'Recovery\n(shock reversed)', fontsize=9, color=BLUE,
        ha='center', fontweight='bold', alpha=0.5)
ax.text(-20, -18, 'Deepening Decline\n(permanent shift)', fontsize=9, color=RED,
        ha='center', fontweight='bold', alpha=0.5)

ax.set_xlabel('Q3 Forecast Deviation (Stage 1 vs Actual, %)', fontsize=11, fontweight='bold')
ax.set_ylabel('Q4 Forecast Deviation (Stage 2 vs Actual, %)', fontsize=11, fontweight='bold')
ax.set_title('Structural Permanence: Was the Shock Permanent or Did We Overreact?', fontsize=14, fontweight='bold')
ax.set_xlim(-35, 40)
ax.set_ylim(-23, 5)

legend_patches = [Patch(color=COLORS[t], label=t) for t in ['City', 'Express', 'Feeder', 'Intercity']]
ax.legend(handles=legend_patches, loc='upper left', fontsize=10, framealpha=0.9)

add_inference(ax,
    "INFERENCE: Express routes (X11, X28, X66) cluster in OVERREACTION quadrant — Q3 surge was +33%,\n"
    "but Q4 shows -10 to -12% over-forecast. City routes near origin = well-calibrated. Feeder F25 and\n"
    "F12 in deepening decline = structural shift deeper than our adjustment captured.",
    x=0.5, y=0.03, va='bottom')

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_03_structural_permanence.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [3/6] Structural permanence")

# ============================================================
# CHART S3-04: Fleet Alignment (Pax/Bus vs Ideal)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

fleet_routes = ['C04', 'F12', 'C01', 'X11', 'E16', 'C02', 'F18', 'X66', 'C03', 'E22', 'F25', 'X28']
fleet_types =  ['City','Feed','City','Exp','Inter','City','Feed','Exp','City','Inter','Feed','Exp']
pax_bus =      [766, 686, 542, 475, 471, 470, 430, 381, 350, 322, 307, 301]
fleet_count =  [4, 3, 7, 7, 4, 7, 5, 8, 11, 7, 7, 11]
headways =     [35.0, 43.9, 16.6, 12.2, 30.8, 14.3, 28.6, 17.9, 10.4, 15.2, 18.9, 11.3]

x = np.arange(len(fleet_routes))
bar_colors = []
for pb in pax_bus:
    if pb > 500: bar_colors.append(RED)
    elif pb > 350: bar_colors.append(ORANGE)
    else: bar_colors.append(GREEN)

bars = ax.bar(x, pax_bus, color=bar_colors, edgecolor='white', width=0.6, zorder=3)

# Ideal zone
ax.axhspan(300, 450, alpha=0.1, color=GREEN, zorder=1)
ax.axhline(y=450, color=GREEN, linewidth=1, linestyle='--', alpha=0.5)
ax.axhline(y=300, color=GREEN, linewidth=1, linestyle='--', alpha=0.5)
ax.text(11.5, 375, 'IDEAL\nZONE', fontsize=9, color=GREEN, ha='center', fontweight='bold', alpha=0.6)

# Labels: fleet count + headway
for i, (bar, pb, fc, hw) in enumerate(zip(bars, pax_bus, fleet_count, headways)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
            f'{pb}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.text(bar.get_x() + bar.get_width()/2, 20,
            f'{fc} buses\n{hw:.0f} min', ha='center', va='bottom', fontsize=7, color='white', fontweight='bold')

labels = [f'{r}\n({t})' for r, t in zip(fleet_routes, fleet_types)]
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel('Passengers per Bus (daily)', fontsize=12)
ax.set_title('Strategic Alignment: Fleet vs Q4 Stabilized Demand', fontsize=14, fontweight='bold')
ax.set_ylim(0, 850)

legend_patches = [
    Patch(color=RED, label='Under-served (>500 pax/bus)'),
    Patch(color=ORANGE, label='Adequate (350-500 pax/bus)'),
    Patch(color=GREEN, label='Well-served (<350 pax/bus)'),
]
ax.legend(handles=legend_patches, loc='upper right', fontsize=9, framealpha=0.9)

add_inference(ax,
    "INFERENCE: C04 (766 pax/bus, 35 min headway) and F12 (686 pax/bus, 44 min) are critically\n"
    "under-served post-stabilization. C03 and X28 are well-served with 11 buses each. For 2026,\n"
    "C04 needs 2-3 more buses and F12 needs restructuring as a metro-connector route.",
    x=0.5, y=0.97)

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_04_fleet_alignment.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [4/6] Fleet alignment")

# ============================================================
# CHART S3-05: Elasticity Decay (H1 → Q3 → Q4)
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Left: Congestion elasticity over time
periods = ['H1 2025\n(Baseline)', 'Q3 2025\n(Metro Shock)', 'Q4 2025\n(Stabilized)']
elasticities = [720, 1447, 940]
cong_levels = [2.78, 3.09, 2.83]
speeds = [31.1, 29.2, 31.0]
period_colors = ['#90CAF9', '#EF9A9A', '#A5D6A7']

bars1 = ax1.bar(periods, elasticities, color=period_colors, edgecolor='white', width=0.5, zorder=3)
for bar, val in zip(bars1, elasticities):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
             f'+{val:,}', ha='center', va='bottom', fontsize=11, fontweight='bold')

# Arrows showing change
ax1.annotate('', xy=(1, 1447), xytext=(0, 720),
             arrowprops=dict(arrowstyle='->', color=RED, lw=2))
ax1.text(0.5, 1100, '+101%', ha='center', fontsize=10, color=RED, fontweight='bold')

ax1.annotate('', xy=(2, 940), xytext=(1, 1447),
             arrowprops=dict(arrowstyle='->', color=GREEN, lw=2))
ax1.text(1.5, 1200, '-35%', ha='center', fontsize=10, color=GREEN, fontweight='bold')

ax1.set_ylabel('Pax per Congestion Level', fontsize=11)
ax1.set_title('Congestion-Ridership Elasticity', fontsize=13, fontweight='bold')
ax1.set_ylim(0, 1700)

# Right: Route-type share trajectory
types_list = ['City', 'Express', 'Feeder', 'Intercity']
h1_share = [38.5, 24.2, 24.4, 12.9]
q3_share = [38.9, 31.0, 18.4, 11.7]
q4_share = [40.9, 28.3, 18.6, 12.1]

x2 = np.arange(3)
for i, (rtype, h1s, q3s, q4s) in enumerate(zip(types_list, h1_share, q3_share, q4_share)):
    color = COLORS[rtype]
    ax2.plot(x2, [h1s, q3s, q4s], 'o-', color=color, linewidth=2.5, markersize=8, label=rtype)
    ax2.text(2.1, q4s, f'{q4s}%', fontsize=9, va='center', color=color, fontweight='bold')

ax2.set_xticks(x2)
ax2.set_xticklabels(['H1 2025', 'Q3 2025', 'Q4 2025'], fontsize=10)
ax2.set_ylabel('Mode Share (%)', fontsize=11)
ax2.set_title('Route-Type Structural Rebalancing', fontsize=13, fontweight='bold')
ax2.legend(fontsize=9, loc='center left')
ax2.set_ylim(5, 45)
ax2.set_xlim(-0.2, 2.5)

fig.suptitle('Elasticity & Substitution Diagnosis', fontsize=15, fontweight='bold', y=1.02)

fig.text(0.5, -0.04,
    "INFERENCE: Congestion elasticity spiked +101% during the shock then decayed -35% as the system stabilized.\n"
    "Express share peaked at 31% (Q3) then settled at 28.3% (Q4). Feeder found its floor at ~18.5%.\n"
    "The new equilibrium: City dominates at 41%, Express elevated at 28%, Feeder structurally contracted.",
    ha='center', fontsize=9, style='italic',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9))

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_05_elasticity_decay.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [5/6] Elasticity decay")

# ============================================================
# CHART S3-06: 2026 Forward Strategy Summary
# ============================================================
fig, ax = plt.subplots(figsize=(14, 8))

# Route-level H1→Q4 change with 2026 recommendation
fwd_routes = ['X28', 'X66', 'X11', 'C03', 'C02', 'C04', 'C01', 'E22', 'E16', 'F25', 'F12', 'F18']
fwd_types =  ['Exp', 'Exp', 'Exp', 'City','City','City','City','Inter','Inter','Feed','Feed','Feed']
h1_q4_ch =   [28.2, 30.2, 27.1, 17.5, 17.5, 16.1, 15.1, 3.6, 2.6, -14.9, -13.1, -20.8]
q4_pax_km =  [265.7, 160.3, 143.3, 264.2, 181.8, 89.1, 182.9, 173.4, 85.2, 154.6, 76.2, 118.9]

# Recommendations
recommendations = [
    'Maintain 11 buses', 'Maintain 8 buses', 'Maintain 7 buses',
    'Maintain 11 buses', 'Add 1 bus', 'Add 2-3 buses', 'Maintain 7 buses',
    'Maintain', 'Maintain',
    'Optimize schedule', 'Restructure', 'Metro-connector'
]

bar_colors = [COLORS.get({'Exp':'Express','City':'City','Feed':'Feeder','Inter':'Intercity'}[t], GRAY) for t in fwd_types]

x = np.arange(len(fwd_routes))
bars = ax.bar(x, h1_q4_ch, color=bar_colors, edgecolor='white', width=0.6, zorder=3)

ax.axhline(y=0, color='#424242', linewidth=1)

# Value labels and recommendations
for i, (bar, val, rec) in enumerate(zip(bars, h1_q4_ch, recommendations)):
    y_pos = val + 1 if val >= 0 else val - 1
    va = 'bottom' if val >= 0 else 'top'
    ax.text(bar.get_x() + bar.get_width()/2, y_pos, f'{val:+.1f}%',
            ha='center', va=va, fontsize=9, fontweight='bold')

    # Recommendation badge at bottom
    rec_color = GREEN if 'Maintain' in rec else (ORANGE if 'Add' in rec or 'Optimize' in rec else RED)
    ax.text(bar.get_x() + bar.get_width()/2, -28, rec,
            ha='center', va='top', fontsize=7, fontweight='bold', color='white', rotation=0,
            bbox=dict(boxstyle='round,pad=0.2', facecolor=rec_color, edgecolor='none', alpha=0.85))

labels = [f'{r}\n({t})' for r, t in zip(fwd_routes, fwd_types)]
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel('H1 → Q4 Demand Change (%)', fontsize=12)
ax.set_title('2026 Forward Strategy: Route-Level Demand Change & Recommendations', fontsize=14, fontweight='bold')
ax.set_ylim(-32, 38)

legend_patches = [Patch(color=COLORS[t], label=t) for t in ['Express', 'City', 'Feeder', 'Intercity']]
ax.legend(handles=legend_patches, loc='upper right', fontsize=10, framealpha=0.9)

add_inference(ax,
    "INFERENCE: Express routes stabilized at +27-30% above baseline — current fleet is adequate.\n"
    "City routes grew +15-18% and need targeted capacity adds (C04 needs 2-3 more buses).\n"
    "Feeder F18 (-21%) should be restructured as a metro-connector. F12/F25: optimize schedules.",
    x=0.5, y=0.15, va='bottom')

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_06_forward_strategy.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [6/6] Forward strategy")

# ============================================================
print(f"\n{'='*50}")
print(f"All 6 Stage 3 charts saved to: {CHART_DIR}")
print(f"{'='*50}")
for c in sorted(CHART_DIR.glob('s3_*.png')):
    print(f"  {c.name}")
