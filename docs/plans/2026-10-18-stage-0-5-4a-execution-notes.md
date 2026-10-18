# AAD-0.5.4-A+ execution notes

- Original workspace: five pre-existing deletions under `doc/literature-notes/`; preserved and excluded from this task.
- Initial test-first run: new module import failed as expected before implementation; five initial behavior tests then passed. Boundary qualification and bounded benchmark-plan tests added subsequently.
- Full diagnostic pilot `stage_0_5_calibration_gaps_v1/` completed without source/join errors. Its unguarded source-boundary density was retained as sensitivity; final diagnostic package is `stage_0_5_calibration_gaps_v1_r2/`. The observed complete-trajectory boundary issue motivated a time-based candidate exclusion, never SUMO scores.
- Initial focused regression: stopped at a stalled child `sumo.exe --version` (PID 22092, parent pytest PID 43032; started 21:29:13 Asia/Shanghai). Separate 10 s bounded SUMO/netconvert version probes succeeded with version 1.26.0. Only these task-owned stalled processes were terminated; no completed SUMO simulation was discarded or retuned. Focused regression rerun requested. This interruption is an engineering startup anomaly, not a failed scientific trial.

All research choices remain Proposal. No validation content, holdout, download, formal calibration, Protocol Lock or Stage I/II.
