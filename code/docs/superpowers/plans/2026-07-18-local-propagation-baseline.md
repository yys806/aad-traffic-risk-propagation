# Local One-hop And Multi-hop Propagation Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a validated local propagation graph, multi-hop chain metrics, null-model comparison, sensitivity analysis, and visual package from the formal risk episodes.

**Architecture:** A focused baseline module owns eligibility, edge construction, graph traversal, summaries, permutations, and sensitivity. A separate visual module reads only generated tables, while a thin CLI orchestrates the full package.

**Tech Stack:** Python 3.10+, pandas, NumPy, NetworkX, Matplotlib, pytest, Pillow.

---

### Task 1: Eligibility And Local Edges
- [ ] Write failing tests for exclusions, context strata, local relation priority, positive delay, and single strongest parent.
- [ ] Confirm the tests fail because the module does not exist.
- [ ] Implement eligibility, candidate edge construction, scoring, and direct selection.
- [ ] Confirm focused tests pass.

### Task 2: Multi-hop Traversal And Summaries
- [ ] Write failing tests for root assignment, hop depth, chain metrics, run summaries, and exposure-normalised rates.
- [ ] Confirm the tests fail on missing traversal functions.
- [ ] Implement node, chain, run, and cell summaries.
- [ ] Confirm focused tests pass.

### Task 3: Null Model And Sensitivity
- [ ] Write failing deterministic tests for vehicle-wise circular shifts, empirical p-values, and time/distance grids.
- [ ] Implement 100-draw null comparison and 12-setting sensitivity tables.
- [ ] Confirm repeated calls with the same seed are identical.

### Task 4: Visual Package And CLI
- [ ] Write failing tests for ten nonblank figures, a figure catalog, and CLI help.
- [ ] Implement the visual package and `scripts/build_local_propagation_baseline.py`.
- [ ] Confirm library and CLI tests pass.

### Task 5: Formal Run And Verification
- [ ] Run the baseline against the validated 270-file event dataset.
- [ ] Run the full test suite and Python compilation.
- [ ] Verify table schemas, counts, graph invariants, deterministic output hashes, and image pixels.
- [ ] Visually inspect every figure and record the conclusions and limitations.
