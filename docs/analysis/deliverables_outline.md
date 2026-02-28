# DECODE X 2026 — Deliverables Structure & Content Guide

All content below is pre-loaded with actual data from our Stage 1 analysis. After the 7 PM shock, update Sections marked [SHOCK-DEPENDENT].

---

## Deliverable 1: Interim Submission (5 Slides, Due 11 PM after Shock)

### Slide 1 — Situation Assessment
- **Title:** "Mobility Shift: Structural Shock Impact Assessment"
- **Content:**
  - 1-line summary of the shock event
  - Baseline context: 12 routes, 60 stops, 33.5M cumulative pax (2022–H1 2025)
  - Growth trajectory: +9.2% (2022→23), +13.1% (2023→24)
- [SHOCK-DEPENDENT] How the shock changes the baseline assumptions

### Slide 2 — Before vs After the Shock
- **Content:**
  - Left column: Pre-shock forecast (H2 2025 = 5.5M pax, +7.5% growth)
  - Right column: Post-shock revised forecast
  - Delta table showing which routes/zones are most affected
- Use: `forecast_h2_2025.csv` as "before" baseline

### Slide 3 — Revised Corridor Risk Map
- **Content:**
  - Updated overload risk rankings (currently: X28=89, X11=68, X66=60)
  - Which corridors move up/down the risk ladder after the shock
  - Zone pressure changes (currently all zones are GENERATORS)
- Use: `corridor_output.txt` Section B as baseline

### Slide 4 — Adapted Strategy
- **Content:**
  - Revised fleet reallocation (currently: 11 buses redistributed, budget-neutral)
  - Headway modifications adjusted for new constraints
  - Any new route proposals or service changes triggered by the shock
- [SHOCK-DEPENDENT] Modify based on new constraints

### Slide 5 — Decision Framework for Stage 3
- **Content:**
  - Key uncertainties remaining
  - Scenario planning: best case / worst case / most likely
  - What data/decisions needed from the Stage 3 directive (1 AM)
  - Risk mitigation actions being taken now

---

## Deliverable 2: Executive Presentation (15 Slides, Due 9 AM)

### Part A — Context & Diagnosis (Slides 1–5)

| Slide | Title | Key Content | Data Source |
|-------|-------|-------------|-------------|
| 1 | Title Slide | Team name, case title, date | — |
| 2 | Executive Summary | 3 bullet findings, 1 recommendation | All outputs |
| 3 | Network Overview | 12 routes, 7 zones, 4 route types, map | `Bus_Stops.csv` coords |
| 4 | Historical Growth | YoY growth chart (+9.2%, +13.1%), monthly trend | `stage1_output.txt` 6a, 6i |
| 5 | Demand Decomposition | Seasonality (31% winter uplift), weekday/weekend, congestion elasticity | `stage1_output.txt` 6b, 6c, 6f |

### Part B — Analysis & Forecast (Slides 6–9)

| Slide | Title | Key Content | Data Source |
|-------|-------|-------------|-------------|
| 6 | Baseline Forecast | H2 2025: 5.5M pax, monthly breakdown, full year = 11.1M | `forecast_output.txt` |
| 7 | Corridor Risk Assessment | Overload ranking (X28/X11/X66), waste ranking (F18/E16/F12) | `corridor_output.txt` Section B, C |
| 8 | Route Load Profiles | Cumulative boarding charts showing where buses fill up | `corridor_output.txt` Section G |
| 9 | Stop-Level Bottlenecks | Coastal Marina dominance, Top 5 bottleneck stops, pax/dwell-min | `corridor_output.txt` Section D |

### Part C — Shock Response (Slides 10–12) [SHOCK-DEPENDENT]

| Slide | Title | Key Content |
|-------|-------|-------------|
| 10 | Shock Impact Analysis | What changed, magnitude, which routes/zones hit hardest |
| 11 | Revised Forecast | Updated H2 2025 numbers with shock factored in |
| 12 | Stage 3 Directive Response | How the final binding constraint was incorporated |

### Part D — Recommendations (Slides 13–15)

| Slide | Title | Key Content | Data Source |
|-------|-------|-------------|-------------|
| 13 | Fleet Reallocation | Budget-neutral 11-bus redistribution, headway tables | `fleet_output.txt` Section 3 |
| 14 | Operational Playbook | Seasonal rotation (22-25% swing), DOW schedules, Coastal Marina plan | `fleet_output.txt` Sections 4, 5 |
| 15 | Strategic Roadmap | 30/60/90-day implementation timeline, KPIs to track, risk register | Synthesized |

---

## Deliverable 3: Technical Appendix (10 Pages, Due 9 AM)

| Page | Section | Content |
|------|---------|---------|
| 1 | Data Pipeline | 5 CSVs, merge strategy, join keys, integrity checks (zero loss, zero nulls) |
| 2 | Feature Engineering | Total_Pax, Dubai weekend logic, season classification, time features |
| 3 | Forecasting Methodology | Component decomposition: trend slope + seasonal multipliers + DOW effects + congestion elasticity |
| 4 | Forecast Validation | H2 2025 vs H2 2024 comparison (+7.5%), full-year projection, P95 capacity flags |
| 5 | Corridor Risk Model | Overload risk scoring formula (40% Pax/km + 30% Pax/Stop + 30% Growth), waste scoring |
| 6 | Stop-Level Analysis | Bottleneck detection (share ratio), pax/dwell-min, cumulative load profiles |
| 7 | Fleet Optimization | Service profile (81 buses, 60-pax capacity), round-trip calculations, load factors |
| 8 | Reallocation Model | Density-proportional allocation, headway recalculation, impact metrics |
| 9 | [SHOCK] Shock Response Model | Post-shock forecast revision methodology, sensitivity analysis |
| 10 | [SHOCK] Final Optimization | Incorporating Stage 3 directive, revised reallocation under new constraints |

**Key files to reference:**
- `stage1_pipeline.py` — data merge code
- `stage1_forecast.py` — forecasting code
- `stage1_corridor_analysis.py` — corridor analysis code
- `stage1_fleet_reallocation.py` — fleet optimization code
- `master_analytical_dataset.csv` — 195,381 row unified dataset

---

## Deliverable 4: One-Page Decision Memo (Due 9 AM)

### Template:

```
TO:      Dubai RTA Board of Directors
FROM:    [Team Name] — Strategic Advisory
DATE:    [Date]
RE:      MOBILITY SHIFT — Fleet Reallocation & Headway Optimization

SITUATION:
  - Network serving 11.1M projected annual pax across 12 routes
  - Growth accelerating at +7-13% YoY with strong seasonal pattern
  - Express corridors at critical overload (X28: 89/100 risk)
  - [SHOCK IMPACT SUMMARY - 1 line]

RECOMMENDATION:
  1. Immediately redistribute 11 buses from low-density to high-density
     corridors (budget-neutral, +3 to X28, +2 to C03/C02)
  2. Implement time-variable headways: 11-15 min weekday peak,
     19-29 min weekend off-peak
  3. Activate seasonal rotation: +12% fleet in winter, -12% in summer
  4. [SHOCK-SPECIFIC RECOMMENDATION]

EXPECTED IMPACT:
  - X28 headway: 20 min → 12.4 min (38% improvement)
  - C03 headway: 15 min → 11.5 min (23% improvement)
  - Zero additional capital expenditure required
  - [SHOCK-SPECIFIC METRIC]

RISK:
  - Coastal Marina bottleneck requires medium-term infrastructure
  - Reduced service on C04/F12 may affect coverage zones
  - [SHOCK-SPECIFIC RISK]

DECISION REQUIRED:
  Approve fleet reallocation effective [date] with seasonal
  adjustment cycle beginning November 2025.
```

---

## Pre-Shock Checklist (Before 7 PM)

- [x] Master dataset built and validated
- [x] Baseline forecast generated (H2 2025)
- [x] Corridor overload/waste identified
- [x] Fleet reallocation proposed
- [x] Deliverables outlines structured
- [ ] **Await shock at 7 PM** — update Slides 10-12, Appendix Pages 9-10, Decision Memo
- [ ] Submit Interim (5 slides) by 11 PM
- [ ] Await Stage 3 directive at 1 AM
- [ ] Submit Final Package by 9 AM
