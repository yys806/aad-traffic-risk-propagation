# Full Risk Event Visualisation Design

## Goal

Turn the validated full event dataset into a reproducible visual package for result checking and later weekly-report or paper use.

## Scope

The existing event taxonomy and the 270-file extraction remain authoritative. The visual package reads the generated CSV files and does not recalculate risk events. It covers:

1. formal data coverage and vehicle-time exposure;
2. episode composition with override candidates clearly separated;
3. event-rate trends across penetration levels with run-level 95% confidence intervals;
4. scenario and method comparisons;
5. TTC and braking threshold sensitivity;
6. DRIFT improvement relative to FS and PI;
7. manual-review outcomes and context flags;
8. representative adjacent-frame event traces.

## Architecture

`risk_event_visuals.py` owns data validation, chart generation, and a machine-readable figure catalog. `render_risk_event_visuals.py` is a thin command-line entry point that loads the existing CSV outputs. The full extraction script calls the same public function so future dataset rebuilds also refresh the figures.

The figures are static PNG files rendered with Matplotlib. Static output is preferred because it can be checked pixel-by-pixel, embedded in LaTeX, and regenerated without a browser or GPU.

## Visual Rules

- Use a restrained multi-hue palette with stable colors for DRIFT, FS, PI, ordinary events, and override candidates.
- Use Chinese labels where the local font supports them; retain metric identifiers such as TTC, THW, and DRIFT.
- Every rate axis states the denominator: episodes or frames per 1000 vehicle-seconds.
- Override candidates never share the ordinary-braking series.
- Confidence intervals are shown only when the source table contains run-level uncertainty.
- Empty strata produce an informative empty panel instead of an exception.

## Outputs

The output directory `outputs/risk_event_dataset_20260716/figures` contains numbered PNG files and `figure_catalog.csv`. The catalog records filename, title, category, and source table for traceability.

## Testing And Verification

Unit tests use small synthetic frames to verify the expected figure set, non-empty PNG files, catalog contents, and missing-column errors. Final verification runs the full test suite, Python compilation, the renderer against the 270-file result tables, image-dimension checks, and visual inspection of a contact sheet.

## Boundaries

This work does not build the local propagation graph, claim causal effects, or fill absent IDM/Flow-AIL/Flow-RL frame-level data. It is CPU-only.
