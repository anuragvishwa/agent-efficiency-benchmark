# Lumni Integration

```text
OSS pipeline
    ↓
reports/public_benchmark.json
    ↓
versioned public object or GitHub release
    ↓
Lumni ingestion job/API
    ↓
Lumni dashboard
```

Recommended Lumni routes:

```text
/benchmarks
/benchmarks/models
/benchmarks/agents
/benchmarks/failures
/benchmarks/waste
/benchmarks/tasks
/benchmarks/trajectories/:runId
/benchmarks/methodology
```

Navigation:

```text
Research
  Public Benchmarks
  Methodology
```

Product switch:

```text
Public Benchmarks | Your Agents
```

The OSS project remains independent from Lumni's private backend. Private
ingestion, advanced RCA, clustering, alerts, replay, routing, workflows, and
enterprise controls remain proprietary.
