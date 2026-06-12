# Methodology

This benchmark analyzes historical public Terminal-Bench trajectories. It is a
trajectory-backed research layer, not a universal model ranking.

## Scope

The v0.1 pipeline supports Terminal-Bench and SWE-agent trajectories as separate
benchmark families. It keeps agent scaffold, raw model identifier, canonical
model identifier, task count, run count, trajectory coverage, cost coverage,
dataset revision, snapshot cutoff, and methodology version with public
comparisons.

Terminal-Bench and SWE-agent are not merged into one universal leaderboard.
SWE-agent cost and duration are marked unavailable unless source data provides
them.

## Signals

Step-level signals classify errors, tests, edits, reads, searches, shell
actions, submissions, adjacent repeats, same-result repeats, repeated failed
attempts, and suspected waste.

The primary suspected-waste rule is conservative:

```text
same normalized action
+ immediately previous tool event in same run
+ same normalized observation
+ not an edit action
= suspected_waste
```

These are rule-based estimates, not ground truth.

## Cost and Savings

Cost metrics are eligible only when a system has enough runs and sufficient
positive-cost coverage. Zero observed cost is not treated as proof of free
execution. Estimated wasted cost and duration are proportional historical
estimates using observed trajectory waste rates.

## RCA

RCA categories are assigned by transparent rules in priority order. Confidence
is heuristic and not a calibrated probability.

## Agent System Thesis

The benchmark is designed to show that model choice alone is insufficient.
Harness design, tool interfaces, context handling, verification behavior, and
recovery loops can materially change success and efficiency.

## Early Stopping

Early-stop simulations are counterfactual historical estimates. A false stop is
recorded when a policy would have stopped a historically successful run.
