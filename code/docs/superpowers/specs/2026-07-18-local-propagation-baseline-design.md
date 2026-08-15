# Local One-hop And Multi-hop Propagation Baseline Design

## Goal

Build a conservative, reproducible local propagation baseline from the 2,057 eligible formal risk episodes before testing any nonlocal effect.

## Inputs And Exclusions

The baseline reads `risk_episodes.csv` and `extraction_manifest.csv` from the validated 270-file event dataset. It excludes `safe_speed_override_candidate` and vehicle entry/exit boundary episodes. Interaction transitions and adjacency to override candidates remain in explicit, mutually exclusive context strata:

- stable following;
- interaction transition only;
- adjacent override only;
- transition and adjacent override.

## Local Edge Definition

Source and target must belong to the same run and satisfy `0 < delay <= 3 s`. A pair receives one relation, in priority order:

1. `same_vehicle`: a later episode on the same vehicle;
2. `leader_to_follower`: the target names the source vehicle as leader;
3. `follower_to_leader`: the source names the target vehicle as leader;
4. `same_region_local`: known identical region and longitudinal separation no greater than 50 m.

Leader/follower distance uses the available headway of the following vehicle. Same-vehicle distance is zero because it is temporal persistence, not spatial separation. Each target retains only the highest-scoring prior source, producing a time-directed acyclic graph with maximum in-degree one.

## Multi-hop Metrics

Graph traversal assigns every node a root and hop depth. Chain outputs include event count, edge count, maximum depth, time span, cumulative link score, mean delay, and maximum path distance. Run and cell summaries report edge exposure rates, cross-vehicle share, multi-hop-chain share, and depth.

## Robustness Checks

Threshold sensitivity uses time windows of 1, 2, 3, and 5 seconds and local distances of 25, 50, and 80 m. A deterministic vehicle-wise circular time-shift null model preserves each vehicle's event pattern while breaking cross-vehicle timing alignment. It compares observed cross-vehicle direct-edge counts with 100 null draws using an empirical one-sided p-value and z-score.

## Visual Outputs

The package includes coverage, relation composition, penetration trends, delay/distance distributions, depth heatmaps, multi-hop shares, context strata, null-model results, sensitivity heatmaps, and representative chains. Every figure records its source table in a catalog.

## Interpretation Boundary

These links are local temporal-topological baseline associations. Scores rank plausible predecessors and are not causal probabilities. A nonlocal candidate can only be studied after conditioning on this baseline and passing the null and sensitivity checks.

## Resources

The implementation is CPU-only and uses pandas, NumPy, NetworkX, and Matplotlib.
