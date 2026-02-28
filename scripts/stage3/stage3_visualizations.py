"""
DECODE X 2026 — Stage 3 Visualizations (Redesigned)
=====================================================
Format: Forecast Performance Audit
  - Stage 1 forecast vs Q3 actual
  - Stage 2 forecast vs Q4 actual
All hardcoded from stage3_output.txt
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib.patches import Patch
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

print("Generating Stage 3 charts (Forecast Audit format)...\n")

# === DATA (from stage3_output.txt) ===
routes = ['C01','C02','C03','C04','E16','E22','F12','F18','F25','X11','X28','X66']
rtypes = ['City','City','City','City','Intercity','Intercity','Feeder','Feeder','Feeder','Express','Express','Express']

# Stage 1 forecast vs Q3 actual (per-route totals for Q3: Jul-Sep)
s1_fcast = [263541, 223710, 263126, 211125, 146338, 174013, 190827, 220832, 203777, 207280, 208600, 188070]
q3_actual= [305634, 259248, 309292, 254360, 155712, 183126, 173889, 171906, 190006, 309414, 306846, 284638]

# Stage 2 forecast vs Q4 actual
s2_fcast = [356607, 296983, 358329, 294420, 181994, 214144, 219201, 218135, 233688, 342668, 336538, 314256]
q4_actual= [348918, 302572, 354094, 281907, 173147, 207552, 189369, 197912, 197522, 305663, 305065, 280427]

# ============================================================
# CHART S3-01: Stage 1 Forecast vs Q3 Actual (Grouped Bar)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

x = np.arange(len(routes))
w = 0.35

bars_f = ax.bar(x - w/2, [v/1000 for v in s1_fcast], w, label='Stage 1 Forecast',
                color='#90CAF9', edgecolor='white', zorder=3)
bars_a = ax.bar(x + w/2, [v/1000 for v in q3_actual], w, label='Q3 Actual',
                color=[COLORS[t] for t in rtypes], edgecolor='white', zorder=3)

# Deviation labels on top
for i in range(len(routes)):
    dev = ((q3_actual[i] / s1_fcast[i]) - 1) * 100
    color = GREEN if dev > 5 else (RED if dev < -5 else GRAY)
    y_top = max(s1_fcast[i], q3_actual[i]) / 1000 + 5
    ax.text(x[i], y_top, f'{dev:+.1f}%', ha='center', va='bottom', fontsize=9,
            fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=color, alpha=0.8))

# Value labels inside bars
for bar, val in zip(bars_f, s1_fcast):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f'{val/1000:.0f}K',
            ha='center', va='center', fontsize=7, color='#333', fontweight='bold')
for bar, val in zip(bars_a, q3_actual):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f'{val/1000:.0f}K',
            ha='center', va='center', fontsize=7, color='white', fontweight='bold')

labels = [f'{r}\n({t[:4]})' for r, t in zip(routes, rtypes)]
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel('Total Passengers (thousands)', fontsize=12)
ax.set_title('A. Forecast Performance Audit — Stage 1 Forecast vs Q3 Actual', fontsize=15, fontweight='bold')
ax.set_ylim(0, 370)

# Summary stats box (top-right)
total_f = sum(s1_fcast)
total_a = sum(q3_actual)
overall_err = ((total_a / total_f) - 1) * 100
mape = np.mean([abs(a - f) / a * 100 for f, a in zip(s1_fcast, q3_actual)])
ax.text(0.98, 0.98, f'Overall Error: {overall_err:+.1f}%\nMAPE: {mape:.1f}%\nBias: Systematic under-estimation',
        transform=ax.transAxes, fontsize=10, va='top', ha='right', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFCDD2', edgecolor=RED, alpha=0.9))

legend_extra = [Patch(color='#90CAF9', label='Stage 1 Forecast')]
legend_extra += [Patch(color=COLORS[t], label=f'{t} (Actual)') for t in ['City','Express','Feeder','Intercity']]
ax.legend(handles=legend_extra, loc='upper left', fontsize=9, framealpha=0.9)

add_inference(ax,
    "INFERENCE: Stage 1 missed the Metro Phase 2 shock entirely. Express routes were under-forecast\n"
    "by +32-34% (X66: +34%, X11: +33%, X28: +32%). Feeder routes were over-forecast by 7-29%.\n"
    "Total error: +16.1% — the structural break was not anticipated in Stage 1 modeling.",
    x=0.5, y=0.03, va='bottom')

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_01_s1_vs_q3.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [1/6] S1 Forecast vs Q3 Actual")

# ============================================================
# CHART S3-02: Stage 2 Forecast vs Q4 Actual (Grouped Bar)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

bars_f = ax.bar(x - w/2, [v/1000 for v in s2_fcast], w, label='Stage 2 Forecast',
                color='#A5D6A7', edgecolor='white', zorder=3)
bars_a = ax.bar(x + w/2, [v/1000 for v in q4_actual], w, label='Q4 Actual',
                color=[COLORS[t] for t in rtypes], edgecolor='white', zorder=3)

for i in range(len(routes)):
    dev = ((q4_actual[i] / s2_fcast[i]) - 1) * 100
    color = GREEN if dev > 5 else (RED if dev < -5 else GRAY)
    y_top = max(s2_fcast[i], q4_actual[i]) / 1000 + 5
    ax.text(x[i], y_top, f'{dev:+.1f}%', ha='center', va='bottom', fontsize=9,
            fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=color, alpha=0.8))

for bar, val in zip(bars_f, s2_fcast):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f'{val/1000:.0f}K',
            ha='center', va='center', fontsize=7, color='#333', fontweight='bold')
for bar, val in zip(bars_a, q4_actual):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f'{val/1000:.0f}K',
            ha='center', va='center', fontsize=7, color='white', fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel('Total Passengers (thousands)', fontsize=12)
ax.set_title('A. Forecast Performance Audit — Stage 2 Forecast vs Q4 Actual', fontsize=15, fontweight='bold')
ax.set_ylim(0, 420)

total_f2 = sum(s2_fcast)
total_a2 = sum(q4_actual)
overall_err2 = ((total_a2 / total_f2) - 1) * 100
mape2 = np.mean([abs(a - f) / a * 100 for f, a in zip(s2_fcast, q4_actual)])
ax.text(0.98, 0.98, f'Overall Error: {overall_err2:+.1f}%\nMAPE: {mape2:.1f}%\nBias: Over-correction (overreacted)',
        transform=ax.transAxes, fontsize=10, va='top', ha='right', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#C8E6C9', edgecolor=GREEN, alpha=0.9))

legend_extra2 = [Patch(color='#A5D6A7', label='Stage 2 Forecast')]
legend_extra2 += [Patch(color=COLORS[t], label=f'{t} (Actual)') for t in ['City','Express','Feeder','Intercity']]
ax.legend(handles=legend_extra2, loc='upper left', fontsize=9, framealpha=0.9)

add_inference(ax,
    "INFERENCE: Stage 2 recalibration halved the error (17.9% to 8.1% MAPE). City routes were near-perfect\n"
    "(1-4%). But Express and Feeder were OVER-corrected: we assumed 75% of the Q3 shock was permanent,\n"
    "but demand partially reverted. Stage 2 over-estimated by +7.1% overall.",
    x=0.5, y=0.03, va='bottom')

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_02_s2_vs_q4.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [2/6] S2 Forecast vs Q4 Actual")

# ============================================================
# CHART S3-03: MAPE Improvement (S1 vs S2 side by side)
# ============================================================
fig, ax = plt.subplots(figsize=(14, 7))

s1_ape = [abs(a-f)/a*100 for f,a in zip(s1_fcast, q3_actual)]
s2_ape = [abs(a-f)/a*100 for f,a in zip(s2_fcast, q4_actual)]

bars1 = ax.bar(x - w/2, s1_ape, w, label='Stage 1 MAPE (vs Q3)', color='#EF9A9A', edgecolor='white', zorder=3)
bars2 = ax.bar(x + w/2, s2_ape, w, label='Stage 2 MAPE (vs Q4)', color='#81C784', edgecolor='white', zorder=3)

for bar, val in zip(bars1, s1_ape):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold', color=RED)
for bar, val in zip(bars2, s2_ape):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=8, fontweight='bold', color=GREEN)

# Improvement arrows between pairs
for i in range(len(routes)):
    impr = s1_ape[i] - s2_ape[i]
    if impr > 0:
        ax.annotate(f'{impr:+.0f}pp', xy=(x[i], max(s1_ape[i], s2_ape[i]) + 3.5),
                    fontsize=7, ha='center', color=GREEN, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='#E8F5E9', edgecolor=GREEN, alpha=0.7))
    else:
        ax.annotate(f'{impr:+.0f}pp', xy=(x[i], max(s1_ape[i], s2_ape[i]) + 3.5),
                    fontsize=7, ha='center', color=RED, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.15', facecolor='#FFEBEE', edgecolor=RED, alpha=0.7))

ax.axhline(y=5, color=GRAY, linewidth=1, linestyle=':', alpha=0.7, label='Acceptable threshold (5%)')
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel('Absolute Percentage Error (%)', fontsize=12)
ax.set_title('A. Forecast Audit — MAPE Comparison: Stage 1 vs Stage 2', fontsize=15, fontweight='bold')
ax.set_ylim(0, 40)
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

ax.text(0.98, 0.98, f'Stage 1 MAPE: {np.mean(s1_ape):.1f}%\nStage 2 MAPE: {np.mean(s2_ape):.1f}%\nImprovement: +{np.mean(s1_ape)-np.mean(s2_ape):.1f}pp',
        transform=ax.transAxes, fontsize=11, va='top', ha='right', fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#E8F5E9', edgecolor=GREEN, alpha=0.9))

add_inference(ax,
    "INFERENCE: Recalibration improved MAPE on 9 of 12 routes. Biggest gains: City routes (C01: -12pp,\n"
    "C03: -14pp) and Express (X11: -21pp). Feeder F25 and F12 worsened — we over-corrected for a shock\n"
    "that partially reverted. Net gain: +6.5pp improvement.",
    x=0.5, y=0.97)

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_03_mape_improvement.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [3/6] MAPE improvement")

# ============================================================
# CHART S3-04: Directional Bias — Over vs Under Forecast
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), sharey=True)

# S1 bias
s1_bias = [((f/a)-1)*100 for f,a in zip(s1_fcast, q3_actual)]
colors_s1 = [RED if b > 5 else (BLUE if b < -5 else GRAY) for b in s1_bias]
ax1.barh(x, s1_bias, color=colors_s1, edgecolor='white', height=0.6)
ax1.axvline(x=0, color='#424242', linewidth=1)
ax1.axvspan(-5, 5, alpha=0.08, color='gray')
for i, val in enumerate(s1_bias):
    ha = 'left' if val >= 0 else 'right'
    offset = 1 if val >= 0 else -1
    ax1.text(val + offset, i, f'{val:+.1f}%', ha=ha, va='center', fontsize=9, fontweight='bold')
ax1.set_yticks(x)
ax1.set_yticklabels([f'{r} ({t[:4]})' for r,t in zip(routes, rtypes)], fontsize=10)
ax1.set_xlabel('Forecast Bias (%)', fontsize=11)
ax1.set_title('Stage 1 Bias\n(vs Q3 Actual)', fontsize=13, fontweight='bold')
ax1.set_xlim(-40, 35)

# S2 bias
s2_bias = [((f/a)-1)*100 for f,a in zip(s2_fcast, q4_actual)]
colors_s2 = [RED if b > 5 else (BLUE if b < -5 else GRAY) for b in s2_bias]
ax2.barh(x, s2_bias, color=colors_s2, edgecolor='white', height=0.6)
ax2.axvline(x=0, color='#424242', linewidth=1)
ax2.axvspan(-5, 5, alpha=0.08, color='gray')
for i, val in enumerate(s2_bias):
    ha = 'left' if val >= 0 else 'right'
    offset = 1 if val >= 0 else -1
    ax2.text(val + offset, i, f'{val:+.1f}%', ha=ha, va='center', fontsize=9, fontweight='bold')
ax2.set_xlabel('Forecast Bias (%)', fontsize=11)
ax2.set_title('Stage 2 Bias\n(vs Q4 Actual)', fontsize=13, fontweight='bold')
ax2.set_xlim(-40, 35)

fig.suptitle('A. Forecast Audit — Directional Bias: Under-forecast (←) vs Over-forecast (→)',
             fontsize=14, fontweight='bold', y=1.02)

legend_patches = [
    Patch(color=RED, label='Over-forecast (>+5%)'),
    Patch(color=BLUE, label='Under-forecast (<-5%)'),
    Patch(facecolor='gray', alpha=0.15, label='Acceptable range (±5%)'),
]
fig.legend(handles=legend_patches, loc='lower center', ncol=3, fontsize=10, framealpha=0.9,
           bbox_to_anchor=(0.5, -0.06))

fig.text(0.5, -0.12,
    "INFERENCE: Stage 1 had 8 under-forecasts (mostly Express/City) — missed the demand surge.\n"
    "Stage 2 flipped to 7 over-forecasts — over-corrected for a shock that partially reverted.\n"
    "Stage 2 bias is SMALLER in magnitude but systematically positive (over-estimation).",
    ha='center', fontsize=9, style='italic',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9))

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_04_directional_bias.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [4/6] Directional bias")

# ============================================================
# CHART S3-05: Demand Trajectory H1 → Q3 → Q4
# ============================================================
fig, ax = plt.subplots(figsize=(13, 7))

types_list = ['City', 'Express', 'Feeder', 'Intercity']
h1_vals = [12008, 7542, 7609, 4013]
q3_vals = [12267, 9792, 5824, 3683]
q4_vals = [13994, 9686, 6357, 4138]

xp = np.arange(len(types_list))
w2 = 0.25

bars_h1 = ax.bar(xp - w2, h1_vals, w2, label='H1 2025 (Baseline)', color='#90CAF9', edgecolor='white')
bars_q3 = ax.bar(xp, q3_vals, w2, label='Q3 2025 (Metro Shock)', color='#EF9A9A', edgecolor='white')
bars_q4 = ax.bar(xp + w2, q4_vals, w2, label='Q4 2025 (Stabilized)', color='#A5D6A7', edgecolor='white')

for i in range(len(types_list)):
    for bars, vals in [(bars_h1, h1_vals), (bars_q3, q3_vals), (bars_q4, q4_vals)]:
        bar = bars[i]
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                f'{vals[i]:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # H1→Q3 and Q3→Q4 change
    h1_q3 = ((q3_vals[i]/h1_vals[i])-1)*100
    q3_q4 = ((q4_vals[i]/q3_vals[i])-1)*100
    h1_q4 = ((q4_vals[i]/h1_vals[i])-1)*100
    color = GREEN if h1_q4 > 0 else RED
    ax.annotate(f'Net: {h1_q4:+.1f}%', xy=(xp[i], max(h1_vals[i], q3_vals[i], q4_vals[i]) + 600),
                fontsize=10, ha='center', fontweight='bold', color=color,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=color, alpha=0.8))

ax.set_xticks(xp)
ax.set_xticklabels(types_list, fontsize=13, fontweight='bold')
ax.set_ylabel('Avg Daily Passengers', fontsize=12)
ax.set_title('B. Demand Trajectory: Baseline → Metro Shock → Stabilized Equilibrium', fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v/1000:.0f}K'))
ax.set_ylim(0, 16500)
ax.legend(fontsize=10, loc='upper right', framealpha=0.9)

add_inference(ax,
    "INFERENCE: Express surged +29.8% in Q3 then held at +28.4% net — demand plateaued (permanent shift).\n"
    "Feeder contracted -23.5% then recovered +9.1% — floor found at -16.5%. City grew +16.5% throughout.\n"
    "Network entered a REDISTRIBUTED EQUILIBRIUM: total demand +9.6%, but routed differently.",
    x=0.5, y=0.97)

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_05_demand_trajectory.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [5/6] Demand trajectory")

# ============================================================
# CHART S3-06: 2026 Forward Strategy + Elasticity
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

# Left: Congestion elasticity evolution
periods = ['H1 2025\n(Baseline)', 'Q3 2025\n(Shock)', 'Q4 2025\n(Stable)']
elasticities = [720, 1447, 940]
period_colors = ['#90CAF9', '#EF9A9A', '#A5D6A7']

bars_e = ax1.bar(periods, elasticities, color=period_colors, edgecolor='white', width=0.5, zorder=3)
for bar, val in zip(bars_e, elasticities):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 25,
             f'+{val:,}', ha='center', va='bottom', fontsize=12, fontweight='bold')

ax1.annotate('', xy=(1, 1447), xytext=(0, 720),
             arrowprops=dict(arrowstyle='->', color=RED, lw=2.5))
ax1.text(0.5, 1100, '+101%', ha='center', fontsize=11, color=RED, fontweight='bold')
ax1.annotate('', xy=(2, 940), xytext=(1, 1447),
             arrowprops=dict(arrowstyle='->', color=GREEN, lw=2.5))
ax1.text(1.5, 1210, '-35%', ha='center', fontsize=11, color=GREEN, fontweight='bold')

ax1.set_ylabel('Pax per Congestion Level', fontsize=11)
ax1.set_title('C. Congestion Elasticity\n(Shock → Decay)', fontsize=13, fontweight='bold')
ax1.set_ylim(0, 1700)

# Right: Route-type share evolution (lines)
shares_types = ['City', 'Express', 'Feeder', 'Intercity']
h1_share = [38.5, 24.2, 24.4, 12.9]
q3_share = [38.9, 31.0, 18.4, 11.7]
q4_share = [40.9, 28.3, 18.6, 12.1]

x_line = np.arange(3)
for i, (rtype, h1s, q3s, q4s) in enumerate(zip(shares_types, h1_share, q3_share, q4_share)):
    color = COLORS[rtype]
    ax2.plot(x_line, [h1s, q3s, q4s], 'o-', color=color, linewidth=2.5, markersize=10, label=rtype, zorder=5)
    # Endpoint labels
    ax2.text(-0.15, h1s, f'{h1s}%', fontsize=8, va='center', ha='right', color=color, fontweight='bold')
    ax2.text(2.15, q4s, f'{q4s}%', fontsize=9, va='center', color=color, fontweight='bold')

ax2.set_xticks(x_line)
ax2.set_xticklabels(['H1 2025', 'Q3 2025\n(Shock)', 'Q4 2025\n(Stable)'], fontsize=10, fontweight='bold')
ax2.set_ylabel('Mode Share (%)', fontsize=11)
ax2.set_title('D. Route-Type Rebalancing\n(Structural Shift)', fontsize=13, fontweight='bold')
ax2.legend(fontsize=9, loc='center right')
ax2.set_ylim(8, 45)
ax2.set_xlim(-0.3, 2.5)

fig.suptitle('C/D. Elasticity & Substitution Diagnosis + Structural Rebalancing',
             fontsize=14, fontweight='bold', y=1.02)

fig.text(0.5, -0.04,
    "INFERENCE: Congestion elasticity spiked +101% during Metro shock, then decayed -35% as network stabilized.\n"
    "Express peaked at 31% share (Q3) then settled at 28.3% (Q4). Feeder found floor at ~18.5%.\n"
    "New equilibrium: City dominates at 41%, Express structurally elevated at 28%, Feeder permanently contracted.",
    ha='center', fontsize=9, style='italic',
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#FFF9C4', edgecolor='#F9A825', alpha=0.9))

plt.tight_layout()
plt.savefig(CHART_DIR / 's3_06_elasticity_rebalancing.png', dpi=150, bbox_inches='tight')
plt.close()
print("  [6/6] Elasticity & rebalancing")

# ============================================================
print(f"\n{'='*50}")
print(f"All 6 Stage 3 charts saved to: {CHART_DIR}")
print(f"{'='*50}")
for c in sorted(CHART_DIR.glob('s3_*.png')):
    print(f"  {c.name}")
