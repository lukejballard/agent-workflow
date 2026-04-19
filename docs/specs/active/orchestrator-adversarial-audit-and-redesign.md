# Orchestrator Adversarial Audit & Redesign

**Status:** Active  
**Classification:** architecture-change  
**Date:** 2026-04-18  

---

# PHASE 1 — FULL-SYSTEM ADVERSARIAL AUDIT

## 1.1 Core Architecture

### ISSUE-01: `task_graph` Is Optional in Context Packet Schema — DAG Planning Is Unenforced

1. **What is broken:** The `task_graph` field in [context-packet.schema.json](.github/agent-platform/context-packet.schema.json#L10) is _not_ in the `required` array (line 10-21). The schema requires `current_step` but the full DAG is optional. This means the orchestrator can legally produce a context packet with no task decomposition whatsoever.
2. **Why it matters:** Without a required task graph, there is no structural guarantee that the LLM actually planned before executing. The "atomic subtask routing" described in the orchestrator is pure prompt theater — the schema permits skipping it entirely.
3. **Evidence:** `context-packet.schema.json` `required` array omits `task_graph`. The `workflow-manifest.json` `subtaskExecution.requireAtomicContracts: true` is a prompt-level instruction with zero schema enforcement.
4. **Real-world failure mode:** Agent receives a complex brownfield task, skips decomposition, tunnels into one file, breaks adjacent modules. No structural gate catches this.
5. **Concrete fix:** Move `task_graph` into `required` in the schema. Add a validation rule in `sync_agent_platform.py` that rejects example packets with an empty or missing `task_graph` for non-trivial classifications. For trivial tasks, allow an explicit `"task_graph": []`.
6. **Priority:** HIGH
7. **Confidence:** 95% — the schema is unambiguous.

### ISSUE-02: No State Machine — Phase Transitions Are LLM Honor System

1. **What is broken:** The 10-phase workflow (`goal-anchor → classify → breadth-scan → ... → traceability-and-verify`) defined in `workflow-manifest.json` at `workflow.phaseOrder` has **zero runtime enforcement**. There is no state machine, no phase-transition validator, and no gate between phases. The orchestrator agent markdown describes phases in natural language, but nothing prevents the LLM from jumping from `classify` directly to `execute-or-answer`, skipping planning and critique entirely.
2. **Why it matters:** This is the single most critical architectural weakness. Without a state machine, the entire workflow is a suggestion, not an enforcement. LangGraph-style `StateGraph` exists precisely to solve this.
3. **Evidence:** [orchestrator.agent.md](.github/agents/orchestrator.agent.md) describes phases 1-9 as markdown sections. No code validates transitions. `workflow-manifest.json` `phaseOrder` is a static array with no associated transition logic.
4. **Real-world failure mode:** Under token pressure or ambiguous tasks, the LLM skips critique, ships buggy code directly. This _will_ happen regularly — it is the dominant LLM failure mode for long-horizon tasks.
5. **Concrete fix:** Implement a `StateGraph` (LangGraph pattern) where each phase is a node with explicit allowed transitions. Encode phase gates (e.g., "spec must exist before entering `execute-or-answer` for non-trivial tasks") as conditional edges. Runtime state tracks the current phase and rejects out-of-order transitions. Minimum viable: extend `context-packet.schema.json` with a `"current_phase"` enum field that `sync_agent_platform.py` validates against `phaseOrder`, and add a CI check that example packets have valid phase transitions.
6. **Priority:** HIGH
7. **Confidence:** 98%

### ISSUE-03: Single-Agent Monolith With No Role Isolation

1. **What is broken:** Despite having 7 specialist agents (analyst, planner, implementer, qa, reviewer, cleanup, researcher), the orchestrator.agent.md says "Use the specialist agents as internal reference patterns, not as the default workflow." In practice, ALL work runs through one LLM call chain with no role isolation. The planner, executor, and critic are the same LLM in the same context window.
2. **Why it matters:** Without role separation, there is no adversarial pressure. The LLM reviews its own work with the same biases that produced it. AutoGen-style multi-agent patterns exist precisely to create independent critic/verifier roles.
3. **Evidence:** `orchestrator.agent.md` line ~197: "Use the specialist agents as internal reference patterns." The subagent system exists (the VS Code `runSubagent` tool can invoke `analyst`, `qa`, `reviewer`, etc.) but the orchestrator never requires it.
4. **Real-world failure mode:** LLM generates code in Phase 8, "critiques" it in Phase 6 (out of order), finds no issues because it has anchoring bias toward its own output. Ships broken code with a false "PASS" critique.
5. **Concrete fix:** For medium/high-risk tasks, make a hard requirement that the critique phase invokes the `reviewer` agent as a subagent (different context window). The reviewer's output must be structured (`PASS`/`REJECT` per its own spec) and the orchestrator must not proceed past critique if the reviewer returns `REJECT`. This is achievable today with `runSubagent`.
6. **Priority:** HIGH
7. **Confidence:** 90%

---

## 1.2 Enforcement & Runtime Guarantees

### ISSUE-04: Token Limits Are Prompt Suggestions, Not Runtime Enforcement

1. **What is broken:** `workflow-manifest.json` defines `contextEngineering.healthGate.maxContextUtilizationPct: 70` and `subtaskExecution.maxLlmCallsPerSubtask: 1`. These are prompt-facing metadata. No runtime system counts tokens or limits LLM calls. The `context_health.current_utilization_pct` field in the schema is self-reported by the LLM.
2. **Why it matters:** The LLM cannot accurately count its own tokens. tiktoken provides real token counts. Without real counting, the 70% budget gate is fiction.
3. **Evidence:** No `tiktoken` import or usage anywhere in the codebase. `context_health.current_utilization_pct` is a number field the LLM fills in — it is fabricated.
4. **Real-world failure mode:** LLM reports `46%` utilization (as in `context-packet.example.json`) when it is actually at 85%. Subsequent tool output silently truncates. Quality degrades without any signal.
5. **Concrete fix:** Integrate `tiktoken` into a lightweight Python helper that agents call before each major step. The helper counts real tokens in the context window and returns actual utilization. Wire this into `pretool_approval_policy.py` as a gate: if context exceeds 80%, emit an `"ask"` decision forcing trim before proceeding. Cost: ~50 lines of Python.
6. **Priority:** HIGH
7. **Confidence:** 95%

### ISSUE-05: Schema Validation Only Runs on Example Files, Not Live Packets

1. **What is broken:** `sync_agent_platform.py` validates only the example JSON files under `.github/agent-platform/examples/`. There is no mechanism to validate context packets or run artifacts that the LLM actually produces during a live session.
2. **Why it matters:** The validation infrastructure exists but applies only to static fixtures. Every live agent execution produces unvalidated packets. Drift between schema and runtime behavior is invisible.
3. **Evidence:** `sync_agent_platform.py` `validate_run_artifact_instance()` is called only for files matching `examples/*.json`. No hook or middleware validates live output.
4. **Real-world failure mode:** The LLM produces a context packet missing `self_check` or with an invalid `context_health.status` value. Nothing catches it. The "typed contract" is typed on paper only.
5. **Concrete fix:** Add a `validate_context_packet_instance()` function to `sync_agent_platform.py`. Wire it into `pretool_approval_policy.py` as a post-tool hook or add a `PostToolUse` hook that spot-checks structured output blocks in LLM responses. At minimum, add a `--validate-packet` CLI flag that CI scripts or manual invocations can use.
6. **Priority:** MEDIUM
7. **Confidence:** 85%

### ISSUE-06: Scratchpad Isolation Is Unenforced

1. **What is broken:** `workflow-manifest.json` says `subtaskExecution.scratchpadScope: "current-subtask-only"` and the orchestrator says "Local scratchpads are replaced between subtasks." This is a prompt instruction to the LLM. Nothing actually clears or isolates the scratchpad.
2. **Why it matters:** If the LLM accumulates stale scratchpad content across subtasks within a conversation, context pollution and hallucination risk increase.
3. **Evidence:** `scratchpad` in the context packet schema is `"type": "array", "items": {"type": "string"}` with no cardinality limit or freshness constraint.
4. **Real-world failure mode:** Agent carries notes from subtask 1 into subtask 5. Old notes contain outdated assumptions. Agent makes decisions based on stale evidence.
5. **Concrete fix:** Add `maxItems: 10` to the scratchpad schema. Add a `subtask_id` association so validation can detect stale entries. In the prompt, enforce a structural pattern: scratchpad must be cleared at the start of each new `current_step`.
6. **Priority:** MEDIUM
7. **Confidence:** 80%

---

## 1.3 Context & Memory

### ISSUE-07: Memory System Is Prompt-Described, Not Implemented

1. **What is broken:** The `semantic_memory` section in the context packet schema references `scopes: ["repo", "session", "user"]` and a `retrieval_policy`. The actual infrastructure is the VS Code `memory` tool (file-based notes in `/memories/`). There is no vector database, no embedding pipeline, no real semantic retrieval. The "semantic memory" is a flat directory of markdown files.
2. **Why it matters:** The system describes a three-tier memory hierarchy (working/episodic/semantic) that would require something like Chroma or Qdrant to implement properly. The current implementation is plain file reads with no ranking, no relevance scoring, no deduplication.
3. **Evidence:** `.vscode/mcp.json` contains only a `fetch` server. No Chroma, Qdrant, or embedding service is configured. The `loaded_memories` field in examples shows a single `/memories/repo/` file with a hand-written summary.
4. **Real-world failure mode:** On task #50 in a project, the agent has no way to retrieve relevant past failures or solutions. It redoes work, repeats mistakes, and cannot learn.
5. **Concrete fix:** Phase 4 item. Integrate Chroma (lightweight, local, Python-native) as an MCP server or direct integration. Index: completed run artifacts, failure postmortems, spec-to-code mappings. Query: on each new task, embed the goal and retrieve top-K relevant past artifacts. Cost: ~200 lines + dependency.
6. **Priority:** MEDIUM
7. **Confidence:** 90%

### ISSUE-08: Front-Loaded Context Strategy Risks Budget Overrun

1. **What is broken:** The orchestrator's "Before doing anything" section requires reading 10 files before processing the request: `AGENTS.md`, `copilot-instructions.md`, `workflow-manifest.json`, `repo-map.json`, `skill-registry.json`, active specs, requirement sources, relevant instructions, scoped AGENTS.md, and skill checklists. For a simple task, this front-loads thousands of tokens of context before the LLM even considers the user request.
2. **Why it matters:** Context window budget is finite. Front-loading 10+ files for a trivial fix wastes tokens that could be used for the actual task.
3. **Evidence:** `orchestrator.agent.md` lines 25-40 list the mandatory pre-reads. `workflow-manifest.json` alone is ~500 lines (≈2000 tokens).
4. **Real-world failure mode:** User asks "fix this typo in README.md." Agent reads 10 governance files, consuming 8000+ tokens, then has less budget for the actual fix. On smaller context models, this causes quality degradation.
5. **Concrete fix:** Implement progressive context loading. Phase 1 (classify) reads only `AGENTS.md` and `workflow-manifest.json`. Phase 2 and beyond loads files relevant to the classified surface. The repo-map's `changeRouting` section already encodes this: use it as the progressive loading guide instead of front-loading everything.
6. **Priority:** MEDIUM
7. **Confidence:** 85%

---

## 1.4 Tooling & Execution

### ISSUE-09: Verification Routes Are Empty Arrays for Backend and Frontend

1. **What is broken:** In [repo-map.json](.github/agent-platform/repo-map.json), `verificationRoutes.backend` and `verificationRoutes.frontend` are both empty arrays (`[]`). The `changeRouting` entries for `src/**` and `frontend/**` have empty `verifyWith` arrays. This means the canonical metadata tells the agent: "there are no verification commands to run for code changes."
2. **Why it matters:** The orchestrator reads `repo-map.json` for verification guidance. Empty arrays mean it will skip verification. No `ruff`, `mypy`, `tsc`, `pytest`, `vitest`, no build check. The verify-narrow.sh and verify-broad.sh scripts exist but are not referenced in the routing metadata.
3. **Evidence:** `repo-map.json` lines: `"verificationRoutes": { "backend": [], "frontend": [], "contracts": [] }`. `sync_agent_platform.py` generates these dynamically from filesystem presence, but since `tests/unit/` and `frontend/package.json` don't exist yet, they produce empty arrays.
4. **Real-world failure mode:** Agent generates Python code with syntax errors or TypeScript code that doesn't compile. No verification is triggered. The change is marked "done" with broken code.
5. **Concrete fix:** Two-part: (1) Add static fallback verification routes to `repo-map.json` that are always present regardless of filesystem state: `"ruff check src/"` for Python, `"cd frontend && npm run lint && npm run build"` for frontend. (2) When application code is eventually added, `sync_agent_platform.py` will upgrade these with the dynamic routes.
6. **Priority:** HIGH
7. **Confidence:** 95%

### ISSUE-10: No AST/Static Analysis Integration

1. **What is broken:** No Tree-sitter, Semgrep, or equivalent AST-based analysis is referenced anywhere in the system. Code review and critique rely entirely on LLM judgment.
2. **Why it matters:** LLMs are poor at detecting certain code patterns (e.g., SQL injection via string concatenation, unsafe `eval()`, missing null checks). Static analysis tools catch these deterministically.
3. **Evidence:** No `semgrep` or `tree-sitter` in any config, script, workflow, or instruction file.
4. **Real-world failure mode:** Agent generates code with a security vulnerability (e.g., `f"SELECT * FROM users WHERE id = {user_id}"`). The adversarial review skill is LLM-based and may miss it. Semgrep would catch it deterministically.
5. **Concrete fix:** Add `semgrep` with a curated rule set (OWASP top 10 minimum) to the `verify-narrow.sh` pipeline. Add a Semgrep CI step to `ci.yml`. Reference: https://semgrep.dev/ — lightweight, no build system dependency.
6. **Priority:** MEDIUM
7. **Confidence:** 90%

### ISSUE-11: PreTool Hook Cannot Enforce Complex Policies

1. **What is broken:** `pretool_approval_policy.py` is a well-implemented gate for destructive/remote commands. However, it can only `deny`, `ask`, or `continue`. It cannot: inject context, modify tool parameters, enforce sequencing (e.g., "run tests before committing"), or validate LLM output structure.
2. **Why it matters:** The hook is the only real enforcement point in the system. Its limited vocabulary means many governance rules (e.g., "spec must exist before coding") are unenforced.
3. **Evidence:** `pretool_approval_policy.py` emits `permissionDecision: "deny" | "ask"` or `continue: true`. No `additionalContext` injection for constraints like "verify tests passed."
4. **Real-world failure mode:** Agent edits `src/` files without having read the spec. The hook permits the edit because it only checks for destructive commands and sensitive paths.
5. **Concrete fix:** Extend the hook protocol: (1) Add a `PostToolUse` hook that validates outcomes (e.g., after file edit, check that the edit doesn't introduce lint errors). (2) Add state tracking: record which files have been read, and block edits to areas where the scoped `AGENTS.md` hasn't been read. Cost: moderate — requires maintaining a session state file.
6. **Priority:** MEDIUM
7. **Confidence:** 75%

---

## 1.5 Reasoning Quality

### ISSUE-12: Adversarial Critique Is Self-Review, Not Independent

1. **What is broken:** Phase 6 (Adversarial Critique) in the orchestrator runs within the same LLM context as the plan it's critiquing. The `adversarial-review` skill is a prompt instruction, not an independent agent call with a separate context window.
2. **Why it matters:** Self-review by the same LLM in the same context is fundamentally limited by anchoring bias. Research on LLM self-correction shows it often reinforces rather than challenges initial outputs.
3. **Evidence:** `orchestrator.agent.md` Phase 6 says "Use the `adversarial-review` skill for medium- or high-risk work." This loads a markdown file into the same conversation — not a separate agent.
4. **Real-world failure mode:** Agent plans an approach with a subtle flaw, then "critiques" it and finds nothing wrong because it generated the plan. Ships with the flaw.
5. **Concrete fix:** For non-trivial work, make Phase 6 invoke `runSubagent(agentName="reviewer")` with the plan as input. The reviewer runs in a clean context, applies its own hard checklist, and returns a structured verdict. The orchestrator must not proceed past critique with a `REJECT` verdict. This provides genuine adversarial pressure.
6. **Priority:** HIGH
7. **Confidence:** 90%

### ISSUE-13: No Confidence/Uncertainty Modeling

1. **What is broken:** No mechanism exists for the agent to express confidence in its outputs. Every assertion, code change, and diagnosis is treated as equally certain.
2. **Why it matters:** Without confidence modeling, the system cannot route uncertain tasks to human review or apply more conservative verification. High-confidence trivial fixes and low-confidence architectural recommendations are treated identically.
3. **Evidence:** The context packet schema has no confidence field. The run artifact schema has no confidence field. No prompt or instruction asks the LLM to rate its confidence.
4. **Real-world failure mode:** Agent is 30% confident about a database migration approach but presents it with the same certainty as a typo fix. User trusts it, migration breaks production.
5. **Concrete fix:** Add a `confidence` field (0.0-1.0) to the `current_step` and `run_artifact` schemas. Add a prompt instruction: "Rate confidence. Below 0.6 → escalate to human. Below 0.3 → abort." Note: LLM confidence is not calibrated probability, but it is a useful relative signal for routing.
6. **Priority:** MEDIUM
7. **Confidence:** 85%

---

## 1.6 Model Strategy

### ISSUE-14: All Specialist Agents Hardcoded to gpt-4o — No Model Routing

1. **What is broken:** Every specialist agent in `.github/agents/` specifies `model: gpt-4o`. The orchestrator has no model field (defaulting to whatever the VS Code extension uses). There is no task-to-model routing logic.
2. **Why it matters:** Different tasks have different model requirements. A simple lint fix doesn't need the most expensive model. A complex architectural plan may benefit from a stronger reasoning model. Without routing, every task pays the same cost.
3. **Evidence:** `analyst.agent.md`: `model: gpt-4o`. `planner.agent.md`: `model: gpt-4o`. `qa.agent.md`: `model: gpt-4o`. All identical.
4. **Real-world failure mode:** (a) Waste: simple tasks use an expensive model. (b) Capability gap: complex reasoning tasks may need Claude Opus or o1-series, but gpt-4o is always used. (c) No fallback: if gpt-4o is unavailable/degraded, the system has no alternative.
5. **Concrete fix:** Add a `modelRouter` section to `workflow-manifest.json` mapping task complexity to model tiers: `{ "trivial": "gpt-4o-mini", "research-only": "gpt-4o", "brownfield-improvement": "claude-sonnet-4", "greenfield-feature": "claude-opus-4", "review-only": "claude-opus-4" }`. The orchestrator reads this after classification and sets the model for subsequent subagent calls.
6. **Priority:** MEDIUM
7. **Confidence:** 80%

---

## 1.7 Performance Constraints

### ISSUE-15: No Cost Tracking or Token Budget Per Task

1. **What is broken:** No per-task cost tracking exists. The `taskLedger` in the run artifact schema has `tokensIn` and `tokensOut` fields, but these are self-reported by the LLM. No real token counting. No price mapping. No budget enforcement.
2. **Why it matters:** Without cost visibility, there is no optimization signal. An agent spending $5 on a typo fix looks the same as one spending $0.10.
3. **Evidence:** No `tiktoken` dependency. No price table. `taskLedger.tokensIn`/`tokensOut` are `"type": "integer"` — but who fills them in? The LLM, inaccurately.
4. **Real-world failure mode:** Agent enters a retry loop on a complex task, making 20 LLM calls at $0.50 each. Total cost: $10 for a task that should have been escalated after $1. No signal to stop.
5. **Concrete fix:** Create `scripts/agent/token_budget.py` using `tiktoken`. Expose a CLI and a Python library function: `count_tokens(text, model) → int` and `estimate_cost(tokens_in, tokens_out, model) → float`. Wire into the pretool hook to enforce a per-task budget ceiling (configurable, default $2).
6. **Priority:** MEDIUM
7. **Confidence:** 90%

---

## 1.8 Failure Handling

### ISSUE-16: No Explicit Retry, Recovery, or Abort Mechanism

1. **What is broken:** The workflow has no retry logic, no recovery workflows, and no explicit ABORT state. If the agent gets stuck, it either loops indefinitely or produces garbage.
2. **Why it matters:** Every robust orchestration system (LangGraph, AutoGen) has explicit retry policies, dead-letter queues, and abort states. This system has none.
3. **Evidence:** `workflow-manifest.json` has `maxCritiquePasses: 2` (at least that limits retries for critique). But there is no `maxRetries`, no `maxToolCallsPerTask`, no `ABORT` state in any schema. The run artifact `status` enum has `"blocked"` but no `"aborted"` or `"failed-permanently"`.
4. **Real-world failure mode:** Agent tries to fix a flaky test 5 times, each time making it worse. No circuit breaker. User watches the agent spiral for 20 minutes.
5. **Concrete fix:** (1) Add `"aborted"` to the run artifact `status` enum. (2) Add `maxToolCallsPerTask: 30` to `workflow-manifest.json`. (3) In the pretool hook, track tool call count per session and emit `deny` after threshold. (4) Add explicit escalation: after 3 failed attempts at a subtask, emit a structured "ESCALATE" response to the user instead of continuing.
6. **Priority:** HIGH
7. **Confidence:** 90%

---

## 1.9 Scope Control

### ISSUE-17: No Hard Scope Boundaries — Agent Can Touch Any File

1. **What is broken:** The pretool hook blocks destructive operations and gates sensitive paths, but nothing prevents the agent from editing files outside the scope of its task. If asked to fix a bug in `src/api/`, the agent could also "improve" `frontend/components/` or modify CI workflows.
2. **Why it matters:** Scope creep is one of the most common LLM failure modes. Without hard boundaries, a simple bug fix can turn into an unwanted refactor.
3. **Evidence:** The pretool hook checks sensitive paths but has no concept of "task scope." The context packet has no `allowed_paths` or `forbidden_paths` field.
4. **Real-world failure mode:** User asks to fix a Python bug. Agent also "notices" a TypeScript issue and "fixes" it, introducing a regression in the frontend.
5. **Concrete fix:** Add an `allowed_paths` field to the context packet. The orchestrator fills it during classification based on the task scope. Add a check in the pretool hook: if an edit targets a path outside `allowed_paths`, emit `"ask"` with a scope-expansion warning.
6. **Priority:** MEDIUM
7. **Confidence:** 80%

---

## 1.10 Persistence & Artifacts

### ISSUE-18: Run Artifacts Are Optional and Have No Concurrency Safety

1. **What is broken:** The `run_artifact` section in the context packet has `mode: "not-needed" | "active" | "required"`. For most tasks, it defaults to "not-needed." When active, artifacts are written to JSON files with no locking, no UUID-namespaced paths, and no protection against concurrent writes.
2. **Why it matters:** If two agent sessions edit the same run artifact, data is lost. If artifacts are usually "not-needed," there's no audit trail for most work.
3. **Evidence:** Example artifact path: `.github/agent-platform/examples/brownfield-run-artifact.json` — a shared example file, not a per-run namespaced path. No file locking in any script.
4. **Real-world failure mode:** Two concurrent chat sessions both write to the same artifact file. Second write overwrites first. Trace data lost.
5. **Concrete fix:** (1) Namespace run artifacts by UUID: `docs/runs/{uuid}/artifact.json`. (2) Add file-locking via `fcntl` (Unix) or `msvcrt` (Windows) in any write helper. (3) Make run artifacts "active" by default for all non-trivial tasks.
6. **Priority:** LOW
7. **Confidence:** 80%

### ISSUE-19: Spec-to-Code-to-Test Traceability Is Aspirational

1. **What is broken:** The `requirements-traceability` skill exists as a prompt instruction. No automated system verifies that every spec requirement has corresponding code and tests. The PR template and CI check for spec reference presence, but not for spec requirement coverage.
2. **Why it matters:** Without automated traceability, requirements can be silently dropped during implementation. The manual skill relies on the LLM remembering to run it.
3. **Evidence:** `pr-quality.yml` checks for spec path string presence in PR body. No CI step validates that the spec's acceptance criteria are each covered by a test.
4. **Real-world failure mode:** Spec has 10 acceptance criteria. Implementation covers 8. LLM claims "All acceptance criteria addressed." CI passes because the spec file path is present.
5. **Concrete fix:** Phase 2 item. Extend the PR quality gate: parse spec files for `- [ ]` checklist items, parse test files for corresponding test function names or `@pytest.mark.parametrize` tags, flag uncovered criteria. This is a structured text check, not an LLM task.
6. **Priority:** MEDIUM
7. **Confidence:** 75%

---

## 1.11 Evaluation & Learning

### ISSUE-20: No Eval Harness Exists

1. **What is broken:** There is no evaluation harness. No benchmark suite. No way to measure whether a change to the agent system improved or degraded task success rate.
2. **Why it matters:** Without evals, changes to prompts, schemas, or workflows are guesswork. You cannot know if a "improvement" actually helped.
3. **Evidence:** `workflow-benchmarks.json` contains contract-level marker checks (does a prompt file contain required strings?). These are structural, not behavioral. No Inspect AI, no OpenAI Evals, no behavioral eval suite.
4. **Real-world failure mode:** Engineer improves the orchestrator prompt. Marker checks pass. But the agent now skips critique 40% of the time because the prompt change had an unintended effect. No way to detect this.
5. **Concrete fix:** Phase 0 item. Create `evals/` directory. Use Inspect AI (Python-native, open-source). Define 10-20 benchmark tasks spanning trivial, brownfield, and greenfield. Each task has: input prompt, expected outputs (files created, tests passed, verification commands run), and grading rubrics. Run evals before and after every agent system change.
6. **Priority:** HIGH
7. **Confidence:** 95%

### ISSUE-21: No Learning Loop From Failures

1. **What is broken:** When the agent fails, there is no mechanism to index the failure, identify root cause, and retrieve the lesson for similar future tasks.
2. **Why it matters:** Without failure-driven learning, the system makes the same mistakes indefinitely. This is the difference between a static prompt and an improving system.
3. **Evidence:** No `/memories/repo/failures/` directory. No failure indexing logic. No retrieval-augmented repair mechanism.
4. **Real-world failure mode:** Agent mishandles async Python context managers 3 times across different tasks. Each time, it starts from scratch with no memory of the previous failure.
5. **Concrete fix:** Phase 4 item. (1) After each failed task, write a structured postmortem to `/memories/repo/failures/{task-id}.md` with: symptoms, root cause, fix applied, prevention pattern. (2) Before each task, query the failure index for similar symptoms. (3) Integrate with Chroma for semantic search over past failures.
6. **Priority:** MEDIUM
7. **Confidence:** 85%

---

## 1.12 Extensibility

### ISSUE-22: Dual Skill Registry — `.github/skills/` vs `skills/`

1. **What is broken:** Skills live in two locations: `.github/skills/` (14 skills, registered in `skill-registry.json`) and root-level `skills/` (8 skills, NOT registered in `skill-registry.json`). The two registries are disjoint and use different conventions.
2. **Why it matters:** The orchestrator's trigger matrix only references `.github/skills/`. The root `skills/` are invisible to the automated trigger system. They might as well not exist for agentic workflows.
3. **Evidence:** Root `skills/` contents: `api-contract-review`, `application-security-review`, `docker-deploy-validation`, `docs-release-readiness`, `frontend-accessibility`, `python-quality`, `telemetry-observability-audit`, `testing-regression`. None of these appear in `skill-registry.json`.
4. **Real-world failure mode:** Agent receives a task involving API contract review. The `api-contract-review` skill exists in `skills/` but has no trigger tag. The agent doesn't find it.
5. **Concrete fix:** Consolidate. Either: (a) move root `skills/` into `.github/skills/` and register them in the manifest, or (b) extend `workflow-manifest.json` to reference both locations. Option (a) is cleaner — collocate all agent-discoverable skills.
6. **Priority:** MEDIUM
7. **Confidence:** 95%

### ISSUE-23: Skill Trigger Accuracy Is Untested

1. **What is broken:** The trigger matrix maps tags like `"frontend"`, `"brownfield"`, `"bugfix"` to skills. But nowhere is this mapping tested against actual task inputs. No eval checks whether a given task description correctly triggers the right skills.
2. **Why it matters:** If triggers misfire (false positives or false negatives), the agent either loads irrelevant skills (wasting context) or misses critical skills.
3. **Evidence:** `workflow-benchmarks.json` tests prompt marker presence, not trigger resolution. No test says "given task X classified as brownfield, verify skills Y and Z are triggered."
4. **Real-world failure mode:** A brownfield task involving API work should trigger `observability-inject` and `test-hardening`. Missing trigger: no observability added.
5. **Concrete fix:** Add trigger resolution tests to the eval harness. For each benchmark task, define expected triggered skills. Verify the trigger index resolves correctly.
6. **Priority:** LOW
7. **Confidence:** 85%

---

## 1.13 Frontend Systems

### ISSUE-24: Frontend Area Is a Scaffold — No Verified Runtime Code

1. **What is broken:** `frontend/` contains only `AGENTS.md`. There is no `package.json`, no `vite.config.ts`, no `tsconfig.json`, no `eslint.config.js`, no source files. The `frontend/AGENTS.md` describes a complete React 19 + Vite 8 + Vitest 4 stack that does not exist.
2. **Why it matters:** The frontmatter documents an imaginary stack. When the agent reads `frontend/AGENTS.md`, it may attempt to run `npm ci`, `npm run lint`, or `npm run build` — all of which will fail because there is no `package.json`.
3. **Evidence:** `frontend/` directory contains only `AGENTS.md`. `verify-narrow.sh` has a frontend section that runs `npm run lint` and `npm run build` — these will fail.
4. **Real-world failure mode:** Agent is asked to add a frontend feature. Reads `frontend/AGENTS.md`, trusts the tech stack summary, tries `npm ci`, fails. Wastes an entire subtask.
5. **Concrete fix:** Two options: (a) If the frontend is planned, scaffold it: `package.json`, `vite.config.ts`, `tsconfig.json`, `eslint.config.js`, `src/App.tsx`, `src/main.tsx`. (b) If the frontend is not yet started, update `frontend/AGENTS.md` to say "This area is reserved. No runtime code exists yet. Do not attempt to install or build."
6. **Priority:** HIGH
7. **Confidence:** 99%

### ISSUE-25: Frontend Verification Is Not Wired Into Routing Metadata

1. **What is broken:** Even when the frontend exists, `repo-map.json` `verificationRoutes.frontend` is `[]`. The `sync_agent_platform.py` generates frontend routes only when `frontend/package.json` exists and has matching script names. Since the package.json doesn't exist, no routes.
2. **Why it matters:** This is a systemic architectural gap: the verification system is conditional on filesystem presence, but the agent guidance assumes the stack exists. These must be consistent.
3. **Evidence:** `build_frontend_verification_routes()` in `sync_agent_platform.py` checks for `frontend/package.json`. Returns empty list when missing.
4. **Real-world failure mode:** See ISSUE-24. But even when frontend code is added, if the script names don't match the expected values (`lint`, `typecheck`, `test`, `test:e2e`), verification routes will be silently missing.
5. **Concrete fix:** (1) Guard `frontend/AGENTS.md` with a conditional header: "Stack below is the target spec — verify `package.json` exists before running commands." (2) When scaffolding the frontend, ensure `package.json` scripts include `lint`, `typecheck`, `test`, and `build` so `sync_agent_platform.py` picks them up.
6. **Priority:** HIGH (coupled with ISSUE-24)
7. **Confidence:** 95%

### ISSUE-26: No Frontend-Backend API Contract Enforcement

1. **What is broken:** No OpenAPI spec, no Zod schema, no Pydantic → OpenAPI export, no client generation, no contract testing. The `frontend/AGENTS.md` says "All API response shapes must have a corresponding interface in `types/`" — but this is a manual rule with no automation.
2. **Why it matters:** When both frontend and backend exist, the API boundary is the highest-risk surface for silent drift. A backend schema change that doesn't update the frontend type is a runtime crash waiting to happen.
3. **Evidence:** No `openapi.json`, no `openapi.yaml`, no Zod files, no Orval config, no openapi-typescript config. No Schemathesis CI step.
4. **Real-world failure mode:** Backend adds a required field to a response model. Frontend types are not updated. Frontend renders `undefined` for the new field. No CI catches it.
5. **Concrete fix:** Phase 3 item. (1) Add Pydantic `→` OpenAPI generation to the backend build. (2) Add `openapi-typescript` or Orval to the frontend build to generate TypeScript types from the OpenAPI spec. (3) Add a CI step that regenerates and diffs — any drift blocks the PR. (4) Add Schemathesis for runtime API contract testing.
6. **Priority:** HIGH (when runtime code exists)
7. **Confidence:** 95%

---

# PHASE 2 — MISSING SYSTEMS ANALYSIS

| # | Missing System | Gap | Consequence | Implementation Approach |
|---|---|---|---|---|
| M1 | **Deterministic state machine** | Phases are prose, not enforced transitions | Agent skips critique, planning, or verification at will | LangGraph `StateGraph` or lightweight Python finite-state-machine. Encode `phaseOrder` as nodes, define allowed transitions, validate against `current_phase` in the context packet |
| M2 | **Model routing layer** | All agents use gpt-4o regardless of task complexity | Cost waste on trivial tasks; capability gap on complex ones | `modelRouter` config in `workflow-manifest.json` with task-class → model mapping. Orchestrator reads after classification |
| M3 | **Token budget allocator** | Token counts are LLM self-reported | Budget overruns, silent truncation, degraded quality | `tiktoken` Python helper + pretool hook integration. Real per-turn counting with cumulative budget tracking |
| M4 | **Cost tracking layer** | No per-task cost visibility | Unbounded spend, no optimization signal | Token × model price table. Per-task ledger entries with real counts. Dashboard or summary CLI |
| M5 | **Uncertainty/confidence scoring** | No confidence modeling on any output | Overconfident failures proceed silently; no routing to human review | `confidence: 0.0-1.0` field in context packet `current_step` and run artifact. Routing rules: <0.6 → escalate, <0.3 → abort |
| M6 | **Independent critic role** | Critique runs in same context as generation | Anchoring bias; self-review finds nothing wrong | Subagent invocation of `reviewer` agent for Phase 6. Structured PASS/REJECT verdict required before proceeding |
| M7 | **Eval harness** | No behavioral evaluation suite | Cannot measure impact of system changes | Inspect AI or OpenAI Evals. 20+ benchmark tasks. Run before/after every agent system change |
| M8 | **Learning loop** | No failure indexing or retrieval-augmented repair | System repeats same mistakes | Structured failure postmortems → Chroma index → semantic retrieval on new tasks |
| M9 | **Artifact retrieval system** | No vector-backed memory for past work | Duplicate work, lost context, no reuse | Chroma (local Python) as MCP server or direct integration. Index run artifacts, specs, and failure postmortems |
| M10 | **Scope enforcement** | Agent can modify any file regardless of task scope | Unintended side effects, scope creep | `allowed_paths` in context packet + pretool hook validation |
| M11 | **Abort/circuit-breaker** | No safe stop path; no retry limit | Agent spirals on hard tasks | `maxToolCallsPerTask`, `"aborted"` status, escalation protocol |
| M12 | **API contract validation** | No OpenAPI, Zod, or contract testing | Silent frontend-backend drift, runtime crashes | Pydantic → OpenAPI → openapi-typescript pipeline + Schemathesis CI |
| M13 | **Execution tracing / observability** | No structured trace emission | Cannot debug agent decisions, no replay capability | OpenTelemetry-compatible structured event log. Per-run trace file with decision DAG |
| M14 | **Static analysis gates** | No Semgrep, no Tree-sitter | Security vulnerabilities and code smells undetected | Semgrep with OWASP rules in CI + verify-narrow.sh |

---

# PHASE 3 — TARGET ARCHITECTURE

## Data Flow

```
User Request
     │
     ▼
┌─────────────────────────────────┐
│ PHASE 0: Goal Anchor            │ ← Inject one-line goal
│   Read AGENTS.md + manifest     │
│   (progressive: ONLY these two) │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ PHASE 1: Classify + Route       │ ← Deterministic classification
│   Model Router selects model    │ ← workflow-manifest.json modelRouter
│   Token Budget Allocator inits  │ ← tiktoken real counting
│   Scope Boundaries set          │ ← allowed_paths computed
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│ STATE MACHINE CONTROLLER                                │
│ (Python FSM validating transitions from phaseOrder)     │
│                                                         │
│ Allowed transitions:                                    │
│   classify → breadth-scan → depth-dive →                │
│   lock-requirements → choose-approach →                 │
│   adversarial-critique → revise → execute-or-answer →   │
│   traceability-and-verify                               │
│                                                         │
│ Conditional edges:                                      │
│   - trivial: classify → execute-or-answer (skip middle) │
│   - critique REJECT: revise → adversarial-critique      │
│     (max 2 loops)                                       │
│   - budget exceeded: any → ABORT                        │
│   - confidence < 0.3: any → ABORT                       │
│   - confidence < 0.6: execute → ESCALATE                │
└──────────┬──────────────────────────────────────────────┘
           │
           ├──► EXECUTION HARNESS
           │      ├── Tool Dispatcher (pretool hook enforced)
           │      ├── Code Generation (LLM)
           │      ├── Verification Gate:
           │      │     ├── ruff check (Python)
           │      │     ├── mypy --strict (Python)
           │      │     ├── tsc --noEmit (TypeScript)
           │      │     ├── ESLint w/ React Hooks plugin
           │      │     ├── vite build (frontend)
           │      │     ├── semgrep --config=auto (security)
           │      │     └── pytest / vitest (tests)
           │      └── If verification fails → loop back to execute
           │           (max 3 verification retries)
           │
           ├──► CRITIQUE GATE (subagent: reviewer)
           │      ├── Independent context window
           │      ├── Structured verdict: PASS / WARN / REJECT
           │      ├── REJECT → back to revise (max 2)
           │      ├── WARN → proceed with human notification
           │      └── PASS → continue
           │
           ├──► SKILL DISPATCHER (unified registry)
           │      ├── .github/skills/ + skills/ consolidated
           │      ├── Trigger resolution from task tags
           │      └── Loaded into context on demand, not front-loaded
           │
           ├──► MEMORY/RETRIEVAL LAYER
           │      ├── Working: context packet scratchpad (current subtask)
           │      ├── Episodic: compressed summaries (in-memory)
           │      └── Semantic: Chroma vector store
           │           ├── Past run artifacts
           │           ├── Failure postmortems
           │           └── Spec-to-code mappings
           │
           ├──► ARTIFACT STORE
           │      ├── UUID-namespaced: docs/runs/{uuid}/
           │      ├── Append-only trace log
           │      ├── Concurrent-safe (file locking)
           │      └── TTL: 90 days, then archive
           │
           ├──► CONTRACT VALIDATION LAYER
           │      ├── OpenAPI spec (source of truth)
           │      ├── Pydantic → OpenAPI (backend)
           │      ├── openapi-typescript (frontend)
           │      ├── Schema Diff Engine (on every change)
           │      └── Gate: CONTRACT_BROKEN blocks merge
           │
           ├──► EVAL HARNESS (Inspect AI)
           │      ├── Benchmark tasks (20+)
           │      ├── Grading rubrics
           │      └── Before/after comparison on system changes
           │
           ├──► LEARNING LOOP
           │      ├── Failure → structured postmortem
           │      ├── Index in Chroma
           │      └── Retrieve on new tasks
           │
           └──► OBSERVABILITY (OpenTelemetry-compatible)
                  ├── Structured event log (JSON, append-only)
                  ├── Per-event: type, timestamp, tokens, model, decision
                  ├── Context snapshots at phase transitions
                  └── Decision trace graph (DAG of observations → decisions)
```

## Enforcement Boundaries (Code, Not Prompts)

| Guarantee | Enforcement Method | Location |
|---|---|---|
| Phase transition validity | Python FSM + schema validation | `scripts/agent/state_machine.py` + pretool hook |
| Token budget | tiktoken real counting | `scripts/agent/token_budget.py` + pretool hook |
| Tool call limit | Counter in pretool hook state | `pretool_approval_policy.py` |
| Scope boundaries | `allowed_paths` check | pretool hook |
| Independent critique | Subagent invocation (separate context) | orchestrator Phase 6 |
| Verification before merge | CI verification steps | `ci.yml`, `pr-quality.yml` |
| API contract validity | Schema diff + CI gate | `ci.yml` contract step |
| Static analysis | Semgrep CI step | `ci.yml` |

## Where LLM Is Constrained vs Free

| Activity | LLM Freedom Level | Constraint |
|---|---|---|
| Task classification | Free (LLM judges) | Must match enum in workflow-manifest taskClasses |
| DAG planning | Free (LLM plans) | Schema requires task_graph for non-trivial tasks |
| Code generation | Free (LLM writes) | Gated by ruff/mypy/tsc/semgrep/tests |
| Critique | Constrained (separate agent) | REJECT verdict is binding |
| Phase transitions | Constrained (FSM) | Only allowed transitions permitted |
| Token budget | Constrained (tiktoken) | Hard cutoff at budget ceiling |
| Scope | Constrained (pretool hook) | `allowed_paths` enforced |
| Confidence | Free (LLM estimates) | Low confidence triggers escalation |

---

# PHASE 4 — IMPLEMENTATION ROADMAP

## Phase 0 — Baseline (Before Any Changes)

### P0.1: Eval Harness Setup
- **Create:** `evals/` directory with `evals/tasks/`, `evals/rubrics/`, `evals/runner.py`
- **Dependency:** `inspect-ai` (pip install)
- **Define:** 10 benchmark tasks:
  1. Trivial: fix a typo in a markdown file
  2. Trivial: answer a question about repo structure
  3. Research: summarize a spec
  4. Brownfield: add a field to an existing schema
  5. Brownfield: fix a bug in sync_agent_platform.py
  6. Greenfield: scaffold a new Python module with tests
  7. Test-only: add tests for an existing module
  8. Review: review a diff for security issues
  9. Frontend: scaffold a React component (when frontend exists)
  10. Architecture: propose an ADR
- **Expected outcome:** Baseline success rate and token usage per task

### P0.2: Token Logging
- **Create:** `scripts/agent/token_budget.py`
- **Dependency:** `tiktoken`
- **Contents:**
```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def estimate_cost(tokens_in: int, tokens_out: int, model: str) -> float:
    prices = {
        "gpt-4o": (0.0025, 0.010),       # per 1K tokens
        "gpt-4o-mini": (0.00015, 0.0006),
        "claude-sonnet-4": (0.003, 0.015),
        "claude-opus-4": (0.015, 0.075),
    }
    in_price, out_price = prices.get(model, (0.003, 0.015))
    return (tokens_in / 1000 * in_price) + (tokens_out / 1000 * out_price)
```
- **Expected outcome:** Accurate token counting available for all subsequent phases

---

## Phase 1 — Quick Wins (1-2 days)

### P1.1: Make `task_graph` Required for Non-Trivial Work
- **Modify:** `.github/agent-platform/context-packet.schema.json`
- **Change:** Add `"task_graph"` to `"required"` array
- **Update:** Example packets to all include `task_graph`
- **Verify:** `python scripts/agent/sync_agent_platform.py --check`

### P1.2: Consolidate Dual Skill Registries
- **Move:** All 8 skills from `skills/` into `.github/skills/`
- **Update:** `workflow-manifest.json` skills section with new entries
- **Verify:** `sync_agent_platform.py --check` validates alignment

### P1.3: Fix Frontend AGENTS.md Accuracy
- **Modify:** `frontend/AGENTS.md`
- **Change:** Add a header: "⚠️ This describes the target stack. Before running any commands, verify `package.json` exists. If it does not, this area is reserved but not yet implemented."

### P1.4: Add `"aborted"` Status to Run Artifact Schema
- **Modify:** `.github/agent-platform/run-artifact-schema.json`
- **Change:** `status.enum` → `["in-progress", "blocked", "review-needed", "done", "aborted"]`
- **Also add:** `"failed"` to `taskLedger.completionStatus` enum (already present)

### P1.5: Add Confidence Field to Schemas
- **Modify:** `context-packet.schema.json` → add `confidence` (0.0-1.0) to `current_step`
- **Modify:** `run-artifact-schema.json` → add `confidence` to root level
- **Update:** Example packets

### P1.6: Add `CONTRACT_BROKEN` Verification Status
- **Modify:** `run-artifact-schema.json` → `verification.status.enum` → add `"contract-broken"`
- **Update:** orchestrator instructions to recognize this status

---

## Phase 2 — Enforcement (3-5 days)

### P2.1: Token Budget Enforcement
- **Create:** `scripts/agent/token_budget.py` (from P0.2)
- **Modify:** `pretool_approval_policy.py` → add token budget tracking
- **Logic:** Track cumulative tokens per session. If exceeds configurable ceiling (default: 200K input tokens ≈ $2), emit `"ask"` decision

### P2.2: Tool Call Limit
- **Modify:** `pretool_approval_policy.py`
- **Add:** `maxToolCallsPerTask: 50` tracking
- **Logic:** After 50 tool calls in a session, emit `"deny"` with "Tool call limit exceeded. Escalating to human."

### P2.3: Verification Route Population
- **Modify:** `sync_agent_platform.py` `build_backend_verification_routes()` and `build_frontend_verification_routes()`
- **Change:** Add static fallback routes that are always present:
  - Backend: `["ruff check src/", "python -m mypy src/"]`
  - Frontend: `["cd frontend && npm run lint", "cd frontend && npm run build"]`
- **Condition:** Only emit if `src/` or `frontend/` directories exist (they do)

### P2.4: Semgrep Integration
- **Create:** `.semgrep.yml` with OWASP top-10 rules
- **Modify:** `verify-narrow.sh` → add `semgrep --config=auto src/` step
- **Modify:** `ci.yml` → add Semgrep CI step

### P2.5: Independent Critique Gate
- **Modify:** `orchestrator.agent.md` Phase 6
- **Change:** For `medium-risk` and `high-risk` tasks, require: "Invoke the reviewer agent as a subagent for independent critique. Parse its PASS/REJECT verdict. If REJECT, return to Phase 7 (revise). Do not proceed past Phase 6 without a PASS verdict."

### P2.6: Scope Enforcement
- **Modify:** `context-packet.schema.json` → add `allowed_paths` array to root
- **Modify:** `pretool_approval_policy.py` → read `allowed_paths` from session state, check edit targets

---

## Phase 3 — Architecture Upgrade (1-2 weeks)

### P3.1: Model Router
- **Modify:** `workflow-manifest.json` → add `modelRouter` section:
```json
"modelRouter": {
  "default": "gpt-4o",
  "taskClassOverrides": {
    "trivial": "gpt-4o-mini",
    "greenfield-feature": "claude-opus-4",
    "review-only": "claude-opus-4"
  },
  "complexityEscalation": {
    "highTokenCount": "claude-sonnet-4",
    "multiSurface": "claude-sonnet-4"
  }
}
```
- **Modify:** Orchestrator to read `modelRouter` after classification and set model for subagent calls

### P3.2: State Machine Implementation
- **Create:** `scripts/agent/state_machine.py`
- **Contents:** Python FSM class with:
  - States from `workflow.phaseOrder`
  - Allowed transitions (sequential + skip for trivial + retry for critique)
  - Conditional edges (budget exceeded → ABORT, low confidence → ESCALATE)
  - `validate_transition(from_state, to_state) → bool`
- **Integrate:** Into pretool hook or as a standalone validation helper

### P3.3: Progressive Context Loading
- **Modify:** `orchestrator.agent.md` "Before doing anything" section
- **Change:** Phase 0 reads only `AGENTS.md` + `workflow-manifest.json`. Subsequent phases load files based on `changeRouting.readBeforeEditing` for the classified target area.

### P3.4: API Contract Pipeline (When Runtime Code Exists)
- **Create:** `scripts/agent/contract_check.py`
- **Backend:** Pydantic model export → OpenAPI JSON
- **Frontend:** `openapi-typescript` generation from OpenAPI JSON
- **CI step:** Diff generated types against checked-in types. Fail if different.
- **Dependencies:** `openapi-typescript` (npm), Pydantic (already used if backend exists)

---

## Phase 4 — Intelligence Layer (2-4 weeks)

### P4.1: Chroma Integration for Semantic Memory
- **Dependency:** `chromadb` (pip install)
- **Create:** `scripts/agent/memory_store.py`
- **Index:** Run artifacts, failure postmortems, spec files
- **Query:** On task start, embed goal → retrieve top-5 relevant artifacts
- **MCP option:** Wrap as an MCP server for direct agent access

### P4.2: Learning Loop
- **Create:** `scripts/agent/failure_index.py`
- **On failure:** Write structured postmortem to `/memories/repo/failures/`
- **Index:** In Chroma with tags: symptoms, root cause, area, task class
- **Retrieve:** Before each task, query for similar failures

### P4.3: Execution Tracing
- **Create:** `scripts/agent/trace_logger.py`
- **Schema:** JSON event log per run: `{run_id, trace_id, events: [{event_type, timestamp, context_snapshot_id, inputs, outputs, model_used, token_usage, decision_rationale}]}`
- **Integration:** Structured logging in pretool hook (tool calls), orchestrator (phase transitions), verification (results)
- **Storage:** `docs/runs/{uuid}/trace.json` (append-only)
- **Compatible with:** OpenTelemetry span format, Phoenix (Arize AI), LangSmith

### P4.4: Full Eval Harness
- **Expand:** 10 tasks → 25+ tasks
- **Add:** Regression detection: run evals before/after every PR that touches `.github/`
- **Add:** Confidence calibration: compare predicted confidence vs actual pass rate

---

# PHASE 5 — METRICS & EVALS

| Metric | Definition | Measurement Method | Target |
|---|---|---|---|
| Task success rate | % tasks completed without escalation or failure | Eval harness pass/fail per run | >85% |
| Regression rate | % of tasks introducing test failures | pytest/vitest before/after diff | <5% |
| Lint/type pass rate | % of generated code passing ruff + mypy + tsc | CI gate output | >95% |
| Token efficiency | Tokens used per successful task | tiktoken per-run logging | <100K avg |
| Cost per successful task | USD per completed task | Token × model price | <$1.50 avg |
| Latency | Wall-clock time per task | Trace timestamps | <5 min for brownfield |
| Confidence calibration | Predicted confidence vs actual outcome | Eval harness comparison | Within 20% |
| Escalation correctness | % of escalations that were genuinely necessary | Human review | >70% |
| Contract drift rate | % of changes triggering CONTRACT_BROKEN | Contract validation logs | <2% |
| Frontend build pass rate | % of frontend changes passing tsc + build | CI gate output | >95% |
| Critique independence rate | % of non-trivial tasks using subagent critique | Trace log analysis | 100% for medium+ risk |
| Phase skip rate | % of tasks that skip required phases | FSM violation log | 0% |

---

# PHASE 6 — RISKS & ANTI-PATTERNS

## Over-Engineering Risks

| Risk | Mitigation |
|---|---|
| State machine complexity exceeds maintainability budget | Keep FSM flat: 10 states, ~15 transitions. No nested sub-states. LangGraph graphs should be acyclic except for critique-revise loop |
| Eval harness produces false confidence | Validate evals against known-bad examples first. Include adversarial tasks that _should_ fail |
| Chroma adds infrastructure overhead | Use local persistent mode (SQLite backend). No external server needed |
| Token counting adds latency | tiktoken is <1ms per call. Cache encoding objects |

## Enforcement Backfiring

| Risk | Mitigation |
|---|---|
| Hard gates blocking all progress on ambiguous tasks | WARN level is non-blocking with human notification. Only REJECT and budget-exceeded are blocking |
| Over-restrictive scope enforcement | `allowed_paths` can include wildcards. Scope expansion requires human `"ask"` confirmation, not hard deny |
| Critique subagent rejects valid approaches | Limit to 2 critique-revise passes. After 2 REJECTs, escalate to human |

## Persistent LLM Limitations

| Limitation | Handling |
|---|---|
| Confidence scores are not calibrated probabilities | Treat as relative signals only. Use for routing, not for guarantees |
| Model routing cannot substitute for capability limits | Route complex tasks to strongest available model but accept that some tasks exceed all models |
| Replay mode cannot guarantee identical outputs | Treat replay as approximate. Use for debugging patterns, not exact reproduction |
| Self-reported token counts are unreliable | This is why tiktoken is mandatory. Never trust LLM self-reports |

## Long-Term System Drift

| Risk | Mitigation |
|---|---|
| Learning loop reinforces incorrect patterns | Require human validation of failure postmortems before indexing. Add a `verified: true/false` flag |
| Contract graph becomes stale | OpenAPI spec is generated from code, not hand-maintained. Staleness is structurally prevented |
| Trace store unbounded growth | TTL: 90 days for runs, 365 days for failure postmortems. Archive to compressed storage |
| Agent system changes break evals without detection | Run eval suite in CI for any PR touching `.github/`, `scripts/agent/`, or workflow metadata |

---

# SUMMARY OF FINDINGS

## Critical (Must Fix Immediately)

1. **ISSUE-02:** No state machine — phases are unenforced prompt theater
2. **ISSUE-12:** Adversarial critique is self-review — no real adversarial pressure
3. **ISSUE-20:** No eval harness — changes are unmeasured guesswork
4. **ISSUE-24:** Frontend AGENTS.md describes stack that doesn't exist
5. **ISSUE-09:** Verification routes are empty — agent skips all verification

## High Priority

6. **ISSUE-01:** `task_graph` optional in schema — DAG planning unenforced
7. **ISSUE-04:** Token limits are prompt suggestions — no tiktoken
8. **ISSUE-16:** No retry limit or abort mechanism — agent can spiral
9. **ISSUE-03:** Single agent monolith — planner/executor/critic are same LLM
10. **ISSUE-26:** No API contract enforcement infrastructure

## Medium Priority

11. **ISSUE-07:** Memory system is file-based, not vector-backed
12. **ISSUE-08:** Front-loaded context wastes tokens on trivial tasks
13. **ISSUE-10:** No static analysis (Semgrep) integration
14. **ISSUE-13:** No confidence/uncertainty modeling
15. **ISSUE-14:** All agents hardcoded to gpt-4o — no model routing
16. **ISSUE-15:** No cost tracking
17. **ISSUE-22:** Dual skill registry — root `skills/` invisible to triggers
18. **ISSUE-21:** No learning loop from failures
19. **ISSUE-05:** Schema validation only runs on examples, not live packets
20. **ISSUE-17:** No hard scope boundaries
21. **ISSUE-19:** Spec-to-code traceability is aspirational
22. **ISSUE-11:** Pretool hook limited vocabulary

## Low Priority

23. **ISSUE-06:** Scratchpad isolation unenforced
24. **ISSUE-18:** Run artifacts have no concurrency safety
25. **ISSUE-23:** Skill trigger accuracy untested
26. **ISSUE-25:** Frontend verification not wired into routing metadata
