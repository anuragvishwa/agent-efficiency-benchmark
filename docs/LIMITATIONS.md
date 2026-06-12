# Limitations

- Historical public runs are confounded by task mix, agent scaffold, model
  endpoint, time, and evaluation context.
- Cost accounting is incomplete, and zero observed cost does not prove free
  execution.
- Trajectory-only analysis cannot explain runs without usable steps.
- RCA categories are heuristic and rule-based.
- Waste estimates are suspected waste, not confirmed waste.
- Estimated wasted cost and duration are proportional estimates.
- Early-stop savings are counterfactual historical estimates.
- Recent models may be missing when no public trajectory is available.
- Terminal-Bench and SWE-agent are separate benchmark families and should not be
  interpreted as one universal ranking.
- SWE-agent trajectories do not currently include observed cost or duration in
  the source data, so cost/duration FinOps claims are unavailable for that
  dataset.
