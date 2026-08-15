# Full Risk Event Visualisation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate and verify a traceable visual package from the validated full risk-event dataset.

**Architecture:** Add a focused visual module that consumes the existing extraction tables, plus a thin CLI wrapper. Reuse the same entry point from the extraction script so regenerated data and figures cannot drift apart.

**Tech Stack:** Python 3.10+, pandas, NumPy, Matplotlib, pytest, Pillow.

---

### Task 1: Define The Visual Package Contract

**Files:**
- Create: `tests/test_risk_event_visuals.py`
- Create: `src/riskprop/risk_event_visuals.py`

- [ ] Write a failing test that calls `create_risk_event_visual_package()` with synthetic summary tables and expects a numbered set of PNG files plus `figure_catalog.csv`.
- [ ] Run `python -m pytest tests/test_risk_event_visuals.py -q` and confirm the import fails because the module does not exist.
- [ ] Implement input validation, stable colors, shared save helpers, and the public package function.
- [ ] Re-run the focused test and confirm it passes.

### Task 2: Add Summary And Sensitivity Figures

**Files:**
- Modify: `tests/test_risk_event_visuals.py`
- Modify: `src/riskprop/risk_event_visuals.py`

- [ ] Add failing assertions for coverage, episode composition, penetration trends, method comparison, threshold curves, improvement heatmaps, and manual-review charts.
- [ ] Confirm the focused test fails because the expected files are missing.
- [ ] Implement each plot from the existing CSV schemas, keeping override candidates separate and showing the vehicle-time denominator.
- [ ] Confirm the focused test passes and every generated PNG has non-zero dimensions.

### Task 3: Add Representative Event Context Figures

**Files:**
- Modify: `tests/test_risk_event_visuals.py`
- Modify: `src/riskprop/risk_event_visuals.py`

- [ ] Add a failing test using manual-review rows with previous/current/next speed and acceleration.
- [ ] Confirm failure because no context plot is written.
- [ ] Implement deterministic representative-case selection and adjacent-frame speed/acceleration plots.
- [ ] Confirm context PNGs and catalog rows are produced.

### Task 4: Add The Reproducible CLI

**Files:**
- Create: `scripts/render_risk_event_visuals.py`
- Modify: `scripts/extract_full_risk_events.py`
- Modify: `tests/test_risk_event_visuals.py`

- [ ] Add a failing CLI smoke test for `--help` and a temporary input directory.
- [ ] Implement CSV loading and call the shared package function.
- [ ] Call the same function after full extraction outputs are written.
- [ ] Run the focused tests and confirm the CLI and library paths both pass.

### Task 5: Full Rendering And Verification

**Files:**
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] Run `python -m pytest -q` and record the exact pass count.
- [ ] Run `python -m compileall -q src scripts`.
- [ ] Render the package from `outputs/risk_event_dataset_20260716`.
- [ ] Verify every catalog entry exists, every PNG is readable, and image dimensions are stable.
- [ ] Build and inspect a contact sheet covering all figures.
- [ ] Record the data-backed observations and any limits without changing the paper or weekly report.
