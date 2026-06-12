# AFWB Lite: Low-Cost Agent Failure, Waste, and Memory Benchmark

**Version:** 0.1  
**Status:** Implementation specification  
**Maintainer:** Lumniverse  
**Primary goal:** Publish a credible, reproducible benchmark for AI-agent root-cause analysis, waste attribution, and runtime memory retrieval with minimal API cost.

---

## 1. Executive Summary

AFWB Lite is a reduced, practical first release of the broader Agent Failure & Waste Benchmark.

The benchmark tests two related questions:

### Track A — RCA and Waste

Can a system correctly determine:

1. Whether an AI-agent run failed
2. What the primary root cause was
3. Where the failure first became observable
4. Which work and cost were avoidable
5. Which predefined remediation is most appropriate
6. Whether the remediation fixes the scenario on replay

### Track B — Runtime Memory

Can an external memory system help an agent:

1. Retrieve relevant prior state
2. Avoid repeating failed attempts
3. Avoid rereading unchanged files or outputs
4. Suppress stale or superseded information
5. Solve tasks using less context and fewer tokens
6. Retrieve exact evidence only when needed

The first release intentionally prioritizes:

- Deterministic scenarios
- Strong ground truth
- Small scale
- Local execution
- Reproducibility
- Low or zero hosted-model cost
- Clear research findings

It does **not** attempt to implement the full long-term benchmark roadmap in the first release.

---

## 2. Core Research Questions

### RCA questions

- Can a system distinguish the root cause from downstream symptoms?
- Can it identify the earliest causal span rather than the last visible error?
- Can it quantify avoidable calls, tokens, latency, and cost?
- Can it recommend the smallest valid remediation?
- Does the recommended remediation work when replayed?

### Memory questions

- Is graph-guided retrieval more effective than rolling context or vector-only memory?
- Does hybrid retrieval reduce repeated actions and context usage?
- Can temporal filtering prevent stale-memory retrieval?
- Can compact metadata identify the correct evidence before loading full files?
- Does selective file retrieval outperform placing complete logs in context?

---

## 3. Scope of Version 0.1

### Included

- 24 deterministic or semi-deterministic RCA scenarios
- 10 memory-focused scenarios
- One custom Python agent runner
- Framework-neutral normalized trace format
- Mock model
- Mock tools
- Rules baseline
- Last-error heuristic baseline
- Graph/dependency baseline
- Optional low-cost LLM judge
- Predefined remediation replay
- Local BM25 search
- Local vector retrieval
- Graph-guided file retrieval
- Temporal validity filtering
- HTML and Markdown reports
- JSONL and Parquet outputs

### Deferred

- 120+ scenarios
- Three or more framework adapters
- Private leaderboard infrastructure
- Open-ended code patch generation
- Long-running autonomous agents
- Proprietary customer traces
- Full multi-tenant production infrastructure
- Large-scale human annotation
- Hosted graph databases
- Expensive multi-model benchmark sweeps
- Composite score as the primary result

---

## 4. Benchmark Tracks

# Track A: AFWB-RCA

Track A evaluates diagnosis after a run has completed.

```text
Execution trace
      ↓
Failure detection
      ↓
Root-cause classification
      ↓
Causal-span localization
      ↓
Waste estimation
      ↓
Remediation selection
      ↓
Replay verification
```

## Track A tasks

### Task A1 — Failure Detection

```json
{
  "failed": true,
  "confidence": 0.98
}
```

### Task A2 — Root-Cause Classification

```json
{
  "root_cause_category": "TOOL_ARGUMENT_ERROR",
  "confidence": 0.93
}
```

### Task A3 — Failure Localization

```json
{
  "root_cause_span_id": "span_007",
  "first_observable_failure_span_id": "span_006"
}
```

### Task A4 — Waste Estimation

```json
{
  "avoidable_input_tokens": 8400,
  "avoidable_output_tokens": 1100,
  "avoidable_tool_calls": 3,
  "avoidable_latency_ms": 9200,
  "avoidable_cost_usd": 0.18
}
```

### Task A5 — Remediation Selection

Version 0.1 uses controlled remediation identifiers rather than arbitrary patches.

```json
{
  "remediation_type": "ARGUMENT_SCHEMA_VALIDATION",
  "remediation_id": "validate_iso_date_before_booking_v1",
  "target_component": "booking_adapter"
}
```

### Task A6 — Replay Verification

```json
{
  "replay_passed": true,
  "failure_removed": true,
  "new_failure_introduced": false,
  "cost_delta_usd": -0.15,
  "latency_delta_ms": -7400
}
```

---

# Track B: AFWB-Memory

Track B evaluates memory architecture during agent execution.

```text
Agent action or observation
          ↓
External memory update
          ↓
Keyword/vector/graph retrieval
          ↓
Temporal and version filtering
          ↓
Relevant evidence selected
          ↓
Exact file fragment fetched
          ↓
Compact context returned
          ↓
Agent chooses next action
```

## Memory variants

Run each memory scenario under the following conditions.

| Variant | Description |
|---|---|
| `rolling_context` | Only recent messages and tool calls |
| `full_log` | Complete execution history placed in context |
| `vector_only` | Embedding retrieval over memory chunks |
| `bm25_vector` | Keyword and semantic retrieval |
| `graph_files` | Graph metadata selects relevant files or fragments |
| `temporal_hybrid` | Graph + BM25 + vectors + temporal validity + selective file retrieval |

The agent, task, tools, prompt, token budget, maximum steps, and seed must remain unchanged.

Only the memory architecture may change.

---

## 5. Primary Hypotheses

### RCA hypotheses

- **H1:** Last-error heuristics will identify symptoms more often than true causes.
- **H2:** Rules will perform strongly on mechanical failures.
- **H3:** Graph/dependency reasoning will improve localization on distributed failures.
- **H4:** Hybrid diagnosis will outperform rules-only and LLM-only systems.
- **H5:** Replay verification will expose vague or ineffective remediation recommendations.

### Memory hypotheses

- **M1:** Full-log context will use more tokens than indexed retrieval.
- **M2:** Vector-only retrieval will retrieve semantically similar but stale or unrelated memories.
- **M3:** Graph-guided retrieval will improve causal evidence retrieval.
- **M4:** Temporal filtering will reduce stale-memory retrieval.
- **M5:** Selective file retrieval will reduce context size without reducing task success.
- **M6:** Better memory will reduce repeated reads, calls, and failed attempts.

All hypotheses must remain labeled as hypotheses until supported by benchmark results.

---

## 6. Scenario Count

Version 0.1 contains **24 RCA scenarios**.

| Family | Count |
|---|---:|
| Tool use and control flow | 4 |
| State and memory | 4 |
| Retrieval | 4 |
| Cost and waste | 4 |
| Multi-agent and infrastructure | 4 |
| Multi-cause and distributed failures | 4 |
| **Total** | **24** |

Ten of the 24 scenarios are also used in Track B.

---

## 7. Scenario Design Principle

Every core scenario should use a reference–mutation–repair structure.

```text
Successful reference run
          ↓
Apply one controlled mutation
          ↓
Failed or wasteful run
          ↓
Apply predefined remediation
          ↓
Successful replay
```

This structure produces strong counterfactual ground truth.

### Waste calculation

```text
Avoidable waste =
mutated run resource use
-
minimum necessary successful reference resource use
```

Do not label every failed token as waste.

Necessary exploration is not automatically avoidable.

---

## 8. Initial 24 Scenarios

## 8.1 Tool Use and Control Flow

### 1. Invalid booking date

- Root cause: `TOOL_ARGUMENT_ERROR`
- Mutation: Invalid ISO date generated
- Symptom: Repeated booking rejection
- Remediation: `ARGUMENT_SCHEMA_VALIDATION`
- Memory test: Failed date normalization should be recalled

### 2. Duplicate payment

- Root cause: `SIDE_EFFECT_DUPLICATION`
- Mutation: Payment call repeated after ambiguous response
- Symptom: Two successful charges
- Remediation: `IDEMPOTENCY_KEY`
- Memory test: Previous successful side effect should prevent repetition

### 3. Infinite retry on terminal error

- Root cause: `TOOL_RETRY_STORM`
- Mutation: HTTP 400 treated as transient
- Symptom: Repeated identical calls
- Remediation: `RETRY_POLICY_CHANGE`
- Memory test: Terminal failure should be stored as non-retryable

### 4. Missing loop exit condition

- Root cause: `LOOP_NON_TERMINATION`
- Mutation: Success flag ignored
- Symptom: Planner-executor loop continues
- Remediation: `TERMINATION_CONDITION`

---

## 8.2 State and Memory

### 5. State overwritten after handoff

- Root cause: `HANDOFF_CONTEXT_LOSS`
- Mutation: Completed-state field removed
- Symptom: Next agent repeats completed work
- Remediation: `HANDOFF_CONTRACT`

### 6. Stale customer address

- Root cause: `STALE_STATE_USE`
- Mutation: Old address version selected
- Symptom: Shipment created with previous address
- Remediation: `STATE_VERSIONING`
- Memory test: Temporal retrieval must prefer current state

### 7. Context-window eviction

- Root cause: `CONTEXT_WINDOW_EVICTION`
- Mutation: Important constraint appears early, then leaves rolling context
- Symptom: Agent violates the constraint
- Remediation: `STATE_CHECKPOINTING`
- Memory test: External memory should recover the constraint

### 8. False recall from another run

- Root cause: `MEMORY_FALSE_RECALL`
- Mutation: Similar failure from another task is available
- Symptom: Wrong fix selected
- Remediation: `RETRIEVAL_FILTER`
- Memory test: Graph/task isolation should suppress unrelated memory

---

## 8.3 Retrieval

### 9. Tenant filter omitted

- Root cause: `MISSING_FILTER`
- Mutation: Tenant condition removed
- Symptom: Wrong customer document retrieved
- Remediation: `RETRIEVAL_FILTER`

### 10. Correct document below distractor

- Root cause: `RERANKING_ERROR`
- Mutation: Distractor ranks above evidence
- Symptom: Unsupported answer
- Remediation: `RERANKING_CHANGE`

### 11. Stale policy document

- Root cause: `STALE_DOCUMENT`
- Mutation: Older policy version has higher semantic similarity
- Symptom: Outdated answer
- Remediation: `STATE_VERSIONING`
- Memory test: Temporal filtering must prefer current policy

### 12. Excessive retrieval

- Root cause: `EXCESSIVE_RETRIEVAL`
- Mutation: Top 25 chunks returned where 3 are sufficient
- Symptom: Correct answer with high token cost
- Remediation: `CONTEXT_TRIMMING`

---

## 8.4 Cost and Waste

### 13. Expensive model for extraction

- Root cause: `OVERSIZED_MODEL_USE`
- Mutation: Frontier model used for deterministic parsing
- Symptom: Correct but unnecessarily costly run
- Remediation: `MODEL_DOWNGRADE`

### 14. Parallel tools executed serially

- Root cause: `SERIAL_EXECUTION_WASTE`
- Mutation: Independent calls are awaited sequentially
- Symptom: High latency
- Remediation: `PARALLELIZATION`

### 15. Duplicate retrieval

- Root cause: `DUPLICATE_RETRIEVAL`
- Mutation: Same query issued repeatedly
- Symptom: Repeated documents and token waste
- Remediation: `CACHE_ADDITION`
- Memory test: Prior retrieval result should be reused

### 16. Workflow candidate

- Root cause: `UNNECESSARY_AGENTIC_STEP`
- Mutation: LLM used for fixed branching logic
- Symptom: Higher cost and variable output
- Remediation: `WORKFLOW_CONVERSION`

---

## 8.5 Multi-Agent and Infrastructure

### 17. Wrong handoff target

- Root cause: `HANDOFF_TO_WRONG_AGENT`
- Mutation: Billing task sent to research agent
- Symptom: Invalid or incomplete response
- Remediation: `HANDOFF_CONTRACT`

### 18. Conflicting agent outputs

- Root cause: `AGGREGATION_ERROR`
- Mutation: Two valid but incompatible outputs combined incorrectly
- Symptom: Invalid final result
- Remediation: `OUTPUT_VALIDATION`

### 19. Unhandled rate limit

- Root cause: `RATE_LIMIT_UNHANDLED`
- Mutation: 429 treated as terminal
- Symptom: Premature failure
- Remediation: `RETRY_POLICY_CHANGE`

### 20. Dependency version mismatch

- Root cause: `DEPENDENCY_VERSION_ERROR`
- Mutation: Tool schema changed between versions
- Symptom: Serialization or argument failure
- Remediation: `DEPENDENCY_PINNING`

---

## 8.6 Multi-Cause and Distributed Failures

### 21. Early state corruption, late tool failure

- Root cause: `STATE_CORRUPTION`
- Symptom: Tool rejects malformed payload much later
- Remediation: `STATE_SCHEMA_VALIDATION`

### 22. Retrieval miss followed by hallucination

- Root cause: `RETRIEVAL_MISS`
- Secondary symptom: `HALLUCINATED_FACT`
- Remediation: `CONFIDENCE_GATE`

### 23. Wrong model causes malformed handoff

- Root cause: `MODEL_CAPABILITY_MISMATCH`
- Secondary symptom: `HANDOFF_CONTEXT_LOSS`
- Remediation: `MODEL_UPGRADE`

### 24. Timeout workaround hides parser bug

- Root cause: `TOOL_RESULT_MISINTERPRETATION`
- Secondary symptom: Repeated timeout increases
- Remediation: `OUTPUT_VALIDATION`
- Memory test: Disproved timeout hypothesis must not be reused

---

## 9. Ten Memory Scenarios

Use these scenarios for Track B:

```text
1. Invalid booking date
2. Duplicate payment
3. Infinite retry on terminal error
5. State overwritten after handoff
6. Stale customer address
7. Context-window eviction
8. False recall from another run
11. Stale policy document
15. Duplicate retrieval
24. Timeout workaround hides parser bug
```

These scenarios cover:

- Failed attempts
- Side effects
- Current versus stale state
- Task isolation
- Context loss
- Duplicate work
- Disproved hypotheses
- Selective evidence retrieval

---

## 10. Failure Taxonomy for Version 0.1

Use only categories required by the 24 scenarios.

### Control and tools

```text
TOOL_ARGUMENT_ERROR
SIDE_EFFECT_DUPLICATION
TOOL_RETRY_STORM
LOOP_NON_TERMINATION
TOOL_RESULT_MISINTERPRETATION
```

### State and memory

```text
HANDOFF_CONTEXT_LOSS
STALE_STATE_USE
CONTEXT_WINDOW_EVICTION
MEMORY_FALSE_RECALL
STATE_CORRUPTION
```

### Retrieval

```text
MISSING_FILTER
RERANKING_ERROR
STALE_DOCUMENT
EXCESSIVE_RETRIEVAL
RETRIEVAL_MISS
```

### Cost and execution

```text
OVERSIZED_MODEL_USE
SERIAL_EXECUTION_WASTE
DUPLICATE_RETRIEVAL
UNNECESSARY_AGENTIC_STEP
```

### Coordination and infrastructure

```text
HANDOFF_TO_WRONG_AGENT
AGGREGATION_ERROR
RATE_LIMIT_UNHANDLED
DEPENDENCY_VERSION_ERROR
MODEL_CAPABILITY_MISMATCH
```

Expand the taxonomy only after the initial benchmark is stable.

---

## 11. Remediation Taxonomy for Version 0.1

```text
ARGUMENT_SCHEMA_VALIDATION
IDEMPOTENCY_KEY
RETRY_POLICY_CHANGE
TERMINATION_CONDITION
HANDOFF_CONTRACT
STATE_VERSIONING
STATE_CHECKPOINTING
RETRIEVAL_FILTER
RERANKING_CHANGE
CONTEXT_TRIMMING
MODEL_DOWNGRADE
MODEL_UPGRADE
PARALLELIZATION
CACHE_ADDITION
WORKFLOW_CONVERSION
OUTPUT_VALIDATION
DEPENDENCY_PINNING
STATE_SCHEMA_VALIDATION
CONFIDENCE_GATE
```

Each scenario maps to one predefined remediation implementation.

---

## 12. Repository Structure

```text
afwb-lite/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── uv.lock
├── Makefile
├── docker-compose.yml
│
├── configs/
│   ├── benchmark.yaml
│   ├── memory_variants.yaml
│   ├── budgets.yaml
│   ├── pricing.yaml
│   └── models.example.yaml
│
├── data/
│   ├── scenarios/
│   ├── fixtures/
│   ├── reference_runs/
│   ├── mutated_runs/
│   ├── gold/
│   ├── memory/
│   └── releases/
│
├── src/
│   └── afwb/
│       ├── cli.py
│       ├── config.py
│       ├── schemas/
│       ├── runner/
│       ├── tools/
│       ├── trace/
│       ├── scenarios/
│       ├── scoring/
│       ├── replay/
│       ├── baselines/
│       ├── memory/
│       │   ├── interface.py
│       │   ├── rolling_context.py
│       │   ├── full_log.py
│       │   ├── vector_only.py
│       │   ├── bm25_vector.py
│       │   ├── graph_files.py
│       │   ├── temporal_hybrid.py
│       │   ├── indexing.py
│       │   ├── retrieval.py
│       │   └── evidence.py
│       ├── analysis/
│       └── reporting/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── golden/
│   ├── reproducibility/
│   └── memory/
│
├── scripts/
│   ├── generate_scenarios.py
│   ├── generate_reference_runs.py
│   ├── generate_mutated_runs.py
│   ├── build_memory_indexes.py
│   ├── run_rca_benchmark.py
│   ├── run_memory_benchmark.py
│   ├── score_results.py
│   └── build_report.py
│
├── results/
│   ├── raw/
│   ├── scored/
│   ├── reports/
│   └── figures/
│
└── docs/
    ├── methodology.md
    ├── scenario-guide.md
    ├── memory-architecture.md
    ├── scoring.md
    ├── reproducibility.md
    ├── limitations.md
    └── claims-policy.md
```

---

## 13. Normalized Trace Schema

```json
{
  "run_id": "run_001",
  "scenario_id": "invalid_booking_date",
  "variant": "mutated",
  "framework": "custom",
  "model": "mock",
  "seed": 42,
  "status": "failed",
  "started_at": "2026-06-12T10:00:00Z",
  "ended_at": "2026-06-12T10:00:05Z",
  "total_input_tokens": 1800,
  "total_output_tokens": 320,
  "total_cost_usd": 0,
  "total_latency_ms": 5000,
  "spans": []
}
```

## Span schema

```json
{
  "span_id": "span_006",
  "parent_span_id": "span_004",
  "type": "validation",
  "name": "normalize_date",
  "status": "error",
  "input": {
    "date_text": "next Friday"
  },
  "output": {
    "normalized_date": "2026-14-44"
  },
  "started_at": "2026-06-12T10:00:02.000Z",
  "ended_at": "2026-06-12T10:00:02.020Z",
  "latency_ms": 20,
  "metadata": {
    "file": "booking/date_normalizer.py",
    "version": "abc123"
  }
}
```

---

## 14. Memory Data Model

Use compact metadata plus external evidence files.

## Memory node

```json
{
  "node_id": "memory_104",
  "node_type": "failed_attempt",
  "task_id": "task_001",
  "run_id": "run_001",
  "summary": "Increasing timeout did not resolve the parser failure.",
  "status": "disproved",
  "confidence": 0.98,
  "valid_from_step": 7,
  "valid_until_step": null,
  "file_version": "abc123",
  "evidence_uri": "data/memory/run_001/terminal.log",
  "start_offset": 1820,
  "end_offset": 2490,
  "content_hash": "sha256:..."
}
```

## Memory edge

```json
{
  "source_id": "attempt_07",
  "edge_type": "DISPROVED",
  "target_id": "hypothesis_timeout",
  "confidence": 0.98,
  "evidence_node_id": "memory_104"
}
```

## Recommended node types

```text
Task
Run
Step
File
FileVersion
ToolCall
Failure
Hypothesis
Attempt
Result
Fix
Test
Constraint
Decision
Learning
EvidenceChunk
```

## Recommended relationships

```text
CONTAINS
READ
MODIFIED
PRODUCED
TESTED
CONFIRMED
DISPROVED
CAUSED
RESOLVED
VERIFIED_BY
SUPERSEDES
EVIDENCE_FOR
SIMILAR_TO
BELONGS_TO_TASK
```

---

## 15. Storage Architecture

Version 0.1 should remain local and simple.

```text
Raw traces and large outputs
            ↓
Local files
            ↓
Compact metadata
            ↓
SQLite or Postgres
            ↓
BM25 / full-text index
            ↓
Local vector index
            ↓
NetworkX or relational graph
            ↓
Selective evidence retrieval
```

### Files store

- Full traces
- Terminal output
- Model responses
- Test reports
- Source snapshots
- Large retrieved documents

### Database stores

- Node metadata
- Edges
- Task identifiers
- File versions
- Content hashes
- Evidence references
- Temporal validity
- Retrieval status
- Index version

### Indexes

- SQLite FTS5 or Tantivy for keyword search
- FAISS or hnswlib for vector retrieval
- NetworkX for graph traversal
- Optional Postgres + pgvector later

No hosted database is required.

---

## 16. Retrieval Pipeline

```text
Agent query
    ↓
Task and tenant filter
    ↓
BM25 candidate retrieval
    ↓
Vector candidate retrieval
    ↓
Graph expansion
    ↓
Temporal/version filtering
    ↓
Confidence and recency reranking
    ↓
Select evidence references
    ↓
Read exact file fragments
    ↓
Build compact context package
```

## Example context package

```json
{
  "current_failure": "PaymentSchemaError",
  "active_hypotheses": [
    "Nullable field normalization is incorrect"
  ],
  "disproved_hypotheses": [
    "Network timeout"
  ],
  "relevant_files": [
    "payment/parser.py"
  ],
  "verified_previous_fix": {
    "summary": "Normalize null fields before persistence",
    "evidence_uri": "data/memory/run_014/fix.md"
  },
  "retrieved_evidence_tokens": 420
}
```

---

## 17. Evidence Budgets

Every memory variant must respect the same limits.

```yaml
max_context_tokens: 8000
max_retrieved_chunks: 10
max_graph_hops: 3
max_full_files: 2
max_file_fragment_tokens: 3000
max_retrieval_rounds: 3
max_agent_steps: 20
```

Evaluate at multiple context budgets:

```text
2,000 tokens
4,000 tokens
8,000 tokens
Complete trace
```

This tests whether retrieval quality remains strong under constrained context.

---

## 18. Baselines

## Baseline 1 — Last Visible Error

Returns:

- The last failed span
- The category inferred directly from that span

Purpose:

- Demonstrate symptom-versus-cause confusion

## Baseline 2 — Rules

Checks:

- Explicit errors
- Duplicate calls
- Retry storms
- Missing termination
- Invalid schemas
- Repeated retrieval
- Model cost thresholds
- Serial execution
- State deletion
- Stale version use

## Baseline 3 — Dependency Graph

Uses:

- Parent-child span structure
- State propagation
- Error propagation
- Tool dependencies
- Earliest causal ancestor

## Baseline 4 — Hybrid Open Baseline

Combines:

- Rules
- Dependency graph
- Waste calculator
- Predefined remediation mapping
- Optional local or hosted LLM explanation

## Optional Baseline 5 — LLM Judge

Use:

- One inexpensive model
- Fixed prompt
- Fixed schema
- Maximum 6,000 trace tokens
- Maximum 500 output tokens
- Cached responses
- Three seeds only for final stochastic evaluation

---

## 19. RCA Metrics

### Failure detection

```text
Accuracy
Precision
Recall
F1
```

### Root-cause classification

```text
Macro F1
Micro F1
Top-1 accuracy
Per-category precision
Per-category recall
```

### Localization

```text
Exact span accuracy
Within-1-span accuracy
Within-3-span accuracy
Mean graph distance
First-observable-span accuracy
```

### Waste estimation

Use:

```text
Mean absolute error
Median absolute error
Normalized absolute error
Signed bias
Waste-band classification F1
```

Do not use ordinary MAPE when gold waste can equal zero.

### Remediation

```text
Remediation type accuracy
Remediation ID accuracy
Replay success rate
New failure rate
Cost delta
Latency delta
```

---

## 20. Memory Metrics

### Retrieval quality

```text
Evidence Recall@K
Evidence Precision@K
Mean Reciprocal Rank
Relevant evidence per 1,000 context tokens
Irrelevant memory rate
Stale memory retrieval rate
False-memory rate
```

### Agent behaviour

```text
Task success rate
Steps to resolution
Repeated tool-call rate
Repeated file-read rate
Repeated failed-attempt rate
Disproved-hypothesis reuse rate
Duplicate retrieval rate
```

### Efficiency

```text
Total input tokens
Total output tokens
Context tokens inserted
Bytes of evidence fetched
Full files fetched
File fragments fetched
Retrieval latency
Total execution latency
Total model cost
```

### Memory correctness

```text
Current version retrieval accuracy
Task-isolation accuracy
Superseded fact suppression rate
Verified-fix retrieval accuracy
Evidence citation accuracy
```

---

## 21. Statistical Methodology

### Deterministic scenarios

- One execution per configuration
- Fixed seed
- Fixed timing
- Fixed mock-model outputs
- Exact reproducibility required

### Stochastic scenarios

- Three seeds only where stochasticity exists
- Report mean and standard deviation
- Use bootstrap confidence intervals for aggregate metrics

### Comparisons

Report:

- Overall results
- Per-family results
- Per-difficulty results
- Per-memory-variant results
- Results at each context budget

Do not make significance claims from point estimates alone.

---

## 22. Cost-Control Strategy

The benchmark must be runnable with zero hosted-model spend.

## Free path

```text
Mock model
Mock tools
Local scenarios
Local embeddings
SQLite FTS5
FAISS or hnswlib
NetworkX
Local report generation
Predefined remediations
Deterministic replay
```

## Optional hosted-model path

Recommended cap:

```text
24 scenarios
× 6,000 input tokens
× 500 output tokens
= approximately 156,000 tokens for one pass
```

Three seeds:

```text
approximately 468,000 total tokens
```

Use hosted models only for the optional LLM baseline.

## Caching

Cache by:

```text
hash(
  model
  + model_version
  + prompt_version
  + trace_hash
  + configuration_hash
)
```

Scoring and report generation must never cause additional model calls.

---

## 23. Recommended Local Stack

```text
Python 3.12
uv
Pydantic
Typer
Polars
PyArrow
SQLite
SQLite FTS5
FAISS or hnswlib
sentence-transformers
NetworkX
Jinja2
Rich
Pytest
Ruff
Pyright or Mypy
Docker
```

Optional later stack:

```text
Postgres
pgvector
Neo4j or Memgraph
S3-compatible object storage
Redis
```

Do not add production infrastructure before the local benchmark works.

---

## 24. CLI Specification

### Validate

```bash
afwb validate
```

### Generate reference traces

```bash
afwb generate references
```

### Generate mutated traces

```bash
afwb generate mutations
```

### Run RCA benchmark

```bash
afwb run-rca \
  --system hybrid-open \
  --split validation \
  --output results/raw/hybrid-open.jsonl
```

### Build memory indexes

```bash
afwb memory index \
  --variant temporal_hybrid
```

### Run memory benchmark

```bash
afwb run-memory \
  --scenarios memory-v0.1 \
  --variants rolling_context,vector_only,bm25_vector,graph_files,temporal_hybrid \
  --output results/raw/memory-results.jsonl
```

### Score

```bash
afwb score \
  --predictions results/raw \
  --output results/scored
```

### Replay

```bash
afwb replay \
  --predictions results/raw/hybrid-open.jsonl \
  --output results/replay
```

### Report

```bash
afwb report \
  --results results/scored \
  --output results/reports/afwb-v0.1.html
```

---

## 25. Implementation Milestones

## Milestone 1 — Foundation

Deliver:

- Repository structure
- Pydantic schemas
- CLI skeleton
- Mock model
- Mock tools
- Custom runner
- First 4 scenarios

Acceptance:

- Clean installation
- Deterministic outputs
- Unit tests passing

## Milestone 2 — RCA Core

Deliver:

- 24 scenarios
- Reference and mutated runs
- Gold labels
- Rules baseline
- Last-error baseline
- RCA scoring

Acceptance:

- Exact reproducibility
- All scenarios validated

## Milestone 3 — Replay

Deliver:

- Predefined remediation registry
- Replay runner
- Regression checks
- Cost and latency comparison

Acceptance:

- At least 18 of 24 scenarios replayable
- No arbitrary patch generation required

## Milestone 4 — Memory Core

Deliver:

- Rolling-context baseline
- Full-log baseline
- Vector-only retrieval
- BM25 + vector retrieval
- Graph + file retrieval
- Ten memory scenarios

Acceptance:

- Identical task conditions across variants
- Retrieval budgets enforced

## Milestone 5 — Temporal Hybrid

Deliver:

- File-version tracking
- Valid-from and valid-until metadata
- Superseded-memory handling
- Temporal filtering
- Selective file-fragment loading

Acceptance:

- Stale-state scenarios pass temporal checks
- False-recall scenarios remain task isolated

## Milestone 6 — Reporting and Release

Deliver:

- JSONL results
- Parquet analytics
- Markdown report
- HTML report
- Reproducibility guide
- Limitations
- Claims policy
- Release archive

Acceptance:

- Full benchmark runs from a clean checkout
- No hosted API required for core results

---

## 26. CI Requirements

Run on each pull request:

```text
Lint
Type check
Unit tests
Schema validation
Scenario validation
Deterministic RCA smoke test
Deterministic memory smoke test
Replay smoke test
Dataset checksum verification
```

Run manually or nightly:

```text
Optional hosted LLM baseline
Full memory comparison
Performance regression checks
Report rebuild
```

Do not run hosted-model evaluations on every commit.

---

## 27. Acceptance Criteria for Version 0.1

AFWB Lite v0.1 is ready when:

1. All 24 RCA scenarios are validated.
2. All 10 memory scenarios are implemented.
3. Reference, mutation, and remediation are documented.
4. Gold root-cause and first-observable spans exist.
5. Rules, last-error, and graph baselines run locally.
6. At least 18 scenarios support deterministic replay.
7. All memory variants respect retrieval budgets.
8. Stale-memory and cross-task contamination are measured.
9. Full results are generated from saved files.
10. The core benchmark uses no hosted-model API.
11. Optional LLM calls are cached.
12. A clean checkout reproduces deterministic results.
13. Limitations and conflicts are published.
14. Every public claim maps to a result file.

---

## 28. Claims Policy

Every public claim must be labeled as one of:

### Observed

Directly measured in the released benchmark.

### Supported

Observed across multiple scenarios or configurations with uncertainty reported.

### Hypothesis

Plausible but not sufficiently demonstrated.

### Out of scope

Not tested by the benchmark.

Example:

```text
Observed:
The graph-guided memory variant retrieved the gold evidence with fewer
context tokens than the full-log baseline on 8 of 10 released scenarios.

Supported:
Temporal filtering reduced stale-memory retrieval across the evaluated
state-versioning scenarios.

Hypothesis:
The same architecture will reduce cost on long-running production agents.

Out of scope:
The benchmark does not establish that graph databases are always better
than filesystem-based memory systems.
```

---

## 29. Conflict-of-Interest Disclosure

```text
The benchmark was initiated and maintained by contributors affiliated with
Lumniverse, which develops commercial tooling for AI-agent observability,
root-cause analysis, runtime memory, and cost optimization.

To reduce product bias, the benchmark publishes its scenarios, schemas,
scoring code, baseline implementations, raw predictions, configurations,
and evaluation methodology. Lumniverse must be evaluated using the same
protocol as every other system.
```

---

## 30. Suggested Research Positioning

### Benchmark title

> AFWB Lite: Diagnosing Agent Failures, Waste, and Runtime Memory

### Paper title

> Beyond Traces: Benchmarking Root-Cause Analysis, Waste Attribution, and External Memory for AI Agents

### Core public message

> We evaluate whether agent systems can identify the earliest causal failure,
> quantify avoidable execution waste, recommend a verified remediation, and
> retrieve only the evidence needed to avoid repeating mistakes.

---

## 31. Initial Results Tables

## RCA scorecard

| System | Failure F1 | Root-Cause Macro F1 | Exact Localization | Waste MAE | Replay Success | Cost/Run |
|---|---:|---:|---:|---:|---:|---:|
| Last error | | | | | | |
| Rules | | | | | | |
| Dependency graph | | | | | | |
| Hybrid open | | | | | | |
| Optional LLM judge | | | | | | |

## Memory scorecard

| Variant | Task Success | Evidence Recall@5 | Context Tokens | Repeated Actions | Stale Recall | Cost |
|---|---:|---:|---:|---:|---:|---:|
| Rolling context | | | | | | |
| Full log | | | | | | |
| Vector only | | | | | | |
| BM25 + vector | | | | | | |
| Graph + files | | | | | | |
| Temporal hybrid | | | | | | |

Do not collapse these results into one opaque score in version 0.1.

---

## 32. Final Recommendation

Build the benchmark in this order:

```text
24 deterministic RCA scenarios
        ↓
Rules and graph baselines
        ↓
Predefined remediation replay
        ↓
10 runtime-memory scenarios
        ↓
Vector versus graph-guided retrieval
        ↓
Temporal validity and selective file retrieval
        ↓
Optional low-cost LLM baseline
        ↓
Public report and reproducible release
```

This design is small enough to complete, cheap enough to run locally, and strong enough to produce publishable evidence.

The larger 120+ scenario, multi-framework benchmark should remain the long-term roadmap after version 0.1 proves that the tasks, metrics, and architecture produce meaningful results.
