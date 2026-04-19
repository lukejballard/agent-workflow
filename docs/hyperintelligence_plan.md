# Hyperintelligence Plan for `lukejballard/agent-workflow`

## 1) Landscape Mapping

### Current capability level (honest baseline)

This repository already has a stronger control-plane foundation than most "agent framework" projects. The core strengths are not flashy, but they are the exact foundations that production systems usually discover too late: explicit workflow phases, machine-readable metadata, scoped guidance, and a typed context contract.

What is already strong:

- **Single-entry orchestration discipline**: the repo enforces one gateway (`@orchestrator`) and internal phase transitions rather than free-form agent swarms. That lowers operational chaos.
- **Schema-backed context engineering**: `.github/agent-platform/context-packet.schema.json` and `.github/agent-platform/run-artifact-schema.json` already model short-term and episodic structure.
- **Skill routing scaffold**: `.github/agent-platform/skill-registry.json` and trigger matrix patterns in `.github/agent-platform/workflow-manifest.json` create a policy surface for extensibility.
- **Spec and research workflow**: `docs/specs/active/` and `docs/specs/research/` support anti-drift planning.
- **Quality governance in CI**: workflow scripts validate hygiene and metadata consistency.

What is materially missing:

- **Durable runtime execution layer** (stateful task engine, checkpoint/resume semantics, deterministic retries).
- **Typed event stream for real-time operator UX** (SSE/WebSocket contracts).
- **First-class tool router abstraction** (permissioning, timeout/retry policy, call provenance).
- **Operational memory subsystem** (beyond packet/run artifact): retrieval index lifecycle, TTL/invalidation, contamination controls.
- **Hard separation between planning, execution, and validation at module boundaries** in Python runtime code.
- **Evaluation and learning loop as a productized subsystem**, not ad hoc post-hoc commentary.

### Leverage points in current architecture

Highest leverage comes from upgrading existing strengths, not replacing them:

1. **Treat `workflow-manifest.json` as policy kernel** and bind runtime transitions to that manifest.
2. **Promote context packet and run artifact from "documentation contract" to runtime API contract**.
3. **Add a typed event envelope** that mirrors packet/artifact lifecycle for UI observability.
4. **Implement planner/executor/validator boundaries under `src/` with testable interfaces** while preserving single-entry orchestration.
5. **Use skill registry as a routing policy layer** for optional external frameworks (LangGraph/DSPy/etc.), not as direct orchestration replacement.

### Capability maturity estimate

- **Governance maturity**: high.
- **Runtime maturity**: low-to-medium (scaffold stage).
- **Observability maturity**: medium at docs/process level, low at live runtime telemetry level.
- **Operator UX maturity**: low (no full control surface yet).
- **Learning-loop maturity**: low (conceptual support exists; execution support is limited).

The path to hyperintelligence is not "more agents." It is **strong runtime semantics + explicit memory + hard verification loops + operator-grade observability**.

---

## 2) Top 10 GitHub Repositories by Agentic Leverage Potential

> Ranking criterion: transfer value to this repo’s Python-heavy backend, React/TypeScript control surface, and single-entry orchestrator policy.

| Rank | Name + URL | Primary purpose | Key architectural idea | Why it matters here | Copy / adapt / avoid | Integration difficulty | Production readiness | Adversarial critique |
|---|---|---|---|---|---|---|---|---|
| 1 | **LangGraph** — https://github.com/langchain-ai/langgraph | Stateful agent workflow orchestration | Graph-native state machine with durable checkpoints and interrupts | Maps directly to orchestrator phases and DAG execution | Copy explicit node state; adapt state schema to context packet; avoid hidden implicit state | Medium | Production-ish / mature beta | Strong model, but teams overfit to framework abstractions and underinvest in domain state quality |
| 2 | **Temporal** — https://github.com/temporalio/temporal | Durable long-running workflow engine | Deterministic workflow history + activity retries + replay | Best-in-class reliability for long tasks, retries, resumptions | Copy idempotent activity model; adapt to planner/executor boundaries; avoid premature cluster complexity | High | Production | Operational overhead is real; misuse of workflow code can create deterministic replay bugs |
| 3 | **AutoGen** — https://github.com/microsoft/autogen | Multi-agent coordination framework | Event/message-driven specialist agent collaboration | Useful when orchestrator needs bounded specialist debates | Copy typed inter-agent protocol; adapt as optional branch; avoid unconstrained chatter loops | Medium-High | Beta | Easy to create expensive conversational loops that feel smart but degrade throughput |
| 4 | **LlamaIndex** — https://github.com/run-llama/llama_index | Retrieval and knowledge workflows | Modular indexing + retriever abstraction + query workflows | Strong fit for semantic memory and retrieval layer | Copy retriever interfaces; adapt provenance capture into run artifacts; avoid indexing everything blindly | Medium | Production | RAG can become cargo cult; stale embeddings and poor chunking silently degrade output quality |
| 5 | **DSPy** — https://github.com/stanfordnlp/dspy | Programmatic LLM optimization | Declarative LM programs optimized by objective metrics | Ideal for offline tuning of prompts/routing policies | Copy optimize-by-metric loop; adapt to skill-level benchmarking; avoid online self-modifying behavior | Medium | Beta | Optimization can overfit benchmarks and reduce robustness in real tasks |
| 6 | **Letta (MemGPT lineage)** — https://github.com/letta-ai/letta | Long-horizon memory-centric agents | Tiered memory and memory operation semantics | Good blueprint for long-term/episodic memory mechanics | Copy memory tiers + write policies; adapt to context packet/run artifact; avoid unbounded memory growth | Medium | Beta | Memory systems rot without TTL, invalidation, and provenance discipline |
| 7 | **CrewAI** — https://github.com/crewAIInc/crewAI | Role-based multi-agent teams | Role/task decomposition with flow-like execution | Useful for controlled delegation patterns | Copy explicit role contracts; adapt as orchestrator-pluggable mode; avoid role theater with weak validation | Medium | Beta | Good DX, but production guarantees weaker than durable workflow engines |
| 8 | **OpenHands** — https://github.com/OpenHands/OpenHands | Autonomous software engineering agent platform | End-to-end coding agent runtime + sandbox + UI | Valuable reference for coding-agent ergonomics and controls | Copy auditability and sandbox separation patterns; adapt UI interaction models; avoid wholesale platform adoption | High | Beta | Huge scope; adopting too much creates hidden platform lock-in and complexity |
| 9 | **SWE-agent** — https://github.com/SWE-agent/SWE-agent | Repo-aware software-fixing agent | Structured repo interaction loop with benchmarks | Strong patterns for codebase comprehension + verification loops | Copy constrained action policy + eval harness ideas; adapt to this repo’s contracts; avoid blind autonomy defaults | Medium | Beta/Research | Works well in constrained benchmark settings; real enterprise repos expose brittleness quickly |
| 10 | **Agno** — https://github.com/agno-agi/agno | Lightweight typed agent framework + runtime | Typed agent/runtime composition with streamlined APIs | Useful for rapid typed agent components without full platform rewrite | Copy typed interfaces and light runtime conventions; adapt selectively; avoid adding another orchestration center | Medium | Beta | Attractive simplicity can hide future migration costs when requirements grow |

### Additional note: Prefect alternative

If Temporal feels too heavy early, **Prefect** (https://github.com/PrefectHQ/prefect) is a pragmatic stepping stone for task orchestration and observability. It is easier to start with but weaker than Temporal for strict deterministic replay semantics.

### Transfer strategy for this repo

- Keep orchestrator contract and policy in `.github/agent-platform/` untouched as source of truth.
- Introduce framework integrations behind adapter interfaces in `src/agent_runtime/`.
- Use skill registry triggers to gate when external frameworks are invoked.
- Enforce run artifact capture regardless of execution backend.

---

## 3) Top 10 YouTube Resources by Practical Engineering Value

> Objective: extract engineering mental models, not motivational summaries.

| Rank | Title / Channel / URL | Core technical ideas | Patterns worth stealing for this repo | Gaps / hype to watch |
|---|---|---|---|---|
| 1 | **Agentic Design Patterns** — DeepLearning.AI / Andrew Ng — https://www.youtube.com/watch?v=w7vqXL4PWEE | Reflection, planning, tool-use loops, decomposition | Encode explicit plan→act→critique transitions in planner/validator modules | Conceptual clarity is high, operational detail is light |
| 2 | **LangGraph deep-dives** — LangChain official channel — https://www.youtube.com/@LangChain/videos | Stateful graph execution, interrupt/resume, durable reasoning flow | Convert orchestrator phases into typed DAG nodes; persist node state snapshots | Framework-centric framing can underemphasize custom policy kernels |
| 3 | **AutoGen engineering talks** — Microsoft AutoGen team — https://www.youtube.com/@MicrosoftResearch/videos | Event-driven multi-agent messaging and role protocols | Add bounded specialist debates only at high-uncertainty branches | Many demos hide cost and loop-control issues |
| 4 | **Best Practices for Building Agentic AI Systems** — https://www.youtube.com/watch?v=Rbo7dsWIORM | Reliability over novelty, layered architecture, guardrails | Formalize permission gates + retries + eval harness before adding capabilities | Often too broad; requires translation into concrete modules |
| 5 | **Building Effective Agents with LangGraph** — LangChain — https://www.youtube.com/watch?v=aHCDrAbH_go | Agent-vs-workflow boundary discipline | Preserve single-entry orchestrator and use graph runtime as implementation detail | Over-indexing on graph tooling can hide domain-state design flaws |
| 6 | **Microsoft Build / Ignite AutoGen sessions (2024–2025)** — Microsoft Developer — https://www.youtube.com/@MicrosoftDeveloper/videos | Agent protocol design, enterprise concerns, extensibility | Use typed event envelopes and explicit handoff schema between planner/executor/validator | Vendor framing may skip failure-case nuance |
| 7 | **LlamaIndex advanced retrieval sessions (2024–2025)** — LlamaIndex channel — https://www.youtube.com/@LlamaIndex/videos | Retrieval topology, indexing strategy, source attribution | Build semantic memory adapters with provenance and confidence scoring | Retrieval demos often ignore invalidation and stale corpus drift |
| 8 | **Temporal durable execution talks** — Temporal channel — https://www.youtube.com/@temporalio/videos | Idempotency, deterministic replay, workflow/activity split | Implement task state machine with replay-safe transitions | Can feel heavy for teams not ready for distributed workflow ops |
| 9 | **OpenHands demos and architecture talks** — All Hands AI — https://www.youtube.com/@OpenHandsAI/videos | Autonomous SWE runtime, sandbox tooling, audit surfaces | Design DiffReviewer + tool trace views inspired by coding-agent control planes | Product demos can overstate end-to-end autonomy reliability |
| 10 | **DSPy tutorials and talks (2024–2025)** — Stanford NLP / community talks — https://www.youtube.com/results?search_query=DSPy+Stanford+NLP | Programmatic optimization of LM pipelines | Add offline optimization loop for route prompts and evaluator prompts | Optimization gains can vanish when evaluation sets are weak |

### High-signal mental models to carry forward

1. **State is the product**: natural-language logs are not enough; typed state transitions are mandatory.
2. **Plans are first-class artifacts**: if the plan is not machine-readable, execution and learning both rot.
3. **Critique must be bounded**: reflexive loops without stop criteria become latency and cost sinks.
4. **Operator trust is earned through observability**: timelines, diff previews, and reproducible traces matter more than eloquent responses.
5. **Memory requires lifecycle controls**: relevance windows, decay, and invalidation are as important as retrieval quality.

---

## 4) Agent Skill Map

### 4.1 Structured table (16 core skills)

| # | Skill | Why it matters most | Primary host component |
|---|---|---|---|
| 1 | Hierarchical task decomposition | Prevents monolithic brittle execution | Planner (DAG builder) |
| 2 | Retrieval-augmented reasoning | Grounds reasoning in repo reality | Memory layer + retrieval adapters |
| 3 | Memory compression and context pruning | Controls context bloat and drift | Context packet manager |
| 4 | Tool routing and selection | Limits unsafe/irrelevant calls | Tool router |
| 5 | Self-critique and revision loops | Catches plan flaws before execution | Validator |
| 6 | Multi-agent debate / adversarial validation | Reduces blind spots on high-risk tasks | Validator (optional specialist mode) |
| 7 | Codebase semantic mapping | Accelerates repo understanding | Semantic mapper service |
| 8 | Planning / execution separation | Improves testability and replayability | Planner + Executor module split |
| 9 | Failure recovery and retry | Makes long tasks resilient | Execution engine + state machine |
| 10 | Verification and test generation | Converts confidence into evidence | Validator + QA pipeline |
| 11 | Autonomous refactoring | Delivers quality gains safely | Executor + diff risk policy |
| 12 | Uncertainty detection and confidence calibration | Prevents overconfident bad actions | Validator + event model |
| 13 | Episodic memory capture | Supports longitudinal learning | Run artifact manager |
| 14 | Skill extraction and pattern reuse | Compounds improvements over time | Learning loop + skill registry |
| 15 | Feedback capture and preference learning | Aligns runtime behavior with operators | Learning loop + control UI |
| 16 | Post-task analysis and improvement loop | Converts outcomes into system upgrades | Learning loop pipeline |

### 4.2 Detailed implementation notes per skill

#### 1) Hierarchical task decomposition
- **What it does**: Breaks goals into dependency-ordered subtasks with contracts.
- **Required support**: DAG schema aligned to `current_step`/`task_graph` in context packet.
- **Where it fits**: Orchestrator classify→plan phases; planner module in backend.
- **Implementation approach**: Python planner emits `PlanStep` objects with `depends_on`, `input_contract`, `done_condition`.
- **How to test**: Deterministic fixture goals and expected DAG shapes; cycle detection tests.
- **Failure modes**: Over-fragmentation causing overhead; under-fragmentation causing opaque failures.

#### 2) Retrieval-augmented reasoning
- **What it does**: Injects grounded evidence into planning/execution decisions.
- **Required support**: semantic index + provenance metadata + retrieval policy.
- **Where it fits**: Semantic memory fields in context packet and run artifact evidence refs.
- **Implementation approach**: retrieval adapter interface with `retrieve(query, scope) -> MemoryEntry[]`.
- **How to test**: gold-query recall tests + negative tests for irrelevant retrieval.
- **Failure modes**: stale retrieval, context pollution, false confidence from weak sources.

#### 3) Memory compression and context pruning
- **What it does**: Condenses stale interaction while preserving critical constraints.
- **Required support**: context utilization metrics and trim policy.
- **Where it fits**: `context_health` policy in context packet.
- **Implementation approach**: compression strategies keyed by task phase and token budget.
- **How to test**: budget overflow simulations; preservation checks for goal/constraints/current step.
- **Failure modes**: lossy compression dropping critical facts; over-retention causing context overflow.

#### 4) Tool routing and selection
- **What it does**: Selects the right tool path with policy constraints.
- **Required support**: tool metadata, permission levels, timeout/retry policy.
- **Where it fits**: Tool router between executor and MCP/GitHub/filesystem tools.
- **Implementation approach**: scored routing policy (capability fit, safety level, latency profile).
- **How to test**: table-driven routing tests + denied-action policy tests.
- **Failure modes**: route oscillation, unsafe fallbacks, noisy retries.

#### 5) Self-critique and revision loops
- **What it does**: Evaluates plans/results against constraints before finalization.
- **Required support**: explicit critique rubric and stop conditions.
- **Where it fits**: Validator stage and `maxCritiquePasses` alignment.
- **Implementation approach**: validator outputs structured findings (`severity`, `evidence`, `fix_hint`).
- **How to test**: synthetic flawed plans and expected critique outputs.
- **Failure modes**: infinite critique loops, shallow critiques, contradictory revisions.

#### 6) Multi-agent debate / adversarial validation
- **What it does**: Uses independent perspectives for high-risk decisions.
- **Required support**: strict protocol and bounded rounds.
- **Where it fits**: Optional validator branch triggered by risk/uncertainty.
- **Implementation approach**: debate adapter with max rounds + arbitration rule.
- **How to test**: disagreement scenarios with deterministic arbitration outcomes.
- **Failure modes**: cost explosion, role collapse, no convergence.

#### 7) Codebase semantic mapping
- **What it does**: Builds conceptual map of files, modules, dependencies, ownership.
- **Required support**: indexing job and incremental refresh.
- **Where it fits**: pre-planning breadth scan and retrieval substrate.
- **Implementation approach**: build index from `src/`, `frontend/`, `tests/`, `.github/agent-platform/`.
- **How to test**: map coverage checks and dependency edge accuracy tests.
- **Failure modes**: stale map after refactors, hallucinated relationships.

#### 8) Planning / execution separation
- **What it does**: prevents runtime mutation of plan semantics during execution.
- **Required support**: immutable plan snapshots per run revision.
- **Where it fits**: planner emits plan; executor consumes plan only.
- **Implementation approach**: Python protocols (`Planner`, `Executor`) with strict DTOs.
- **How to test**: ensure executor never calls planner internals in unit tests.
- **Failure modes**: hidden coupling, side-channel plan edits.

#### 9) Failure recovery and retry
- **What it does**: retries transient errors while preserving correctness.
- **Required support**: error taxonomy + idempotency keys + backoff policy.
- **Where it fits**: executor and tool wrapper.
- **Implementation approach**: classify errors (TRANSIENT/PERMANENT/POLICY) and act accordingly.
- **How to test**: injected transient failures with expected retry counts.
- **Failure modes**: retry storms, duplicate side effects, masking real defects.

#### 10) Verification and test generation
- **What it does**: produces and runs checks tied to task objectives.
- **Required support**: verification matrix in run artifact.
- **Where it fits**: validator and QA task routing.
- **Implementation approach**: generate targeted checks from plan step contracts.
- **How to test**: mutation tests proving checks fail on intentionally broken variants.
- **Failure modes**: superficial tests, assertion mismatch to user objective.

#### 11) Autonomous refactoring
- **What it does**: quality improvements without behavior regressions.
- **Required support**: diff risk scoring + rollback strategy.
- **Where it fits**: executor when task class permits refactor.
- **Implementation approach**: constrained edit policy with must-pass validations.
- **How to test**: regression test snapshots and semantic diff checks.
- **Failure modes**: broad-scope edits, hidden behavior shifts.

#### 12) Uncertainty detection and confidence calibration
- **What it does**: signals when evidence is weak or conflicts exist.
- **Required support**: confidence model and uncertainty tags in events.
- **Where it fits**: validator outputs + frontend status surfaces.
- **Implementation approach**: confidence derived from evidence density, retrieval quality, verification depth.
- **How to test**: ambiguous fixtures should trigger low-confidence/approval-required outcomes.
- **Failure modes**: false confidence, over-cautious paralysis.

#### 13) Episodic memory capture
- **What it does**: stores durable summaries of what happened and why.
- **Required support**: run artifact persistence and retention policy.
- **Where it fits**: run completion and post-mortem stage.
- **Implementation approach**: append run summary, touched paths, residual risks.
- **How to test**: run replay tests validating artifact completeness.
- **Failure modes**: verbose noise dumps, poor summarization quality.

#### 14) Skill extraction and pattern reuse
- **What it does**: converts repeated successful tactics into reusable skills.
- **Required support**: pattern miner + skill registry update workflow.
- **Where it fits**: learning loop and `.github/skills/` governance.
- **Implementation approach**: mine successful task traces for recurring tool/step patterns.
- **How to test**: precision/recall checks on extracted candidate skills.
- **Failure modes**: overgeneralization, stale skills, policy drift.

#### 15) Feedback capture and preference learning
- **What it does**: learns operator preferences on risk, verbosity, and control points.
- **Required support**: feedback event schema and preference store.
- **Where it fits**: frontend approval UI + backend learning loop.
- **Implementation approach**: explicit feedback objects linked to run/task IDs.
- **How to test**: A/B replay where preference inputs alter routing appropriately.
- **Failure modes**: preference conflict, hidden bias accumulation.

#### 16) Post-task analysis and improvement loop
- **What it does**: turns completed runs into backlog improvements.
- **Required support**: analyzers over artifacts and failure clusters.
- **Where it fits**: learning phase after DONE/FAILED states.
- **Implementation approach**: periodic analysis job emits actionable improvements and confidence.
- **How to test**: seeded run artifacts should generate expected improvement recommendations.
- **Failure modes**: analysis noise, no prioritization, recommendation fatigue.

---

## 5) Next-Generation Architecture Proposal

### 5.1 Target architecture (ASCII)

```text
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND CONTROL SURFACE                     │
│  Task Queue │ Plan Viewer │ Memory Browser │ Trace / Audit Log │
│  Approve/Deny │ Diff Review │ Error Surface │ Agent Status      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ SSE / WebSocket (typed events)
┌─────────────────────────▼───────────────────────────────────────┐
│                    BACKEND ORCHESTRATION LAYER                  │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐    │
│  │  Planner │→ │ Executor │→ │ Validator │→ │   Learning    │    │
│  │  (DAG)   │  │ (Steps)  │  │ (Critique)│  │    Loop       │    │
│  └──────────┘  └──────────┘  └───────────┘  └──────────────┘    │
│         ↕              ↕             ↕                            │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │                     MEMORY LAYER                         │     │
│  │ Short-term (context packet) │ Long-term (vector store)  │     │
│  │ Episodic (run artifacts)    │ Semantic (skill registry) │     │
│  └──────────────────────────────────────────────────────────┘     │
│         ↕              ↕             ↕                            │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │                      TOOL ROUTER                         │     │
│  │ MCP tools │ GitHub API │ Filesystem │ Web Search │ ...  │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │                   OBSERVABILITY LAYER                    │     │
│  │ Structured logs │ Trace IDs │ Event history │ Metrics    │     │
│  └──────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Component boundaries, data model, integration, and failure modes

#### A) Frontend control surface
- **Responsibility**: operator visibility and intervention; never executes agent logic.
- **Data model**: consumes typed `AgentEvent` stream derived from context packet/run artifact states.
- **Connects to existing architecture**: reads orchestration phases equivalent to `workflow-manifest.json` phase order.
- **Python notes**: backend emits event envelope with trace IDs and task/run IDs.
- **React notes**: route-level pages + hooks for subscriptions and normalized caches.
- **Failure modes**: stale subscriptions, event ordering races, over-noisy UI. **Mitigation**: sequence numbers, reconnection replay, progressive disclosure.

#### B) Planner (DAG)
- **Responsibility**: produce immutable plan graph and step contracts.
- **Data model**: aligns to context packet `task_graph` and `current_step` semantics.
- **Integration**: invoked by orchestrator classify/breadth/depth phases.
- **Python notes**: deterministic planning function with structured output.
- **React notes**: render DAG and contract metadata in Plan Viewer.
- **Failure modes**: cyclic plans, ambiguous contracts. **Mitigation**: schema validation + cycle checks + contract linting.

#### C) Executor (step runner)
- **Responsibility**: execute approved plan steps; no autonomous replanning unless explicit revision event.
- **Data model**: `PlanStepExecutionRecord` with status, tool calls, outputs, errors.
- **Integration**: reads plan snapshot and updates run artifact ledger.
- **Python notes**: strict module boundary, dependency injection for tool router.
- **React notes**: step-level progress timeline and action logs.
- **Failure modes**: side-effect duplication, partial completion. **Mitigation**: idempotency keys and checkpoint writes.

#### D) Validator (critique)
- **Responsibility**: evaluate outcomes against requirements, safety, and evidence quality.
- **Data model**: `EvaluationResult` with severity, confidence, unresolved risks.
- **Integration**: maps to adversarial critique/revise phases.
- **Python notes**: rule-based + model-assisted checks with bounded rounds.
- **React notes**: error surface and risk panel.
- **Failure modes**: overly strict blocking or weak checks. **Mitigation**: severity policy + calibration tests.

#### E) Learning loop
- **Responsibility**: extract recurring improvements from artifacts and feedback.
- **Data model**: `LearningSuggestion`, `SkillCandidate`, `PreferenceUpdate`.
- **Integration**: writes recommendations to spec/research backlog, not directly to runtime policy.
- **Python notes**: batch job analyzing run artifact corpus.
- **React notes**: "improvement queue" view with approve/defer controls.
- **Failure modes**: noisy recommendations. **Mitigation**: minimum evidence thresholds and human approval gates.

#### F) Memory layer
- **Responsibility**: manage short-term, episodic, long-term, and semantic memory with provenance.
- **Data model**: current packet schema v2 + run artifact schema v1 + vector index metadata.
- **Integration**: context hydration policy follows `workflow-manifest.json` memory scopes.
- **Python notes**: memory service API with retrieval and write policy.
- **React notes**: Memory Browser with scope filters and provenance links.
- **Failure modes**: stale memory contamination, privacy leakage. **Mitigation**: TTLs, scope ACLs, provenance requirement.

#### G) Tool router
- **Responsibility**: enforce capability policy, tool selection, retries/timeouts.
- **Data model**: `ToolCall` and `ToolPolicyDecision` records.
- **Integration**: capability lists in manifest become runtime policy checks.
- **Python notes**: wrapper around MCP/GitHub/filesystem/web tools.
- **React notes**: ToolCallLog with policy decision details.
- **Failure modes**: unsafe route escalation, timeout cascades. **Mitigation**: deny-by-default for privileged calls; exponential backoff and circuit-breakers.

#### H) Observability layer
- **Responsibility**: make every transition and tool call traceable.
- **Data model**: structured JSON logs and event history snapshots.
- **Integration**: mirrors task ledger metrics already described in workflow manifest.
- **Python notes**: logger adapters injecting `trace_id`, `run_id`, `task_id`, `step_id`.
- **React notes**: TraceTimeline and filtered event stream.
- **Failure modes**: cardinality blowups, missing correlation. **Mitigation**: schema-governed logging and bounded labels.

### 5.3 Major runtime flow

```text
User Request
   ↓
Orchestrator (single-entry)
   ↓ classify + risk score
Planner -> PlanGraph(vN)
   ↓
Executor -> Tool Router -> Tools
   ↓                    ↑ policy decisions
Validator (quality + safety + evidence)
   ↓
if pass -> DONE + RunArtifact snapshot
if fail -> revise plan or escalate for approval
   ↓
Learning Loop (offline/batch) -> skill candidates + policy proposals
```

---

## 6) Frontend Architecture for Agentic Observability

### 6.1 Page inventory

1. **`/tasks` (Task Queue)**
   - Purpose: queue of active/completed tasks, filter by state/risk/owner.
   - Data: `AgentTask[]`, aggregate metrics, last event timestamps.
2. **`/tasks/:taskId/plan` (Plan Viewer)**
   - Purpose: DAG view, current step, dependencies, contracts.
   - Data: `PlanStep[]`, step statuses, revision history.
3. **`/tasks/:taskId/memory` (Memory Browser)**
   - Purpose: inspect short-term, episodic, and semantic entries with provenance.
   - Data: `MemoryEntry[]`, source refs, TTL metadata.
4. **`/tasks/:taskId/tools` (Tool Call Log)**
   - Purpose: list tool calls, durations, retries, policy outcomes.
   - Data: `ToolCall[]`, error taxonomy.
5. **`/tasks/:taskId/diff` (Diff Reviewer)**
   - Purpose: human-in-the-loop review before write actions.
   - Data: diff hunks, risk tags, affected paths.
6. **`/tasks/:taskId/approvals` (Approval Panel)**
   - Purpose: approve/deny/pause/resume/cancel risky operations.
   - Data: pending approvals, rationale, confidence, policy reason.
7. **`/tasks/:taskId/trace` (Trace Timeline)**
   - Purpose: chronological event trace with correlated logs.
   - Data: event stream entries, trace IDs, severity levels.
8. **`/artifacts/:runId` (Run Artifact Viewer)**
   - Purpose: post-task summary and residual risk analysis.
   - Data: `RunArtifact`, verification results, learning suggestions.

### 6.2 Real-time data strategy

- **Default**: **SSE** for one-way server→UI event feed (simple, proxy-friendly, easy resume with `Last-Event-ID`).
- **Use WebSocket only when** bi-directional low-latency control is needed (e.g., live collaborative approvals).
- **Polling fallback**: every 5–15s for environments where stream channels are blocked.

Tradeoff summary:
- SSE: simpler and robust for event timelines.
- WebSocket: flexible but heavier lifecycle management.
- Polling: universal fallback but delayed and wasteful under load.

### 6.3 State model

- **Runtime state (server truth)**: tasks, plans, events, artifacts.
- **Presentation state (client-only)**: selected filters, expanded nodes, panel layout, local sorting.
- Use normalized cache keyed by `taskId`, `runId`, and `eventSeq`.
- Never let UI local state mutate runtime truth directly; all mutations are command API calls.

### 6.4 Key components

- `TaskCard`
- `PlanViewer`
- `MemoryBrowser`
- `ToolCallLog`
- `DiffReviewer`
- `ApprovalPanel`
- `TraceTimeline`

### 6.5 Typed data contracts (TypeScript)

```ts
export type TaskState =
  | "PENDING"
  | "PLANNING"
  | "EXECUTING"
  | "VALIDATING"
  | "LEARNING"
  | "DONE"
  | "FAILED"
  | "CANCELLED";

export interface AgentTask {
  id: string;
  objective: string;
  state: TaskState;
  riskLevel: "low" | "medium" | "high";
  createdAtUtc: string;
  updatedAtUtc: string;
  currentStepId?: string;
  traceId: string;
}

export interface PlanStep {
  id: string;
  title: string;
  dependsOn: string[];
  inputContract: string;
  outputContract: string;
  doneCondition: string;
  status: "pending" | "in_progress" | "done" | "failed" | "blocked";
}

export interface ToolCall {
  id: string;
  taskId: string;
  stepId: string;
  toolName: string;
  startedAtUtc: string;
  endedAtUtc?: string;
  status: "success" | "error" | "timeout" | "denied";
  retryCount: number;
  policyDecision: "allow" | "deny" | "require_approval";
  errorCode?: string;
}

export interface MemoryEntry {
  id: string;
  scope: "working" | "episodic" | "semantic" | "long_term";
  summary: string;
  source: string;
  confidence: number;
  createdAtUtc: string;
  expiresAtUtc?: string;
  evidenceRefs: string[];
}

export interface EvaluationResult {
  taskId: string;
  status: "pass" | "fail" | "needs_review";
  confidence: number;
  findings: Array<{
    severity: "low" | "medium" | "high" | "critical";
    summary: string;
    evidence: string[];
    remediation?: string;
  }>;
  evaluatedAtUtc: string;
}

export interface RunArtifact {
  runId: string;
  taskClass: string;
  objective: string;
  status: "in-progress" | "blocked" | "review-needed" | "done";
  summary: string;
  touchedPaths: string[];
  verification: Array<{
    kind: string;
    status: "passed" | "failed" | "not-run" | "advisory";
    details: string;
  }>;
  residualRisks: string[];
}
```

### 6.6 Progressive disclosure pattern

- **Default card view**: objective, state, risk, current step.
- **One click deeper**: plan and recent tool calls.
- **Two clicks deeper**: full event payloads, raw tool arguments, memory provenance.
- **Power-user mode**: full trace and artifact JSON export.

This keeps noise low for operators while preserving forensic depth for incidents.

### 6.7 Error surface design

Errors must include:
- what failed,
- where it failed (step/tool/path),
- why it failed (classified cause),
- what happens next (retry/escalate/abort),
- what action operator can take now.

Avoid passive red banners. Every error card should include actionable controls.

### 6.8 UX anti-patterns to avoid

- Streaming raw internal thought text as primary UI.
- Mixing approval actions inside noisy log timelines.
- Hiding policy denials as generic "tool failed" events.
- Presenting confidence without evidence links.
- Forcing full-page refresh for event updates.

---

## 7) Backend Architecture for Robustness

### 7.1 Task state machine

States:
- `PENDING`
- `PLANNING`
- `EXECUTING`
- `VALIDATING`
- `LEARNING`
- `DONE`
- `FAILED`
- `CANCELLED`

Allowed transitions:

```text
PENDING -> PLANNING
PLANNING -> EXECUTING | FAILED | CANCELLED
EXECUTING -> VALIDATING | FAILED | CANCELLED
VALIDATING -> LEARNING | EXECUTING (revision loop) | FAILED | CANCELLED
LEARNING -> DONE | FAILED
FAILED -> (terminal)
DONE -> (terminal)
CANCELLED -> (terminal)
```

Invariants:
- Terminal states are immutable.
- Every transition must emit event + trace metadata.
- `EXECUTING` requires a frozen plan revision ID.
- `VALIDATING -> EXECUTING` requires explicit revision reason.

### 7.2 Execution model (module boundaries)

Proposed Python package structure:

```text
src/agent_runtime/
  planner.py
  executor.py
  validator.py
  learning.py
  state_machine.py
  tool_router.py
  memory_service.py
  events.py
  schemas.py
```

Interface boundary:
- Planner returns `Plan` only.
- Executor consumes `Plan` and returns `ExecutionReport`.
- Validator consumes report + constraints and returns `EvaluationResult`.
- Learning consumes run artifacts asynchronously.

### 7.3 Data schemas (Pydantic)

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class TaskState(str, Enum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    LEARNING = "LEARNING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ToolCallStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    DENIED = "denied"


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    title: str
    depends_on: list[str] = Field(default_factory=list)
    input_contract: str
    output_contract: str
    done_condition: str


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    task_id: str
    revision: int = 1
    steps: list[PlanStep]


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    call_id: str
    task_id: str
    step_id: str
    tool_name: str
    status: ToolCallStatus
    started_at: datetime
    ended_at: datetime | None = None
    retry_count: int = 0
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_id: str
    scope: str
    summary: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime


class EvaluationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    remediation: str | None = None


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    status: str
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[EvaluationFinding] = Field(default_factory=list)
    evaluated_at: datetime


class RunArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    run_id: str
    task_class: str
    objective: str
    status: str
    summary: str
    touched_paths: list[str] = Field(default_factory=list)
    verification: list[dict[str, str]] = Field(default_factory=list)
    residual_risks: list[str] = Field(default_factory=list)


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    objective: str
    state: TaskState = TaskState.PENDING
    plan: Plan | None = None
    trace_id: str
    created_at: datetime
    updated_at: datetime
```

### 7.4 Tool execution wrapper

Required behaviors:
- rate limit per tool family,
- timeout defaults with override policy,
- retry only for transient classes,
- permission gating by action sensitivity,
- structured logging for every call.

Wrapper contract:
- input: `ToolInvocationRequest`
- output: `ToolInvocationResult`
- side channel: emits `tool.call.started`, `tool.call.finished`, `tool.call.failed` events.

### 7.5 Idempotency strategy

- Every task has `task_id` and mutable `revision`.
- Every step execution has idempotency key: `task_id:plan_revision:step_id:attempt_group`.
- Side-effecting tools require idempotency token propagation.
- On retry, wrapper checks prior terminal outcomes before re-execution.

### 7.6 Observability

- Structured JSON logging only.
- Correlation fields: `trace_id`, `run_id`, `task_id`, `step_id`, `tool_call_id`.
- Event history persisted for replay and UI timeline rendering.
- Run artifact snapshots after every major phase transition.

### 7.7 Testability

- Planner, executor, validator interfaces are dependency-injected and mockable.
- Deterministic fixtures for plan generation and retry semantics.
- Regression harness replays historical run artifacts against new validators.
- Tool router integration tests using fake tool adapters.

### 7.8 Queue/event model

- **Start simple**: in-process queue + durable DB table/event log if throughput is modest.
- **Upgrade to external queue** (Temporal/Celery/RQ/Kafka) only when:
  - task concurrency and durations exceed process limits,
  - restart safety becomes critical,
  - SLOs require worker autoscaling.
- **Avoid over-engineering early**: distributed queue complexity before stable task contracts will slow velocity.

---

## 8) Technical Critique of the Proposed Architecture

### Strengths

- Builds on existing governance architecture rather than replacing it.
- Enforces planner/executor/validator boundaries that improve reliability and testing.
- Makes context packet and run artifact central runtime contracts.
- Introduces operator-grade observability and intervention surfaces.
- Adds a learning loop with explicit human approval for policy changes.

### Weaknesses

- Adds conceptual overhead: more modules, more schemas, more transitions.
- Requires disciplined schema versioning to avoid drift.
- Frontend control surface can become noisy if event taxonomy is weak.
- Memory system quality is highly sensitive to data hygiene and invalidation.

### Scale bottlenecks

- Tool-router throughput under high-concurrency multi-step tasks.
- Retrieval latency if semantic memory is not indexed incrementally.
- Validation phase runtime if critique loops are unconstrained.
- Event-stream fanout and storage cardinality in trace-heavy environments.

### Maintenance risks

- Policy drift between `.github/agent-platform/` metadata and runtime implementation.
- Spec drift if implementation bypasses active specs.
- Adapter sprawl when integrating too many external frameworks at once.
- "Feature excitement" pushing multi-agent complexity before reliability fundamentals.

### Intentionally left out (for now)

- Fully autonomous unsupervised code write/merge pipelines.
- End-to-end reinforcement learning in production execution loop.
- Massive distributed memory graph without clear retention and governance policy.
- Complex multi-agent societies with open-ended interaction.

Reason: these are high-cost, high-risk, and low-leverage before deterministic execution, observability, and evaluation are hardened.

---

## 9) Practical Prioritization

### Tier 1 — Immediate Wins (current scaffold, low risk, high leverage)

1. **Define runtime schemas in code**
   - Touch: create `src/agent_runtime/schemas.py`
   - Benefit: typed contracts and reduced ambiguity.
2. **Add task state machine module**
   - Touch: `src/agent_runtime/state_machine.py`
   - Benefit: explicit transitions and invariants.
3. **Create tool router wrapper with policy hooks**
   - Touch: `src/agent_runtime/tool_router.py`
   - Benefit: safer tool execution and better logs.
4. **Add event envelope schema**
   - Touch: `src/agent_runtime/events.py`
   - Benefit: frontend/backend contract stability.
5. **Draft control-surface API spec in docs**
   - Touch: `docs/architecture.md` and new `docs/agent-runtime-api.md`
   - Benefit: clear implementation target.
6. **Add run artifact persistence helper**
   - Touch: `src/agent_runtime/artifacts.py`
   - Benefit: consistent episodic memory capture.
7. **Add unit tests for transition invariants**
   - Touch: `tests/test_state_machine.py`
   - Benefit: prevents invalid task lifecycle bugs.
8. **Add baseline observability utilities**
   - Touch: `src/agent_runtime/observability.py`
   - Benefit: trace correlation from day one.

### Tier 2 — Medium-Term Upgrades (1–3 months)

1. **Implement planner/executor/validator modules**
   - Dependency: Tier 1 schemas + state machine.
   - Benefit: modular runtime engine.
2. **Build semantic mapper + retrieval adapter**
   - Dependency: memory service contract.
   - Benefit: grounded reasoning quality.
3. **Add React control pages and hooks**
   - Dependency: typed event/API contracts.
   - Benefit: operator trust and controllability.
4. **Introduce bounded adversarial validation mode**
   - Dependency: validator framework.
   - Benefit: catches high-risk blind spots.
5. **Implement approval workflow API and UI**
   - Dependency: event and command contracts.
   - Benefit: safe human-in-the-loop control.
6. **Regression harness for run artifact replay**
   - Dependency: artifact persistence.
   - Benefit: stable iteration and confidence.

### Tier 3 — Long-Term Infrastructure Investments

1. **Durable distributed execution engine (Temporal or equivalent)**
   - Unlocks: high-reliability long-running workflows and replay safety.
   - Prerequisites: stable plan/task/event contracts.
   - Risk if early: heavy ops burden and slowed delivery.
2. **Offline optimization pipeline (DSPy-like)**
   - Unlocks: measurable improvement in routing/prompt quality.
   - Prerequisites: evaluation datasets and stable metrics.
   - Risk if early: overfitting and false confidence.
3. **Advanced memory lifecycle platform**
   - Unlocks: long-horizon adaptation and skill compounding.
   - Prerequisites: provenance, TTL, privacy policy, storage governance.
   - Risk if early: memory bloat and contamination.
4. **Selective multi-agent protocol integration**
   - Unlocks: better performance on high-uncertainty or cross-domain tasks.
   - Prerequisites: strict arbitration and bounded loops.
   - Risk if early: complexity explosion and debugging pain.

---

## 10) Implementation Checklist (Ordered by Dependency and Leverage)

1. Create `src/agent_runtime/__init__.py`.
2. Create `src/agent_runtime/schemas.py` with Pydantic task/plan/tool/evaluation models.
3. Create `src/agent_runtime/state_machine.py` with valid transition map.
4. Add `tests/test_state_machine.py` for allowed/forbidden transitions.
5. Create `src/agent_runtime/events.py` for typed event envelope.
6. Add `tests/test_events_schema.py` for serialization and required fields.
7. Create `src/agent_runtime/tool_router.py` with policy decision outcomes.
8. Add `tests/test_tool_router_policy.py` for allow/deny/approval branches.
9. Create `src/agent_runtime/observability.py` for structured logger helpers.
10. Add `tests/test_observability_fields.py` for trace field presence.
11. Create `src/agent_runtime/planner.py` interface and basic implementation.
12. Add `tests/test_planner_dag_constraints.py` for cycle detection.
13. Create `src/agent_runtime/executor.py` interface and step runner skeleton.
14. Add `tests/test_executor_idempotency.py` for repeat-safe behavior.
15. Create `src/agent_runtime/validator.py` with critique result schema.
16. Add `tests/test_validator_findings.py` for severity and confidence handling.
17. Create `src/agent_runtime/learning.py` with artifact analyzer scaffold.
18. Add `tests/test_learning_suggestions.py` for thresholding behavior.
19. Create `src/agent_runtime/memory_service.py` for scoped retrieval/write APIs.
20. Add `tests/test_memory_scopes.py` for repo/session/user access rules.
21. Create `src/agent_runtime/artifacts.py` for run artifact persistence.
22. Add `tests/test_artifact_persistence.py` for schema compliance with `.github/agent-platform/run-artifact-schema.json`.
23. Add backend route module `src/agent_runtime/routes.py` for task/event endpoints.
24. Add `tests/test_routes_task_lifecycle.py` for state-machine-backed endpoint behavior.
25. Create frontend API client `frontend/src/api/agentRuntime.ts`.
26. Create frontend types `frontend/src/types/agentRuntime.ts` aligned to backend schemas.
27. Create hooks `frontend/src/hooks/useTaskStream.ts` and `useTaskCommands.ts`.
28. Create page `frontend/src/pages/AgentControlCenter.tsx` with queue and status summary.
29. Create components under `frontend/src/components/agent/` (`TaskCard`, `PlanViewer`, `TraceTimeline`, `ApprovalPanel`).
30. Update `docs/architecture.md` and add ADR in `docs/architecture/decisions/` for runtime architecture and durability roadmap.

---

## North Star

When fully realized, this repository becomes a **production-minded engineering intelligence layer**: a single-entry orchestrator with deterministic planning and execution, policy-governed tool use, typed memory and artifact contracts, adversarial validation loops, and an operator-grade React control surface that makes every decision inspectable, interruptible, and improvable. The system’s intelligence comes not from agent theatrics, but from disciplined state management, evidence-backed reasoning, resilient execution semantics, and compounding learning cycles that continuously raise quality without sacrificing safety or maintainability.
