from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RootCauseCategory(str, Enum):
    TOOL_ARGUMENT_ERROR = "TOOL_ARGUMENT_ERROR"
    SIDE_EFFECT_DUPLICATION = "SIDE_EFFECT_DUPLICATION"
    TOOL_RETRY_STORM = "TOOL_RETRY_STORM"
    LOOP_NON_TERMINATION = "LOOP_NON_TERMINATION"
    TOOL_RESULT_MISINTERPRETATION = "TOOL_RESULT_MISINTERPRETATION"
    HANDOFF_CONTEXT_LOSS = "HANDOFF_CONTEXT_LOSS"
    STALE_STATE_USE = "STALE_STATE_USE"
    CONTEXT_WINDOW_EVICTION = "CONTEXT_WINDOW_EVICTION"
    MEMORY_FALSE_RECALL = "MEMORY_FALSE_RECALL"
    STATE_CORRUPTION = "STATE_CORRUPTION"
    MISSING_FILTER = "MISSING_FILTER"
    RERANKING_ERROR = "RERANKING_ERROR"
    STALE_DOCUMENT = "STALE_DOCUMENT"
    EXCESSIVE_RETRIEVAL = "EXCESSIVE_RETRIEVAL"
    RETRIEVAL_MISS = "RETRIEVAL_MISS"
    OVERSIZED_MODEL_USE = "OVERSIZED_MODEL_USE"
    SERIAL_EXECUTION_WASTE = "SERIAL_EXECUTION_WASTE"
    DUPLICATE_RETRIEVAL = "DUPLICATE_RETRIEVAL"
    UNNECESSARY_AGENTIC_STEP = "UNNECESSARY_AGENTIC_STEP"
    HANDOFF_TO_WRONG_AGENT = "HANDOFF_TO_WRONG_AGENT"
    AGGREGATION_ERROR = "AGGREGATION_ERROR"
    RATE_LIMIT_UNHANDLED = "RATE_LIMIT_UNHANDLED"
    DEPENDENCY_VERSION_ERROR = "DEPENDENCY_VERSION_ERROR"
    MODEL_CAPABILITY_MISMATCH = "MODEL_CAPABILITY_MISMATCH"


class RemediationType(str, Enum):
    ARGUMENT_SCHEMA_VALIDATION = "ARGUMENT_SCHEMA_VALIDATION"
    IDEMPOTENCY_KEY = "IDEMPOTENCY_KEY"
    RETRY_POLICY_CHANGE = "RETRY_POLICY_CHANGE"
    TERMINATION_CONDITION = "TERMINATION_CONDITION"
    HANDOFF_CONTRACT = "HANDOFF_CONTRACT"
    STATE_VERSIONING = "STATE_VERSIONING"
    STATE_CHECKPOINTING = "STATE_CHECKPOINTING"
    RETRIEVAL_FILTER = "RETRIEVAL_FILTER"
    RERANKING_CHANGE = "RERANKING_CHANGE"
    CONTEXT_TRIMMING = "CONTEXT_TRIMMING"
    MODEL_DOWNGRADE = "MODEL_DOWNGRADE"
    MODEL_UPGRADE = "MODEL_UPGRADE"
    PARALLELIZATION = "PARALLELIZATION"
    CACHE_ADDITION = "CACHE_ADDITION"
    WORKFLOW_CONVERSION = "WORKFLOW_CONVERSION"
    OUTPUT_VALIDATION = "OUTPUT_VALIDATION"
    DEPENDENCY_PINNING = "DEPENDENCY_PINNING"
    STATE_SCHEMA_VALIDATION = "STATE_SCHEMA_VALIDATION"
    CONFIDENCE_GATE = "CONFIDENCE_GATE"


class SpanStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class TraceStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WASTEFUL = "wasteful"


class TraceVariant(str, Enum):
    REFERENCE = "reference"
    MUTATED = "mutated"


class ResourceUsage(BaseModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    latency_ms: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0)

    def __add__(self, other: ResourceUsage) -> ResourceUsage:
        return ResourceUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            tool_calls=self.tool_calls + other.tool_calls,
            latency_ms=self.latency_ms + other.latency_ms,
            cost_usd=round(self.cost_usd + other.cost_usd, 12),
        )


class RemediationSpec(BaseModel):
    remediation_type: RemediationType
    remediation_id: str = Field(min_length=1)
    target_component: str = Field(min_length=1)


class ScenarioStepSpec(BaseModel):
    span_id: str = Field(min_length=1)
    parent_span_id: str | None = None
    type: Literal["model", "tool", "validation", "control_flow", "state"]
    name: str = Field(min_length=1)
    status: SpanStatus
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    usage: ResourceUsage = Field(default_factory=ResourceUsage)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScenarioRunSpec(BaseModel):
    expected_status: TraceStatus
    steps: list[ScenarioStepSpec] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_span_graph(self) -> ScenarioRunSpec:
        span_ids = [step.span_id for step in self.steps]
        if len(span_ids) != len(set(span_ids)):
            raise ValueError("scenario run contains duplicate span IDs")
        known = set(span_ids)
        for step in self.steps:
            if step.parent_span_id is not None and step.parent_span_id not in known:
                raise ValueError(
                    f"parent span {step.parent_span_id!r} is not defined in run"
                )
        return self


class ScenarioDefinition(BaseModel):
    scenario_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    family: str = Field(min_length=1)
    description: str = Field(min_length=1)
    seed: int = Field(default=42)
    memory_test: bool = False
    root_cause_category: RootCauseCategory
    mutation: str = Field(min_length=1)
    symptom: str = Field(min_length=1)
    remediation: RemediationSpec
    reference: ScenarioRunSpec
    mutated: ScenarioRunSpec


class Span(BaseModel):
    span_id: str = Field(min_length=1)
    parent_span_id: str | None = None
    type: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: SpanStatus
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    started_at: str = Field(min_length=1)
    ended_at: str = Field(min_length=1)
    latency_ms: int = Field(ge=0)
    usage: ResourceUsage = Field(default_factory=ResourceUsage)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_latency(self) -> Span:
        if self.latency_ms != self.usage.latency_ms:
            raise ValueError("span latency_ms must match usage.latency_ms")
        return self


class Trace(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    run_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    variant: TraceVariant
    framework: str = Field(min_length=1)
    model: str = Field(min_length=1)
    seed: int
    status: TraceStatus
    started_at: str = Field(min_length=1)
    ended_at: str = Field(min_length=1)
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_tool_calls: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0)
    total_latency_ms: int = Field(ge=0)
    spans: list[Span] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_totals(self) -> Trace:
        usage = ResourceUsage()
        for span in self.spans:
            usage += span.usage
        if self.total_input_tokens != usage.input_tokens:
            raise ValueError("trace total_input_tokens must equal span usage sum")
        if self.total_output_tokens != usage.output_tokens:
            raise ValueError("trace total_output_tokens must equal span usage sum")
        if self.total_tool_calls != usage.tool_calls:
            raise ValueError("trace total_tool_calls must equal span usage sum")
        if self.total_latency_ms != usage.latency_ms:
            raise ValueError("trace total_latency_ms must equal span usage sum")
        if round(self.total_cost_usd, 12) != round(usage.cost_usd, 12):
            raise ValueError("trace total_cost_usd must equal span usage sum")
        return self


class GoldLabel(BaseModel):
    scenario_id: str = Field(min_length=1)
    failed: bool
    root_cause_category: RootCauseCategory
    root_cause_span_id: str = Field(min_length=1)
    first_observable_failure_span_id: str = Field(min_length=1)
    remediation: RemediationSpec
    avoidable_usage: ResourceUsage = Field(default_factory=ResourceUsage)
