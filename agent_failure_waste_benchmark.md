# Agent Failure & Waste Benchmark (AFWB)

**Version:** 0.1  
**Status:** Implementation specification  
**Maintainer:** Lumniverse  
**Primary objective:** Build and publish a reproducible benchmark for diagnosing failures, inefficiency, and avoidable cost in AI-agent executions.

---

## 1. Executive Summary

The Agent Failure & Waste Benchmark, abbreviated **AFWB**, measures whether an observability or root-cause analysis system can correctly explain:

1. **Why an AI-agent run failed**
2. **Where the failure first became observable**
3. **Which component caused the failure**
4. **How much cost or latency was avoidable**
5. **Which remediation would most likely prevent recurrence**

The benchmark must evaluate more than trace collection. It should distinguish between:

- Recording a trace
- Detecting that something went wrong
- Localizing the failure
- Identifying the actual root cause
- Estimating recoverable waste
- Recommending a valid fix
- Verifying whether the proposed fix works

The benchmark should be open, reproducible, vendor-neutral, and usable by:

- Agent framework maintainers
- Observability vendors
- Evaluation vendors
- AI platform teams
- Researchers studying agent reliability
- Enterprises deploying production agents

The initial release should focus on deterministic and semi-deterministic failure scenarios that can be reproduced reliably across multiple agent frameworks and model families.

---

## 2. Core Research Thesis

### Primary thesis

> AI-agent failures and excessive cost are often caused by execution architecture, state handling, retrieval, tool coordination, and control-flow design—not only by model intelligence.

### Secondary thesis

> A trace is not a diagnosis. A useful RCA system must identify the earliest causal failure, distinguish causes from downstream symptoms, quantify avoidable waste, and recommend an actionable remediation.

### Hypotheses to test

- **H1:** General-purpose LLM judges will detect obvious failures but perform poorly on exact root-cause localization.
- **H2:** Rules-based systems will perform well on known mechanical failures but poorly on semantic and multi-step failures.
- **H3:** Hybrid RCA systems combining trace rules, dependency analysis, cost analysis, and model reasoning will outperform single-method baselines.
- **H4:** A meaningful portion of agent cost can be classified as avoidable waste caused by retries, loops, duplicate calls, oversized models, irrelevant retrieval, and unnecessary reasoning.
- **H5:** Failure-step localization and root-cause classification are more operationally useful than a single pass/fail score.
- **H6:** Some tasks commonly implemented as agents are better represented as deterministic workflows.
- **H7:** Proposed remediation quality can be evaluated by replaying the scenario after applying the fix.

These are hypotheses, not conclusions. The benchmark must be designed so that negative or mixed results can also be published.

---

## 3. Benchmark Scope

### 3.1 Included in version 1

AFWB v1 should include:

- Single-agent runs
- Multi-step tool-using agents
- Retrieval-augmented agents
- Planner-executor agents
- Multi-agent handoffs
- Deterministic and semi-deterministic failures
- Model-generated and system-generated failures
- Cost and latency waste
- Replayable scenarios
- Synthetic and public-data-based tasks
- Multiple frameworks
- Multiple model classes

### 3.2 Excluded from version 1

Do not include the following until the benchmark is stable:

- Safety-policy benchmarking
- Adversarial jailbreak evaluation
- Long-running autonomous agents lasting hours or days
- Human-in-the-loop productivity measurement
- Proprietary customer traces without explicit permission
- Subjective task-quality evaluation without a reference answer
- Claims about all agent architectures
- Claims that one product solves every failure mode

### 3.3 Target frameworks

Implement adapters for at least three frameworks in the first public release:

- LangGraph
- OpenAI Agents SDK
- CrewAI or AutoGen
- A minimal custom Python agent loop

A benchmark scenario must not depend on a feature unique to one framework unless it is marked as framework-specific.

### 3.4 Target model classes

Use at least:

- One high-capability hosted model
- One lower-cost hosted model
- One open-weight model
- One deterministic mocked model for reproducibility tests

Do not publish conclusions based on only one provider.

---

## 4. Primary Benchmark Tasks

AFWB should expose six separate tasks.

### Task A: Failure Detection

Determine whether a run contains a material failure.

**Input:** Complete execution trace  
**Output:**

```json
{
  "failed": true,
  "confidence": 0.97
}
```

### Task B: Root-Cause Classification

Assign the primary failure to one category from the benchmark taxonomy.

**Input:** Complete execution trace  
**Output:**

```json
{
  "root_cause_category": "TOOL_ARGUMENT_ERROR",
  "confidence": 0.91
}
```

### Task C: Failure-Step Localization

Identify the earliest trace span where the causal failure became observable.

**Input:** Complete execution trace  
**Output:**

```json
{
  "root_cause_span_id": "span_014",
  "first_observable_failure_span_id": "span_012",
  "confidence": 0.84
}
```

### Task D: Waste Estimation

Estimate avoidable cost, token use, tool calls, and latency.

**Input:** Complete execution trace  
**Output:**

```json
{
  "avoidable_input_tokens": 18200,
  "avoidable_output_tokens": 3100,
  "avoidable_tool_calls": 7,
  "avoidable_latency_ms": 24500,
  "avoidable_cost_usd": 0.43
}
```

### Task E: Remediation Recommendation

Recommend the smallest practical change that would prevent recurrence.

**Input:** Complete execution trace  
**Output:**

```json
{
  "remediation_type": "ARGUMENT_SCHEMA_VALIDATION",
  "recommended_change": "Validate the date field against ISO-8601 before calling the booking tool.",
  "target_component": "booking_tool_adapter"
}
```

### Task F: Fix Verification

Apply the proposed remediation and replay the run.

**Input:** Scenario, original trace, proposed remediation  
**Output:**

```json
{
  "replay_passed": true,
  "failure_removed": true,
  "new_failure_introduced": false,
  "cost_delta_usd": -0.31,
  "latency_delta_ms": -17200
}
```

Each task must be scored separately. Do not collapse all results into one opaque score.

---

## 5. Failure Taxonomy

Every scenario must have one **primary root cause** and may have multiple secondary symptoms.

### 5.1 Planning and control flow

| Code | Failure |
|---|---|
| `PLAN_INCOMPLETE` | Required steps are omitted |
| `PLAN_INVALID_ORDER` | Steps are executed in the wrong order |
| `PREMATURE_TERMINATION` | Agent stops before task completion |
| `LOOP_NON_TERMINATION` | Agent repeats without satisfying an exit condition |
| `BRANCH_SELECTION_ERROR` | Wrong execution path is selected |
| `UNNECESSARY_AGENTIC_STEP` | Predictable step is delegated to an LLM |
| `GOAL_DRIFT` | Agent gradually optimizes for a different objective |
| `FAILED_RECOVERY_POLICY` | Recovery logic worsens or fails to resolve the error |

### 5.2 Tool use

| Code | Failure |
|---|---|
| `WRONG_TOOL_SELECTION` | Agent chooses an inappropriate tool |
| `TOOL_ARGUMENT_ERROR` | Tool receives malformed or invalid arguments |
| `TOOL_SCHEMA_MISMATCH` | Agent output does not satisfy tool schema |
| `TOOL_RESULT_MISINTERPRETATION` | Valid tool output is misunderstood |
| `TOOL_PERMISSION_ERROR` | Required permission or credential is unavailable |
| `TOOL_TIMEOUT_UNHANDLED` | Timeout is not handled correctly |
| `TOOL_RETRY_STORM` | Tool is retried excessively |
| `DUPLICATE_TOOL_CALL` | Equivalent tool call is repeated unnecessarily |
| `SIDE_EFFECT_DUPLICATION` | Non-idempotent action is executed more than once |

### 5.3 State and memory

| Code | Failure |
|---|---|
| `STATE_LOSS` | Required state is dropped |
| `STATE_CORRUPTION` | State is overwritten or malformed |
| `STALE_STATE_USE` | Agent uses outdated state |
| `CROSS_SESSION_LEAKAGE` | State from another session contaminates the run |
| `MEMORY_RETRIEVAL_MISS` | Relevant memory is not retrieved |
| `MEMORY_FALSE_RECALL` | Irrelevant memory is treated as relevant |
| `CONTEXT_WINDOW_EVICTION` | Important information falls out of context |
| `CHECKPOINT_RECOVERY_ERROR` | Resume operation restores the wrong state |

### 5.4 Retrieval

| Code | Failure |
|---|---|
| `RETRIEVAL_MISS` | Relevant document is not retrieved |
| `RETRIEVAL_DISTRACTOR` | Irrelevant content dominates retrieval |
| `BAD_CHUNKING` | Evidence is split or grouped incorrectly |
| `STALE_DOCUMENT` | Outdated information is selected |
| `MISSING_FILTER` | Required metadata filter is absent |
| `RERANKING_ERROR` | Correct candidate is retrieved but ranked too low |
| `CITATION_MISMATCH` | Answer is unsupported by cited evidence |
| `EXCESSIVE_RETRIEVAL` | Too many documents or tokens are retrieved |

### 5.5 Model behavior

| Code | Failure |
|---|---|
| `HALLUCINATED_FACT` | Unsupported fact is generated |
| `INSTRUCTION_MISREAD` | Explicit instruction is misunderstood |
| `FORMAT_NONCOMPLIANCE` | Required output format is violated |
| `OVER_REASONING` | Excessive reasoning adds cost without value |
| `UNDER_REASONING` | Insufficient reasoning causes failure |
| `CONFIDENCE_MISCALIBRATION` | Incorrect output is presented with high confidence |
| `MODEL_CAPABILITY_MISMATCH` | Model is too weak for the assigned task |
| `OVERSIZED_MODEL_USE` | Model is materially more expensive than needed |

### 5.6 Multi-agent coordination

| Code | Failure |
|---|---|
| `HANDOFF_CONTEXT_LOSS` | Context is lost during handoff |
| `HANDOFF_TO_WRONG_AGENT` | Task is assigned to an unsuitable agent |
| `CONFLICTING_AGENT_OUTPUTS` | Agents provide incompatible outputs |
| `DUPLICATED_AGENT_WORK` | Multiple agents perform equivalent work |
| `COORDINATION_DEADLOCK` | Agents wait or bounce indefinitely |
| `AGGREGATION_ERROR` | Correct partial outputs are combined incorrectly |
| `ROLE_BOUNDARY_VIOLATION` | Agent performs work outside its allowed role |

### 5.7 Infrastructure and integration

| Code | Failure |
|---|---|
| `RATE_LIMIT_UNHANDLED` | Rate limit causes incorrect failure |
| `NETWORK_ERROR_UNHANDLED` | Transient network failure is not recovered |
| `SERIALIZATION_ERROR` | Data cannot be serialized or parsed |
| `CLOCK_OR_TIMEZONE_ERROR` | Incorrect time handling causes failure |
| `CONFIGURATION_ERROR` | Invalid configuration causes the run to fail |
| `DEPENDENCY_VERSION_ERROR` | Version mismatch breaks execution |
| `OBSERVABILITY_GAP` | Required diagnostic data is missing |
| `TRACE_CORRELATION_ERROR` | Spans are linked to the wrong run |

### 5.8 Waste-only findings

A run may complete successfully but still contain waste.

| Code | Waste |
|---|---|
| `REDUNDANT_REASONING` | Repeated reasoning produces no new information |
| `UNNECESSARY_RETRY` | Retry occurs despite a terminal error |
| `DUPLICATE_RETRIEVAL` | Same retrieval is repeated |
| `EXCESSIVE_CONTEXT` | Input context is larger than necessary |
| `MODEL_ROUTING_WASTE` | Expensive model is used for a simpler step |
| `SERIAL_EXECUTION_WASTE` | Independent calls are executed serially |
| `CACHE_MISS_WASTE` | Reusable output is recomputed |
| `WORKFLOW_CANDIDATE` | Step should be deterministic rather than agentic |

---

## 6. Scenario Design

### 6.1 Scenario families

The first release should contain at least 120 scenarios.

Recommended distribution:

| Family | Minimum scenarios |
|---|---:|
| Planning/control flow | 20 |
| Tool use | 25 |
| State/memory | 20 |
| Retrieval | 20 |
| Model behavior | 15 |
| Multi-agent coordination | 10 |
| Infrastructure/integration | 10 |
| Successful but wasteful runs | 20 |

A scenario may test multiple categories, but only one category should be marked as the primary root cause.

### 6.2 Difficulty levels

Each scenario must have a difficulty label.

- **Level 1 — Obvious:** Failure is directly visible in one span.
- **Level 2 — Local:** Cause and symptom occur within a few adjacent spans.
- **Level 3 — Distributed:** Cause is separated from failure by several steps.
- **Level 4 — Causal chain:** Multiple failures occur, but one is primary.
- **Level 5 — Ambiguous:** Two explanations are plausible; evidence must distinguish them.

The public v1 benchmark should contain Levels 1–4. Level 5 should be introduced only after annotation quality is validated.

### 6.3 Scenario template

Every scenario must include:

```yaml
scenario_id: tool_argument_error_001
title: Invalid date passed to booking tool
description: >
  The agent receives a natural-language date, converts it incorrectly,
  and passes an invalid date to the booking API.
family: tool_use
difficulty: 2
primary_root_cause: TOOL_ARGUMENT_ERROR
secondary_symptoms:
  - TOOL_RETRY_STORM
expected_first_observable_span: span_006
expected_root_cause_span: span_007
expected_failed_span: span_013
task_success_expected: false
waste_expected: true
replay_supported: true
frameworks:
  - custom
  - langgraph
models:
  - mock
  - hosted_low_cost
seed: 42
```

### 6.4 Gold explanation

Each scenario must contain a human-written gold explanation:

```yaml
gold_explanation:
  summary: >
    The booking request failed because the date-normalization step produced
    an invalid ISO-8601 value before the booking tool was invoked.
  why_not_alternatives:
    - category: TOOL_TIMEOUT_UNHANDLED
      reason: The tool returned immediately with a validation error.
    - category: MODEL_CAPABILITY_MISMATCH
      reason: The failure was preventable through deterministic validation.
  recommended_fix:
    type: ARGUMENT_SCHEMA_VALIDATION
    implementation: >
      Normalize and validate dates before constructing the tool payload.
  expected_fix_effect:
    failure_removed: true
    avoidable_tool_calls_removed: 3
```

---

## 7. Dataset Structure

Use JSONL for public benchmark records and Parquet for analysis.

### 7.1 Repository layout

```text
afwb/
├── README.md
├── LICENSE
├── CITATION.cff
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml
├── uv.lock
├── Makefile
├── docker-compose.yml
├── configs/
│   ├── benchmark.yaml
│   ├── models.example.yaml
│   ├── pricing.yaml
│   └── logging.yaml
├── data/
│   ├── scenarios/
│   │   ├── planning/
│   │   ├── tools/
│   │   ├── state/
│   │   ├── retrieval/
│   │   ├── model/
│   │   ├── multi_agent/
│   │   ├── infrastructure/
│   │   └── waste/
│   ├── fixtures/
│   ├── documents/
│   ├── gold/
│   ├── generated/
│   └── releases/
│       └── v0.1.0/
├── src/
│   └── afwb/
│       ├── cli.py
│       ├── config.py
│       ├── schemas/
│       ├── runners/
│       ├── frameworks/
│       ├── models/
│       ├── tools/
│       ├── trace/
│       ├── scenarios/
│       ├── scoring/
│       ├── baselines/
│       ├── replay/
│       ├── analysis/
│       └── reporting/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── reproducibility/
│   └── golden/
├── scripts/
│   ├── generate_scenarios.py
│   ├── validate_dataset.py
│   ├── run_benchmark.py
│   ├── score_results.py
│   ├── build_leaderboard.py
│   └── export_paper_tables.py
├── results/
│   ├── raw/
│   ├── normalized/
│   ├── scored/
│   ├── reports/
│   └── leaderboard/
├── docs/
│   ├── methodology.md
│   ├── taxonomy.md
│   ├── annotation-guide.md
│   ├── reproducibility.md
│   ├── leaderboard-policy.md
│   ├── limitations.md
│   └── governance.md
├── paper/
│   ├── main.tex
│   ├── references.bib
│   ├── figures/
│   └── tables/
└── website/
    ├── app/
    ├── components/
    ├── public/
    └── content/
```

### 7.2 Trace schema

Use a framework-neutral trace format.

```json
{
  "run_id": "run_01HXYZ",
  "scenario_id": "tool_argument_error_001",
  "framework": "langgraph",
  "model": "provider/model-name",
  "seed": 42,
  "started_at": "2026-06-12T10:00:00Z",
  "ended_at": "2026-06-12T10:00:19Z",
  "status": "failed",
  "total_input_tokens": 18432,
  "total_output_tokens": 2861,
  "total_cost_usd": 0.517,
  "total_latency_ms": 19022,
  "spans": []
}
```

### 7.3 Span schema

```json
{
  "span_id": "span_007",
  "parent_span_id": "span_005",
  "type": "tool_call",
  "name": "booking.create",
  "started_at": "2026-06-12T10:00:05.201Z",
  "ended_at": "2026-06-12T10:00:05.489Z",
  "input": {
    "date": "2026-14-44"
  },
  "output": {
    "error": "invalid_date"
  },
  "status": "error",
  "input_tokens": 0,
  "output_tokens": 0,
  "cost_usd": 0,
  "latency_ms": 288,
  "metadata": {
    "retry_index": 0,
    "tool_version": "1.0.0"
  }
}
```

### 7.4 Prediction schema

All benchmark participants must return the same format.

```json
{
  "run_id": "run_01HXYZ",
  "system_name": "example-rca-system",
  "system_version": "0.2.0",
  "failed": true,
  "root_cause_category": "TOOL_ARGUMENT_ERROR",
  "root_cause_span_id": "span_007",
  "first_observable_failure_span_id": "span_006",
  "confidence": 0.91,
  "waste": {
    "avoidable_input_tokens": 12000,
    "avoidable_output_tokens": 1900,
    "avoidable_tool_calls": 3,
    "avoidable_latency_ms": 11000,
    "avoidable_cost_usd": 0.32
  },
  "remediation": {
    "type": "ARGUMENT_SCHEMA_VALIDATION",
    "target_component": "date_normalizer",
    "description": "Validate normalized dates before tool invocation."
  },
  "explanation": "The invalid date was generated before the booking tool call..."
}
```

---

## 8. Trace Normalization

Create a common intermediate representation so that all frameworks are scored consistently.

### Required normalized span types

- `agent_start`
- `agent_end`
- `llm_call`
- `tool_call`
- `tool_result`
- `retrieval`
- `memory_read`
- `memory_write`
- `handoff`
- `planner`
- `executor`
- `validation`
- `retry`
- `checkpoint`
- `error`
- `custom`

### Normalization rules

1. Preserve original trace IDs.
2. Preserve parent-child relationships.
3. Preserve timestamps with millisecond precision.
4. Record model and tool cost separately.
5. Record retries explicitly rather than inferring them later.
6. Retain raw provider payloads in a private artifact, not necessarily in the public dataset.
7. Redact secrets, credentials, personal data, and proprietary content.
8. Mark missing fields instead of inventing values.
9. Convert all costs to USD using the pricing table active at execution time.
10. Store the pricing snapshot with every benchmark release.

---

## 9. Scenario Generation

Use three methods.

### 9.1 Hand-authored deterministic scenarios

These should form the gold core of the benchmark.

Examples:

- Invalid tool argument
- Duplicate side effect
- Infinite retry loop
- Missing termination condition
- State overwritten by an unrelated step
- Retrieval without tenant filter
- Wrong handoff target
- Stale cache used after update
- Expensive model used for regex extraction

### 9.2 Controlled mutation

Start with a successful reference run and inject one mutation.

Mutation operators:

```text
- Delete a required state field
- Replace a tool name
- Corrupt one argument
- Remove a metadata filter
- Swap two plan steps
- Add a distractor document
- Duplicate a tool result
- Delay a tool beyond timeout
- Change a model route
- Remove a termination condition
- Truncate context
- Replace current state with stale state
```

Every mutated scenario must retain the original successful run for comparison.

### 9.3 Naturally occurring open traces

Include public traces only when:

- License permits redistribution
- Personal or confidential data is absent
- Ground truth can be established
- Scenario can be replayed or sufficiently reconstructed
- Source and transformations are documented

Do not make natural traces the majority of v1 because inconsistent ground truth will weaken the benchmark.

---

## 10. Ground-Truth Creation

### 10.1 Annotation process

Each non-trivial scenario should be reviewed by at least two annotators.

Annotators must independently label:

- Pass/fail
- Primary root-cause category
- Root-cause span
- First observable failure span
- Secondary symptoms
- Avoidable calls
- Avoidable tokens
- Avoidable latency
- Remediation type
- Explanation

Disagreements must be resolved by an adjudicator.

### 10.2 Annotation blind review

Annotators should not know which RCA system is being evaluated.

For scenarios derived from Lumniverse product development:

- Remove product-specific labels
- Use neutral span names
- Ensure annotations are not based on Lumniverse output
- Keep benchmark authors and system evaluators separate where practical

### 10.3 Inter-annotator agreement

Publish:

- Cohen’s kappa for categorical labels
- Span agreement rate
- Mean absolute difference for waste values
- Remediation agreement rate

Minimum release threshold:

```text
Root-cause category kappa >= 0.75
Failure-span agreement >= 0.80
Pass/fail agreement >= 0.90
```

If these thresholds are not met, refine the taxonomy or annotation guide before release.

---

## 11. Baselines

At least four baselines are required.

### Baseline 1: Random

Random category and random span.

Purpose: Establish the lower bound.

### Baseline 2: Rules Only

Implement deterministic checks for:

- Repeated tool calls
- Retry count
- Invalid JSON/schema
- Explicit errors
- Token thresholds
- Model cost thresholds
- Missing termination events
- Duplicate retrieval
- Identical consecutive prompts
- Long idle spans
- State-field deletion

Purpose: Measure the value of mechanical diagnostics.

### Baseline 3: LLM Judge

Give the normalized trace to a capable model with a fixed prompt.

Rules:

- No access to gold labels
- Fixed temperature
- Fixed output schema
- Same prompt across systems
- Run at least three seeds where stochasticity applies

Purpose: Measure general reasoning without specialized RCA logic.

### Baseline 4: Hybrid Open Baseline

Combine:

- Rules
- Trace dependency graph
- Error propagation
- Cost attribution
- LLM explanation

Publish this implementation openly.

Purpose: Give the community a credible baseline rather than only comparing against weak systems.

### Optional Baseline 5: Observability-Only Heuristic

Return the deepest error span or last failed span.

Purpose: Demonstrate the difference between visible failure and root cause.

### Product evaluation

Lumniverse may be evaluated, but results must be reported using the same protocol as every other system. Do not tune the public test split based on Lumniverse errors.

---

## 12. Metrics

### 12.1 Failure detection

- Accuracy
- Precision
- Recall
- F1
- AUROC, if confidence is available

### 12.2 Root-cause classification

- Macro F1
- Micro F1
- Per-category precision and recall
- Top-1 accuracy
- Top-3 accuracy
- Hierarchical accuracy by taxonomy family

Macro F1 should be the primary classification metric because category frequencies will be imbalanced.

### 12.3 Localization

- Exact span accuracy
- Within-1-span accuracy
- Within-3-span accuracy
- Mean graph distance from gold span
- Mean temporal distance from gold span
- First-observable-span accuracy

Graph distance is preferred over list-index distance when traces branch.

### 12.4 Waste estimation

For each quantity:

- Mean absolute error
- Median absolute error
- Mean absolute percentage error
- Signed bias

Evaluate:

- Input tokens
- Output tokens
- Tool calls
- Latency
- Cost

Also report waste classification F1:

```text
No material waste
Low waste
Moderate waste
High waste
```

Define thresholds in the release configuration.

### 12.5 Remediation quality

Use three scores.

#### A. Remediation type accuracy

Does the proposed fix belong to the correct category?

#### B. Human actionability score

Annotators rate from 1 to 5:

- 1: Vague or irrelevant
- 2: Points to area but not action
- 3: Actionable but incomplete
- 4: Specific and likely effective
- 5: Minimal, specific, and verified

#### C. Replay success

Primary metric:

```text
Percentage of proposed fixes that remove the original failure
without introducing a new failure.
```

### 12.6 Cost of diagnosis

Report:

- Diagnostic latency
- Diagnostic input tokens
- Diagnostic output tokens
- Diagnostic cost
- Peak memory, where measurable

An RCA system that is accurate but costs more than the failed run must be reported honestly.

---

## 13. Composite Score

Do not make the composite score the only result.

A suggested public score:

```text
AFWB Score =
  0.25 × Root-Cause Macro F1
+ 0.20 × Exact Localization Accuracy
+ 0.10 × Within-3 Localization Accuracy
+ 0.15 × Waste Estimation Score
+ 0.15 × Remediation Type Accuracy
+ 0.15 × Replay Success Rate
```

Normalize every component to `[0, 1]`.

The leaderboard must display all component metrics beside the composite score.

---

## 14. Statistical Methodology

For every published comparison:

1. Run each stochastic scenario with at least three seeds.
2. Report mean and standard deviation.
3. Use bootstrap confidence intervals for aggregate metrics.
4. Report per-family results.
5. Report results by difficulty level.
6. Correct for multiple comparisons where many systems are compared.
7. Publish raw predictions.
8. Publish failure cases.
9. Avoid significance claims based only on overlapping point estimates.
10. Separate benchmark-development results from final held-out test results.

Recommended split:

```text
Train: 50%
Validation: 20%
Public test: 15%
Private test: 15%
```

The private split should be used only for leaderboard integrity. Its scenarios should follow the published generation methodology.

---

## 15. Reproducibility Requirements

A release is reproducible only when an external user can:

1. Install the repository
2. Run a smoke benchmark locally
3. Reproduce deterministic baseline scores
4. Execute at least one framework adapter
5. Produce a scored result file
6. Generate the benchmark report
7. Verify dataset checksums

### Required commands

```bash
git clone https://github.com/<org>/afwb
cd afwb

uv sync
cp configs/models.example.yaml configs/models.yaml

make validate
make smoke
make test
make benchmark-baselines
make score
make report
```

### Docker path

```bash
docker compose up --build benchmark
```

### Deterministic smoke suite

Provide 10 scenarios using:

- Mock model
- Mock tools
- Fixed timing
- Fixed token accounting
- Fixed random seed

This suite must produce identical scores across runs.

---

## 16. CLI Specification

### List scenarios

```bash
afwb scenarios list
```

### Run benchmark

```bash
afwb run \
  --system baseline-rules \
  --split validation \
  --framework custom \
  --output results/raw/baseline-rules.jsonl
```

### Score predictions

```bash
afwb score \
  --predictions results/raw/baseline-rules.jsonl \
  --split validation \
  --output results/scored/baseline-rules.json
```

### Generate report

```bash
afwb report \
  --results results/scored \
  --output results/reports/report.html
```

### Validate submission

```bash
afwb submission validate \
  --input submission.jsonl
```

### Replay fixes

```bash
afwb replay \
  --predictions submission.jsonl \
  --split validation \
  --output results/replay/submission.jsonl
```

---

## 17. Framework Adapter Interface

Every framework adapter must implement:

```python
from typing import Protocol

class FrameworkAdapter(Protocol):
    name: str

    async def run_scenario(
        self,
        scenario: "Scenario",
        model: "ModelAdapter",
        seed: int,
    ) -> "NormalizedTrace":
        ...

    def normalize_trace(self, raw_trace: object) -> "NormalizedTrace":
        ...

    async def replay_with_fix(
        self,
        scenario: "Scenario",
        remediation: "Remediation",
        model: "ModelAdapter",
        seed: int,
    ) -> "NormalizedTrace":
        ...
```

Framework-specific data must not leak into the scoring layer.

---

## 18. RCA System Interface

Every evaluated RCA system must implement:

```python
from typing import Protocol

class RCASystem(Protocol):
    name: str
    version: str

    async def analyze(
        self,
        trace: "NormalizedTrace",
    ) -> "RCAPrediction":
        ...
```

Optional systems may also expose:

```python
async def propose_patch(
    scenario: "Scenario",
    trace: "NormalizedTrace",
) -> "PatchArtifact":
    ...
```

Do not require vendors to disclose proprietary implementation details. Require only predictions, metadata, runtime, and cost.

---

## 19. Waste Attribution Rules

Waste estimation must be based on explicit counterfactual rules.

### Example rules

#### Duplicate tool call

Avoidable cost equals the cost of all equivalent calls after the first valid call.

#### Retry storm

Avoidable cost excludes:

- First attempt
- Retries permitted by the scenario policy

All excess retries are waste.

#### Oversized model

Avoidable cost equals:

```text
Actual model cost - cost of the cheapest model that passes the scenario
```

This value may only be computed when the cheaper model has been tested successfully.

#### Excessive retrieval

Avoidable tokens equal retrieved tokens not required by the gold evidence set.

#### Workflow candidate

Avoidable cost equals the difference between the agentic implementation and the deterministic reference workflow.

### Important limitation

Do not label every failed token as waste. Some failed attempts are necessary exploration. Waste must be tied to a published counterfactual rule.

---

## 20. Remediation Taxonomy

Use a controlled set of remediation types.

```text
ARGUMENT_SCHEMA_VALIDATION
TOOL_SELECTION_CONSTRAINT
TOOL_TIMEOUT_POLICY
RETRY_POLICY_CHANGE
IDEMPOTENCY_KEY
TERMINATION_CONDITION
STATE_SCHEMA_VALIDATION
STATE_CHECKPOINTING
STATE_VERSIONING
RETRIEVAL_FILTER
RERANKING_CHANGE
CHUNKING_CHANGE
CONTEXT_TRIMMING
MODEL_ROUTING
MODEL_UPGRADE
MODEL_DOWNGRADE
CACHE_ADDITION
PARALLELIZATION
WORKFLOW_CONVERSION
HANDOFF_CONTRACT
OUTPUT_VALIDATION
CONFIDENCE_GATE
HUMAN_ESCALATION
OBSERVABILITY_INSTRUMENTATION
DEPENDENCY_PINNING
CONFIGURATION_FIX
```

A proposed fix may include free text, but it must map to one remediation type.

---

## 21. Benchmark Integrity

### Prevent benchmark leakage

- Keep a private test set.
- Rotate a portion of private scenarios every release.
- Publish generation operators.
- Do not publish private test prompts or exact traces.
- Track submissions by system version.
- Limit repeated private-test submissions.
- Flag systems that use scenario IDs as shortcuts.

### Prevent product bias

- Publish baseline code.
- Publish scoring code.
- Publish public traces.
- Accept external scenarios.
- Create a governance process.
- Document all benchmark changes.
- Invite external reviewers before major claims.

### Versioning

Use semantic versioning.

- Patch: documentation or scoring bug fix with no ranking change
- Minor: new scenarios or categories
- Major: task, metric, or taxonomy changes that break comparability

Every result must state the benchmark version.

---

## 22. Leaderboard

### Required columns

| Column | Description |
|---|---|
| System | Submitted RCA system |
| Version | Exact version |
| AFWB Score | Composite score |
| Root-Cause Macro F1 | Primary classification metric |
| Exact Localization | Exact causal span |
| Within-3 Localization | Near-causal span |
| Waste Error | Aggregate estimation error |
| Remediation Accuracy | Correct remediation type |
| Replay Success | Verified fixes |
| Diagnostic Cost | USD per analyzed run |
| Diagnostic Latency | Median latency |
| Open/Closed | Whether implementation is public |
| Date | Submission date |

### Leaderboard categories

Maintain separate tables for:

- Open systems
- Closed systems
- Rules-only systems
- LLM-only systems
- Hybrid systems
- Framework-specific systems

Do not rank systems with materially different access conditions in one undifferentiated table.

---

## 23. Publication Plan

Publish the work in phases.

### Phase 1: Methodology release

Publish:

- Research thesis
- Taxonomy
- 20 deterministic scenarios
- Trace schema
- Rules baseline
- LLM-judge baseline
- Scoring code

Goal: Receive feedback before large-scale execution.

### Phase 2: Benchmark v0.1

Publish:

- At least 120 scenarios
- Three framework adapters
- Three model classes
- Public train, validation, and test splits
- Private leaderboard split
- Initial leaderboard
- Technical report

### Phase 3: Research paper

Recommended paper title:

> Tracing Is Not Diagnosis: A Benchmark for Root-Cause Analysis and Waste Attribution in AI Agents

Alternative titles:

- The Agent Failure and Waste Benchmark
- Beyond Traces: Measuring Root-Cause Analysis for AI Agents
- Diagnosing Agentic Systems: Failure Localization, Waste Attribution, and Fix Verification

### Phase 4: Ongoing releases

Add:

- Real-world contributed traces
- Longer-running agents
- More frameworks
- More languages
- Human escalation scenarios
- Production incident bundles
- Regression benchmark suites

---

## 24. Technical Report Structure

### Abstract

State:

- Problem
- Benchmark contribution
- Dataset size
- Evaluated baselines
- Primary findings
- Limitations

### 1. Introduction

Explain:

- Why traces alone are insufficient
- Why agent failures are hard to diagnose
- Why cost waste matters
- Why existing evaluation is incomplete

### 2. Related Work

Cover:

- LLM evaluation
- Agent benchmarks
- Observability
- Software fault localization
- Distributed tracing
- AIOps
- Program repair
- Cost optimization

### 3. Taxonomy

Describe:

- Failure families
- Root causes versus symptoms
- Waste-only findings
- Remediation classes

### 4. Dataset

Document:

- Scenario generation
- Frameworks
- Models
- Splits
- Annotation
- Licensing

### 5. Tasks and Metrics

Define all six benchmark tasks and each metric.

### 6. Baselines

Describe:

- Random
- Rules
- LLM judge
- Hybrid baseline
- Any submitted systems

### 7. Results

Include:

- Overall results
- Per-category results
- Difficulty results
- Framework results
- Model results
- Cost and latency
- Error analysis

### 8. Ablations

Test:

- Rules removed
- Dependency graph removed
- Cost model removed
- LLM reasoning removed
- Raw trace versus normalized trace
- Full trace versus truncated trace

### 9. Discussion

Discuss:

- Which failures remain hard
- Where LLM judges overfit to visible errors
- Where rules outperform models
- Whether hybrid RCA is consistently better
- Whether fixes transfer across frameworks

### 10. Limitations

Include:

- Synthetic scenario bias
- Incomplete framework coverage
- Model drift
- Pricing changes
- Subjective remediation grading
- Limited long-horizon evaluation
- Potential author conflict of interest

### 11. Ethics and Responsible Release

Cover:

- Data privacy
- Secret redaction
- Customer trace handling
- Benchmark gaming
- Responsible disclosure of framework bugs

### 12. Conclusion

Summarize only findings supported by benchmark results.

---

## 25. Figures and Visuals

Create the following figures for the report and research page.

1. Benchmark architecture
2. Failure taxonomy tree
3. Trace with cause, symptom, and final failure marked separately
4. Root-cause Macro F1 by system
5. Localization accuracy by difficulty
6. Waste-estimation error by category
7. Diagnostic cost versus accuracy
8. Replay success by remediation type
9. Framework-by-failure heatmap
10. Model capability versus failure rate
11. Agentic versus deterministic workflow cost comparison
12. Example RCA report

All plots must be generated from saved result files, not manually edited.

---

## 26. Research Website

The benchmark website should contain:

### Homepage

- One-sentence problem statement
- Benchmark definition
- Key metrics
- Latest release
- Links to paper, code, dataset, and leaderboard

### Methodology

- Taxonomy
- Scenario construction
- Annotation
- Metrics
- Splits
- Reproducibility

### Interactive trace example

Show:

- Timeline
- Tool calls
- State changes
- Retrieval
- Cost
- Root-cause span
- Downstream symptoms
- Recommended fix

### Leaderboard

Allow filters by:

- Framework
- Failure family
- Difficulty
- Open versus closed
- Cost
- Latency

### Findings

Publish evidence, not marketing claims.

Example:

```text
LLM judges detected visible failures reliably but often selected the final
error span rather than the earliest causal span.
```

Avoid unsupported wording such as:

```text
All current agent observability systems are fundamentally incapable of RCA.
```

### Limitations

Display limitations prominently.

---

## 27. Open-Source Release Checklist

Before publishing:

- [ ] License selected
- [ ] Dataset licenses verified
- [ ] Secrets removed
- [ ] Personal data removed
- [ ] All scenarios validated
- [ ] Deterministic smoke tests pass
- [ ] Baselines reproducible
- [ ] Checksums generated
- [ ] Documentation reviewed
- [ ] Annotation agreement published
- [ ] Pricing snapshot stored
- [ ] Model versions pinned
- [ ] Random seeds recorded
- [ ] Raw predictions published
- [ ] Statistical analysis script published
- [ ] Limitations documented
- [ ] Conflict of interest disclosed
- [ ] External reviewer feedback incorporated
- [ ] Citation file added
- [ ] Release archive created
- [ ] DOI created through Zenodo or equivalent

---

## 28. CI/CD Requirements

Run on every pull request:

```text
- Lint
- Type check
- Unit tests
- Schema validation
- Scenario validation
- Deterministic smoke benchmark
- Dataset checksum verification
- Documentation link check
```

Run nightly or manually:

```text
- Hosted-model benchmark subset
- Multi-framework integration tests
- Cost-regression tests
- Leaderboard rebuild
```

Do not run expensive full benchmarks on every commit.

---

## 29. Acceptance Criteria for v0.1

AFWB v0.1 is ready only when:

1. At least 120 validated scenarios exist.
2. At least three framework adapters work.
3. At least four baselines are included.
4. Public and private splits are generated.
5. All scenarios conform to the schema.
6. The deterministic smoke suite is reproducible.
7. At least two annotators review non-trivial scenarios.
8. Root-cause category kappa is at least 0.75.
9. Every scenario has a successful reference or a documented reason why it cannot.
10. Replay is supported for at least 60% of scenarios.
11. The leaderboard shows component metrics.
12. A complete technical report is generated from repository data.
13. All benchmark claims can be traced to a result file.
14. Limitations and conflicts are explicitly disclosed.

---

## 30. Suggested Implementation Milestones

### Milestone 1: Foundation

Deliver:

- Schemas
- CLI skeleton
- Custom framework adapter
- Mock model
- Mock tools
- Ten deterministic scenarios
- Validation tests

### Milestone 2: Taxonomy and scoring

Deliver:

- Full taxonomy
- Root-cause scorer
- Localization scorer
- Waste scorer
- Remediation scorer
- HTML report

### Milestone 3: Baselines

Deliver:

- Random baseline
- Rules baseline
- LLM judge baseline
- Hybrid open baseline

### Milestone 4: Framework coverage

Deliver:

- LangGraph adapter
- OpenAI Agents SDK adapter
- CrewAI or AutoGen adapter

### Milestone 5: Dataset expansion

Deliver:

- 120 scenarios
- Annotation workflow
- Agreement calculation
- Train, validation, and test splits

### Milestone 6: Replay

Deliver:

- Remediation patch schema
- Replay runner
- Fix verification scorer
- Regression detection

### Milestone 7: Publication

Deliver:

- Technical report
- Research website
- Leaderboard
- Release archive
- DOI
- Announcement material

---

## 31. Codex Implementation Instructions

Use the following rules while implementing the repository.

### Engineering principles

1. Prefer simple, typed Python.
2. Use Pydantic models for schemas.
3. Use JSONL as the interchange format.
4. Use Parquet only for analytics.
5. Keep framework-specific logic behind adapters.
6. Keep scoring deterministic.
7. Never call an LLM from the scoring layer.
8. Store every benchmark configuration with the output.
9. Make all external calls mockable.
10. Add tests before adding large scenario batches.

### Recommended stack

```text
Python 3.12
uv
Pydantic
Typer
Polars
PyArrow
NetworkX
Rich
Jinja2
Pytest
Ruff
Mypy or Pyright
Docker
```

### First implementation sequence

```text
1. Create repository structure.
2. Define Scenario, Trace, Span, Prediction, Remediation, and Score schemas.
3. Implement schema validation.
4. Implement custom agent runner.
5. Implement mock model and mock tools.
6. Create ten deterministic scenarios.
7. Implement failure classification scoring.
8. Implement span localization scoring.
9. Implement waste scoring.
10. Implement CLI commands.
11. Implement rules baseline.
12. Implement report generation.
13. Add framework adapters.
14. Expand scenarios.
15. Add replay.
16. Build leaderboard.
```

### Completion rule

Do not mark a milestone complete unless:

- Tests pass
- Documentation is updated
- Example command works
- Output is stored in the expected schema
- Reproducibility is verified from a clean environment

---

## 32. Initial Ten Scenarios

Start with these scenarios.

### 1. Invalid booking date

- Root cause: `TOOL_ARGUMENT_ERROR`
- Symptom: repeated booking failure
- Fix: argument validation

### 2. Duplicate payment

- Root cause: `SIDE_EFFECT_DUPLICATION`
- Symptom: two successful payment calls
- Fix: idempotency key

### 3. Infinite retry on terminal error

- Root cause: `TOOL_RETRY_STORM`
- Symptom: repeated identical 400 errors
- Fix: retry classification

### 4. Missing loop exit condition

- Root cause: `LOOP_NON_TERMINATION`
- Symptom: repeated planner-executor cycle
- Fix: termination condition

### 5. Tenant filter omitted

- Root cause: `MISSING_FILTER`
- Symptom: wrong customer document retrieved
- Fix: mandatory metadata filter

### 6. State overwritten after handoff

- Root cause: `HANDOFF_CONTEXT_LOSS`
- Symptom: next agent repeats completed work
- Fix: handoff contract

### 7. Stale customer address

- Root cause: `STALE_STATE_USE`
- Symptom: shipment created for previous address
- Fix: state versioning

### 8. Expensive model used for extraction

- Root cause: `OVERSIZED_MODEL_USE`
- Symptom: successful but costly run
- Fix: model routing

### 9. Correct document ranked below distractor

- Root cause: `RERANKING_ERROR`
- Symptom: unsupported answer
- Fix: reranking change

### 10. Parallel tools executed serially

- Root cause: `SERIAL_EXECUTION_WASTE`
- Symptom: correct output with excessive latency
- Fix: parallelization

---

## 33. Claims Policy

Every public claim must be assigned one status.

### Observed

Directly measured in the released benchmark.

### Supported

Observed across multiple scenarios, frameworks, or models with confidence intervals.

### Hypothesis

Plausible but not sufficiently demonstrated.

### Out of scope

Not tested by the benchmark.

Examples:

```text
Observed:
The rules baseline detected duplicate tool calls with 100% recall
on the released duplicate-call scenarios.

Supported:
Hybrid RCA achieved higher root-cause Macro F1 than the evaluated
rules-only and LLM-only baselines across three frameworks.

Hypothesis:
Hybrid diagnosis will remain superior on long-running production agents.

Out of scope:
The benchmark does not establish that all agent observability systems
fail to perform RCA.
```

This policy should be used on the website, in the paper, and in product marketing.

---

## 34. Conflict-of-Interest Disclosure

Use a clear disclosure.

```text
The benchmark was initiated and maintained by contributors affiliated with
Lumniverse, which develops commercial tooling for AI-agent observability,
root-cause analysis, and cost optimization. To reduce product bias, the
benchmark publishes its public scenarios, schemas, scoring code, baseline
implementations, raw predictions, and evaluation methodology. Commercial
systems, including Lumniverse, are evaluated using the same submission and
scoring protocol.
```

---

## 35. Final Deliverables

The complete project should produce:

```text
- Open benchmark repository
- Versioned dataset
- Framework-neutral trace format
- Failure taxonomy
- Waste taxonomy
- Remediation taxonomy
- Baseline implementations
- Scoring package
- Replay engine
- Public leaderboard
- Technical report
- Research website
- Reproducibility guide
- DOI-backed release archive
```

The benchmark should be treated as a research asset first and a marketing asset second. Its long-term value will come from credibility, reproducibility, neutral methodology, and external participation.
