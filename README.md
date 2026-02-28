# DECODE X 2026 — Exception Handlers
## Dubai RTA Bus Network Strategic Advisory

> **Team:** Exception Handlers  
> **Event:** DECODE X 2026 Hackathon  
> **Scope:** 12 bus routes, 56 stops, 195K+ ridership records (2022–2025)

---

## 🎯 Problem Statement

Dubai RTA's bus network faces demand volatility, corridor imbalance, and structural disruption from **Metro Phase 2** (launched Jul 2025). This project provides a data-driven advisory across 3 stages:

| Stage | Challenge | Key Finding |
|-------|-----------|-------------|
| **Stage 1** | Baseline demand diagnostics & H2 2025 forecast | +13.1% accelerating growth, 5.5M H2 forecast |
| **Stage 2** | Metro Phase 2 structural break detection & recalibration | +16.1% shock, Express surged +47-51%, Feeder contracted -22% |
| **Stage 3** | Accountability audit & 2026 forward strategy | MAPE improved 17.9% → 8.1%, demand stabilized at redistributed equilibrium |

---

## 📁 Repository Structure

```
decodex/
├── data/                         # Data files (excluded from repo — provided by organizers)
│   ├── raw/                      # Original datasets (5 CSVs)
│   ├── shock/                    # Stage 2 shock data (2 CSVs)
│   └── generated/                # Processed & forecast outputs (4 CSVs)
│
├── scripts/                      # All analysis code
│   ├── stage1/                   # Stage 1: Pre-shock analysis
│   │   ├── stage1_pipeline.py           # Data merge & diagnostics
│   │   ├── stage1_forecast.py           # H2 2025 demand forecast
│   │   ├── stage1_corridor_analysis.py  # Overload/waste scoring
│   │   ├── stage1_fleet_reallocation.py # Fleet optimization (81 buses)
│   │   ├── stage1_visualizations.py     # 14 charts
│   │   ├── growth_decomposition.py      # Growth breakdown charts
│   │   └── build_submission_doc.py      # Word doc generator
│   ├── stage2/                   # Stage 2: Post-shock analysis
│   │   ├── stage2_shock_analysis.py     # Structural break detection
│   │   ├── stage2_visualizations.py     # 6 shock charts
│   │   └── build_stage2_pptx.py         # 5-slide brief generator
│   ├── stage3/                   # Stage 3: Accountability audit
│   │   ├── stage3_accountability.py     # Forecast audit & 2026 strategy
│   │   └── stage3_visualizations.py     # 6 audit charts
│   └── runners/                  # Wrapper scripts
│
├── charts/                       # All generated visualizations (26 total)
│   ├── stage1/                   # 14 pre-shock charts
│   ├── stage2/                   # 6 structural break charts
│   └── stage3/                   # 6 accountability audit charts
│
├── output/                       # Text analysis reports
│   ├── stage1/                   # Pipeline, forecast, corridor, fleet reports
│   ├── stage2/                   # Shock analysis report
│   └── stage3/                   # Accountability audit report
│
└── README.md
```

---

## 📊 Key Results Summary

### Stage 1: Baseline Analysis
- **Annual demand (2024):** 10.3M passengers (+13.1% YoY)
- **Seasonal pattern:** Winter peak (+18%), Summer moderate, Shoulder transitions
- **Congestion paradox:** Ridership ↑ 20% when congestion ↑, but speed ↓ 50%
- **Fleet proposal:** Budget-neutral reallocation of 11 buses across 12 routes

### Stage 2: Metro Phase 2 Structural Break
- **Overall Q3 deviation:** +16.1% above Stage 1 forecast
- **Express routes:** Surged +47-51% (riders shifted from Feeder to Express)
- **Feeder routes:** Contracted -7 to -22% (riders switched to Metro)
- **Classification:** REGIME CHANGE — not temporary shock
- **Revised Q4 forecast:** 3.37M (+12.3% above original)

### Stage 3: Accountability Audit
- **Recalibration impact:** MAPE improved from 17.9% to 8.1% (+6.5pp)
- **Verdict:** Stage 2 slightly **overreacted** on Express routes (demand moderated)
- **Demand trajectory:** 31,172 → 31,566 → 34,176/day (redistributed equilibrium)
- **Elasticity decay:** Congestion sensitivity doubled then decayed -35%
- **2026 strategy:** Restructure Feeder as metro-connectors, maintain Express, add capacity to City C04

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.x** | Core analysis engine |
| **pandas** | Data manipulation & aggregation |
| **numpy** | Statistical computation |
| **matplotlib / seaborn** | All 26 visualizations |

---

## 🚀 How to Run

```bash
# Stage 1: Full pipeline
python scripts/runners/run_pipeline.py
python scripts/runners/run_forecast.py
python scripts/runners/run_corridor.py
python scripts/runners/run_fleet.py
python scripts/stage1/stage1_visualizations.py

# Stage 2: Shock analysis
python scripts/runners/run_stage2.py
python scripts/stage2/stage2_visualizations.py

# Stage 3: Accountability audit
python scripts/runners/run_stage3.py
python scripts/stage3/stage3_visualizations.py
```

> **Note:** Data files are not included in the repo (provided by hackathon organizers). Place CSVs in the appropriate `data/` subdirectories before running.

---

## 📈 Visualization Gallery

### Stage 1 (14 Charts)
Monthly demand trends, yearly growth, seasonal patterns, route-type comparisons, congestion paradox, zone analysis, weekday/weekend divergence, top stops, overload risk, forecast vs actual, fleet reallocation, day-of-week heatmap, growth decomposition.

### Stage 2 (6 Charts)
Forecast deviation waterfall, demand redistribution pies, timeline with structural break, express vs feeder shift, revised fleet allocation, shift classification scatter.

### Stage 3 (6 Charts)
MAPE comparison, demand trajectory, structural permanence scatter, fleet alignment, elasticity decay, 2026 forward strategy.

---

*Built by Exception Handlers for DECODE X 2026*
