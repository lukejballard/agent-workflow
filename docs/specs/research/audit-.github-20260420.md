# Adversarial Audit · Surface: `.github/` · 2026-04-20

## Executive Summary

This is the first adversarial audit of the `.github/` agent-workflow package.
Evidence collected: 65 session-log entries, 5 memory entries, 11 eval scenarios,
69 unit tests, full git status, and 4 hook files read. The audit found **5
illusory capabilities**, **3 partially-real capabilities**, and **5 Phase-1
critical fixes** all shippable in one PR. The system has strong gate coverage
in tests but weak runtime observability — the mechanism exists but the wiring
between mechanism and trigger is mostly absent. No capability is both
fully-enforced AND exercised in practice during a real session.

---

## Per-Dimension Analysis

### 1. Reasoning Depth — **5 / 10**

The orchestrator prose (`.github/agents/orchestrator.agent.md`) correctly
articulates fact-vs-assumption discipline, critique cycles, and the R1–R15
checklist. However, the live session shows `current_phase: goal-anchor` for
the entire audit-evidence-gathering conversation (65 tool calls, 0 phase
transitions). `critique_results` in `session.json` is empty. The schema has
typed, validated `CritiqueResult` entries but no session in the log has ever
recorded one. The rubric exists on paper; in practice the agent stays at
`goal-anchor` indefinitely.

**Citations:**
- `.github/hooks/session_schema.py:SCHEMA_VERSION=5` — CritiqueResult defined
- `~/.agent-session/session.log.jsonl` — 18 recent entries: all `phase_advisory`
  or `budget_exceeded`, zero `critique_*` events

### 2. Research Ability — **4 / 10**

`researchBriefPolicy` exists in the manifest with `requiredWhen` conditions.
`docs/specs/research/README.md` was extended with `## When a brief is required`.
But zero research briefs exist in `docs/specs/research/` (directory contains
README and five prior briefs all pre-dating this session). The posttool logs
`research_brief_skipped` only if `state.research_brief_required` is truthy —
a field that (a) never appears in `SessionState` and therefore (b) is always
falsy, silently suppressing the gate.

**Citations:**
- `docs/specs/research/` — directory listing confirms no audit-period briefs
- `.github/hooks/session_schema.py` — `research_brief_required` absent from
  `@dataclass SessionState`
- `.github/agent-platform/workflow-manifest.json:researchBriefPolicy`

### 3. Code Quality (Backend) — **7 / 10**

Hook code is clean: typed dataclasses, atomic writes (msvcrt/fcntl), minimal
imports, no unbounded waits, no N+1. Three concrete gaps:

1. `research_brief_required` missing from `SessionState` (see above).
2. `revise` phase not skipped for `docs-only` task class — if `adversarial-critique`
   is skipped, `revise` (which operates on critique output) has nothing to act on.
   `PHASE_SKIP_RULES["docs-only"]` = `{"adversarial-critique", "self-review",
   "critique"}` but not `"revise"`. (`phase_engine.py:PHASE_SKIP_RULES`)
3. `FailureIndex._failures_dir()` returns `Path(__file__).parent / "failures"`
   (`.github/hooks/failures/`), but `session.json` lives at `~/.agent-session/`.
   Failure records would land in-repo and be committed. Neither path appears in
   `.gitignore`. (`failure_index.py:_failures_dir`)

**Citations:**
- `.github/hooks/phase_engine.py:PHASE_SKIP_RULES`
- `.github/hooks/failure_index.py:_failures_dir`
- `.github/hooks/session_io_support.py:default_session_path`

### 4. Code Quality (Frontend) — **N/A**

No frontend code in this package.

### 5. UI/UX Intelligence — **N/A**

No UI components.

### 6. System Design — **6 / 10**

Package boundary (`.github/` only) is explicit and tested. Single-entry
workflow via `@orchestrator` is correctly specified. Key gap: the session state
file resolves to `~/.agent-session/session.json` (user home, shared across ALL
workspaces for the same user — see `session_io_support.py:default_session_path`).
If two VS Code windows open different workspaces simultaneously, they share one
session file with no isolation. `AGENT_SESSION_FILE` env can override this but
there is no mechanism to set it per-workspace automatically.

Cross-workspace contamination evidence: `tool_call_count = 62` at the start of
this conversation — carried from the prior conversation's brownfield task.
`current_phase = goal-anchor` also carried from prior session with `task_class`
blank. `reset_for_new_task()` exists in the schema but is never called between
sessions.

**Citations:**
- `~/.agent-session/session.json: {"tool_call_count": 62, "current_phase": "goal-anchor"}`
- `.github/hooks/session_io_support.py:default_session_path`
- `.github/hooks/session_schema.py:reset_for_new_task`

### 7. Execution Reliability — **3 / 10**

The most critical dimension. Four compounding failures:

**A. Tool-call-limit gate fires but yields (auto-approved)**
`budget_exceeded` events in the log begin at count=57 and appear on every
subsequent tool call (57, 57, 58, 59, 60, 61, 62, 63, 64, 65). VS Code
renders the `additionalContext` as `<PreToolUse-context>…</PreToolUse-context>`
appended to every tool output, but execution continues. The gate emits "ask"
and the VS Code agent mode auto-approves it. Gate is logged, never enforced.

**B. Phase never advances**
`phase_advisory` fires on every tool call suggesting `execute-or-answer`, but
the posttool only logs the advisory — it never writes the new phase back.
`current_phase` stays at `goal-anchor` for the entire 65-call conversation.

**C. FailureIndex never written**
The `failures/` directory under `.github/hooks/` does not exist. Zero call to
`FailureIndex().write()` in the posttool code path — the only write trigger
would be when `verification_status` transitions to `blocked`, but that branch's
write call was described in the summary but does not appear in the posttool
source as read:

```python
# posttool_validator.py (read) — no FailureIndex().write() call present
```

Checking posttool source: the posttool sets `state.audit_due = True` and logs
`audit_required` but never calls `FailureIndex().write()`. This is missing
wiring, not a missing function.

**D. Audit cadence never fires**
`audit_due` is set by posttool when entering `traceability-and-verify`. But
`traceability-and-verify` is never entered (phase stuck at `goal-anchor`). Zero
`audit_required` or `audit_due` events appear in the session log.

**Citations:**
- `~/.agent-session/session.log.jsonl` — `budget_exceeded` events at counts 57–65
- `.github/hooks/posttool_validator.py` — no `FailureIndex().write()` call in file
- `~/.agent-session/session.json` — `audit_due: false`

### 8. Testing Rigor — **8 / 10**

69/69 unit tests pass. Eval harness 11/11 gates verified at `pass_rate=1.0`
(`run_at: 2026-04-21T00:38:08`). New `audit_trigger.py` has dedicated 10-test
suite. `conftest.py` isolation is correct. One gap: no test for `reset_for_new_task()`
being called between conversations, because the call itself is absent (so the
test would trivially pass as "the session carries over").

**Citations:**
- `.github/hooks/tests/eval_results.json: pass_rate=1.0`
- pytest run: 69 passed in 1.05s

### 9. Security Awareness — **6 / 10**

Sensitive-path gate covers hook files, audit charter, research dir, manifest —
all tested. No secrets hardcoded. No SQL/injection surfaces in the Python code.
One finding:

**Prompt-injection channel via `additionalContext`**: The pretool hook's "ask"
response for `budget_exceeded` produces `additionalContext` text that VS Code
injects as `<PreToolUse-context>…</PreToolUse-context>` into **all subsequent
tool outputs**. If the pretool ever constructs `additionalContext` from repo
file content (e.g., future feature reading task descriptions from an issue
body), that content would appear in a trusted channel that the LLM reads as
tool output. The current text is hardcoded ("Override the limit with
AGENT_MAX_TOOL_CALLS…") and not exploitable, but the pattern is a latent
surface. Flagged as WARN.

**Citations:**
- `.github/hooks/pretool_approval_policy.py:emit_pretool_decision`
- All terminal tool outputs in this session showing `<PreToolUse-context>` injection

### 10. DevOps Capability — **4 / 10**

`.gitignore` was created but is **untracked** (`?? .gitignore` in `git status`).
Four new key files are also untracked (`audit_trigger.py`, `test_audit_trigger.py`,
`docs/runbooks/adversarial-audit.md`, `.gitignore`) — they exist on disk but
have never been `git add`ed. Twelve pyc files are **staged for deletion** but
not committed. All 30+ modified/new files from the previous brownfield session
are uncommitted.

`failures/` path (`.github/hooks/failures/`) is not in `.gitignore` — if a
failure record is ever written, it will appear as an untracked file that a
naive `git add .` would commit.

Commit messages: 10 most recent commits use no conventional format ("Pushed
adjustments", "Removed uneeded files", "Fixed/refined prompts"). No issue
references, no semantic prefixes.

**Citations:**
- `git status --short` — 34 modified/untracked/deleted lines
- `git log --oneline -10` — non-semantic messages
- `.gitignore` — no entry for `.github/hooks/failures/`

### 11. Learning Ability — **1 / 10**

The `FailureIndex` has zero records. `failures/` directory does not exist.
`FailureIndex.recent(50)` called at bootstrap Phase 0 returns no matches
(correctly, since there's nothing to match). The TF-IDF retrieval layer is
correctly implemented and tested but has no data to retrieve.

Memory entries (`session.memory.jsonl`, 5 entries) show shallow content:
- 4 of 5 entries: `"decisions":"","unresolved":"","artifacts":"","verification":"pending"` — empty
- 1 entry (the last, from Phase 3 brownfield task): has `facts_learned` and
  `corrections_applied` content but was written manually by the orchestrator,
  not by the posttool hook's memory write (which writes empty stubs)

**Citations:**
- `~/.agent-session/session.memory.jsonl` — 5 entries, 4 empty
- `.github/hooks/failure_index.py` — `_failures_dir()` returns non-existent path

### 12. Self-Improvement — **6 / 10**

This is the first audit, so no prior Phase-1 fixes to track. Scoring on proxy:
14/14 deliverables from the brownfield spec shipped (working tree); schema
advanced v3→v5; phase skip rules, audit machinery, R1–R15 rubric, and business-user
gate all added as specified. No regression in tests.

Deduction: deliverables exist on disk but not in git; `reset_for_new_task()`
added but never called; `FailureIndex.write()` path added in posttool comments
but not implemented.

---

## Failure-Mode Probes

### Probe 1: Complex multi-step task with implicit dependencies
**Reproduction:** Brownfield task above (14 deliverables). `session.json` carried
prior `tool_call_count=62` into the new task with no reset. Phase stayed at
`goal-anchor` throughout. No requirements lock was written to session state.
**Gate that failed:** `requirements_lock_gate` — didn't fire because `task_class`
was also blank (carried from prior session's blank value).
**Classification:** logic-defect — `reset_for_new_task()` exists but is never called.

### Probe 2: Ambiguous requirements with conflicting signals
**Reproduction:** Not directly observed. The orchestrator prose says to repair
gaps. No evidence this was tested under adversarial conditions.
**Gate:** `requirements-lock` gate — partially-real (fires when task_class is
set, but task_class is often blank from session contamination).
**Classification:** missing-context.

### Probe 3: Long-running multi-session workflow
**Reproduction:** This audit conversation itself. `tool_call_count=65`, all at
or past the limit of 50. Every tool call fires `budget_exceeded` ask. Every
ask is auto-approved.
**Gate failed:** `tool-call-limit` — emits ask, not deny; VS Code auto-approves.
**Classification:** logic-defect — gate decision should escalate to deny after
repeated auto-approvals, or use a hard cap enforced differently.

### Probe 4: Prompt injection in repo files
**Reproduction:** The pretool's `additionalContext` string "Override the limit
with AGENT_MAX_TOOL_CALLS when the task is genuinely large." appears in
`<PreToolUse-context>` tags injected into every tool output. The source is
hardcoded (safe). If a future enhancement populates `additionalContext` from
user-controlled content (task description, issue body), the injection channel
is live.
**Gate:** No gate exists for this surface.
**Classification:** transient-environment (low severity, currently benign).

### Probe 5: Missing environment variable
**Reproduction:** Session file path defaults to `~/.agent-session/session.json`.
If the `AGENT_SESSION_FILE` env var is absent (it always is, as nothing sets it),
the session is shared globally across all workspaces.
**Gate:** None.
**Classification:** logic-defect.

---

## Architectural-Weakness Probes

### Structure-without-enforcement inventory

| Prose rule | Enforcement mechanism | Status |
|---|---|---|
| "On the next session bootstrap, read `state.audit_due` first" | No hook reads `audit_due` on bootstrap | **Illusory** |
| `reset_for_new_task()` between sessions | Method exists; never called | **Illusory** |
| `FailureIndex().write(...)` on blocked | Code absent from posttool | **Illusory** |
| Phase advances through canonical loop | Posttool advisory only; never writes | **Illusory** |
| Research brief when requiredWhen fires | Schema field absent; gate suppressed | **Illusory** |
| Critique results written after execute-or-answer | `critique-fail` gate; but results always empty | **Partially-real** |
| Token budget gate | Fires, logs, asks; auto-approved | **Partially-real** |
| Tool-call-limit gate | Fires, logs, asks; auto-approved | **Partially-real** |
| `verification_matrix_present` logged when missing | Posttool logs warning | **Partially-real** |
| Phase gate blocks edits in read-only phases | Tested in eval harness; fires correctly | **Fully-real** |
| Sensitive-path gate | Tested; fires correctly | **Fully-real** |
| Requirements-lock gate | Tested; fires correctly (when task_class set) | **Fully-real** |
| Confidence gate | Tested; fires correctly | **Fully-real** |
| Critique-fail gate | Tested; fires when critique_results has FAIL | **Fully-real** |
| Destructive command gate | Tested; fires correctly | **Fully-real** |

### Misleading abstractions

- **"Episodic memory"** — described as rich cross-session learning store; in
  practice, 4 of 5 entries are empty stubs. The posttool writes a memory entry
  on every phase transition but only populates `summary`, not
  `facts_learned`/`corrections_applied`. The rich format is only produced when
  the orchestrator manually calls `append_memory()`.
- **"Failure index search"** — called at Phase 0 for every task; TF-IDF
  retrieval is correctly implemented; the corpus is empty. Returns no results
  always.

### Model-instead-of-mechanism reliance

- Phase advance: trusted entirely to the LLM calling `declare_phase()`. No hook
  enforces the canonical loop order.
- Research brief creation: trusted entirely to the LLM reading the manifest
  policy. No gate checks.
- Reset between sessions: trusted entirely to the LLM calling `reset_for_new_task()`.
  No automatic trigger.

---

## Capability Classification

| Capability | Classification |
|---|---|
| Phase gate (read-only phases block edits) | Fully-real |
| Sensitive-path gate | Fully-real |
| Requirements-lock gate | Fully-real (when task_class is set) |
| Confidence gate | Fully-real |
| Critique-fail gate | Fully-real |
| Destructive command gate | Fully-real |
| Token budget gate | Partially-real |
| Tool-call-limit gate | Partially-real |
| Phase advisory (posttool detect_phase) | Partially-real |
| Verification matrix presence check | Partially-real |
| Session reset between tasks | Illusory |
| Failure index accumulation | Illusory |
| Audit cadence trigger | Illusory |
| Rich episodic memory | Illusory |
| Research brief policy enforcement | Illusory |

---

## Superintelligence Gap

**Distance from goal (plain language):** The system has excellent gate coverage
for preventing bad edits (phase, scope, sensitive-path, requirements-lock). It
has essentially zero machinery for the *learning and adaptation* half of the
mandate. 5 of 15 capabilities are illusory. The session does not reset between
conversations, the failure index is empty, memory entries are stubs, and no phase
ever advances beyond `goal-anchor` in the live runtime.

### Top 5 bottlenecks by leverage

1. **Session cross-contamination** (`session_io_support.py:default_session_path`)
   Cheapest fix: add `AGENT_SESSION_FILE` to the `.github/hooks/pretool-approval-policy.json`
   environment block using a workspace-fingerprinted path:
   ```json
   "env": {"AGENT_SESSION_FILE": "${workspaceFolder}/.agent-session/session.json"}
   ```
   This makes each workspace get its own session. One-line JSON change.

2. **FailureIndex never written** (`posttool_validator.py:main`)
   The blocked-transition branch sets `state.audit_due = True` and logs
   `audit_required` but never calls `FailureIndex().write()`. Add 6 lines:
   ```python
   FailureIndex().write(
       task_class=state.task_class or "unknown",
       phase_at_failure=state.current_phase,
       symptom="verification_status transitioned to blocked",
       root_cause="",
       task_summary=state.scope_justification,
   )
   ```

3. **Phase never advances** (`posttool_validator.py:main`)
   `detect_phase()` correctly infers the phase but only logs an advisory.
   Add automatic phase commit for forward-only transitions:
   ```python
   if PHASE_INDEX.get(detected, -1) > state.phase_index:
       state.current_phase = detected
       state.phase_index = PHASE_INDEX[detected]
       append_log("phase_auto_advance", {"from": old_phase, "to": detected})
   ```

4. **`reset_for_new_task()` never called** (`session_schema.py`)
   With workspace-isolated sessions (fix #1), this becomes less critical. But
   `reset_for_new_task()` should still be called when `current_phase` resets to
   `goal-anchor` after a `traceability-and-verify` close. The posttool should
   detect this state: if `current_phase = traceability-and-verify` and
   `verification_status` becomes `verified`/`partially-verified`, write a fresh
   session via `state.reset_for_new_task()`.

5. **`research_brief_required` missing from schema** (`session_schema.py`)
   Add field to `SessionState`, add `validate()` check, add v5→v6 migration.
   One field addition. Without it, the research-brief gate is permanently silenced.

---

## Upgrade Roadmap

### Phase 1 — Critical fixes (one PR)

| Fix | File | Effort |
|---|---|---|
| Add `AGENT_SESSION_FILE` workspace env to pretool-approval-policy.json | `.github/hooks/pretool-approval-policy.json` | 3 lines |
| Wire `FailureIndex().write()` in posttool blocked-transition branch | `.github/hooks/posttool_validator.py` | 6 lines |
| Auto-advance phase in posttool for forward-only transitions | `.github/hooks/posttool_validator.py` | 8 lines |
| Add `research_brief_required` to `SessionState` + validate + migration | `.github/hooks/session_schema.py` | 10 lines |
| Add `docs/runbooks/` and `.github/hooks/failures/` to `.gitignore` | `.gitignore` | 2 lines |
| `git add` all untracked new files and commit | git | 1 commit |
| Skip `revise` phase for `docs-only` task class | `.github/hooks/phase_engine.py` | 1 line |

### Phase 2 — Capability expansion

- Posttool: escalate `tool-call-limit` gate from "ask" to "deny" after 3
  consecutive auto-approvals (needs a counter in session state).
- Posttool: call `reset_for_new_task()` when `verification_status` transitions
  to `verified` and `current_phase = traceability-and-verify`.
- Posttool memory write: populate `facts_learned` from `critique_results` and
  `allowed_paths` instead of empty stubs.
- Add `research_brief_required` gate to pretool: block `traceability-and-verify`
  entry if `state.research_brief_required` and no brief file found.

### Phase 3 — Superintelligence path

- Workspace-fingerprinted session paths (derived from git remote URL or
  workspace folder hash), removing the need for manual `AGENT_SESSION_FILE` env.
- TF-IDF search across failure records AND memory entries for richer Phase 0
  context injection.
- Per-task commit reference: store `git rev-parse HEAD` in each task's session
  close entry for traceability.
- Conventional commit enforcement on the agent's output: require semantic
  prefix when suggesting commit messages.

---

## Final Scorecard

| Dimension | Score | Rationale | Citation |
|---|---|---|---|
| Reasoning Depth | 5 | Prose correct; session shows zero phase transitions or critique results | `session.log.jsonl` |
| Research Ability | 4 | Policy written; `research_brief_required` field absent; zero briefs created | `session_schema.py`, `docs/specs/research/` |
| Code Quality (Backend) | 7 | Clean hooks; 3 concrete gaps (schema field, phase skip, failures path) | `failure_index.py`, `phase_engine.py` |
| Code Quality (Frontend) | N/A | No frontend | — |
| UI/UX Intelligence | N/A | No UI | — |
| System Design | 6 | Clear boundary; session cross-workspace contamination is structural | `session_io_support.py` |
| Execution Reliability | 3 | 5 of 5 failure modes confirmed; 3 of 5 illusory capabilities in this dimension | `session.log.jsonl` |
| Testing Rigor | 8 | 69/69 + 11/11; gap is session-reset coverage | `eval_results.json` |
| Security Awareness | 6 | Sensitive-path gate solid; one latent injection channel; no secrets | `pretool_approval_policy.py` |
| DevOps Capability | 4 | Atomic writes solid; 34 uncommitted changes; commit messages non-semantic | `git status` |
| Learning Ability | 1 | Zero failure records; 4/5 memory stubs empty; FailureIndex corpus size=0 | `failure_index.py`, `session.memory.jsonl` |
| Self-Improvement | 6 | 14/14 spec deliverables on disk; wiring gaps in 3 of 14 | `git status` |

**Overall (equal-weighted across 10 applicable dimensions):** **5.5 / 10**

**Confidence: moderate.** Evidence is direct (session log, git status, file
reads, test output). Sample size: 1 brownfield session, 65 tool calls, 5 memory
entries. Gaps: no prior audit to compare against; no cross-task failure record;
no frontend or database surfaces to assess.

---

## Meta-Critique

**What this audit over-stated:**
- Gave learning ability 1/10 as if the code is wrong. The code is correct; the
  problem is zero data. One session of real failures would make the failure index
  useful immediately. The true score on *potential* is 7; on *current state* it is 1.

**What this audit under-stated:**
- The gate coverage in the eval harness is genuinely strong. 11 distinct gate
  scenarios all tested and passing is a real capability. The score for Testing
  Rigor (8) might be understated — most teams ship with 0 gate tests.
- The brownfield task completion (14/14 deliverables, all tested) demonstrates
  high execution quality even if those changes are not committed.

**Systematic bias:**
This audit was conducted *during the conversation that implemented the deliverables
it is auditing*. The session log includes evidence of the implementation work
(budget_exceeded events from the 65-tool prior conversation). A cleaner audit
would run on a fresh session with a clean slate. The session-contamination finding
(tool_call_count=62 on entry) is a direct consequence of this bias — a human
reviewer would have noticed and reset between sessions.

**Revised confidence: moderate-low.** The structural findings (illusory
capabilities, session contamination, FailureIndex unwired) are solid. The
scoring of partially-real gates may be too harsh — "auto-approved ask" in VS Code
agent mode may be intentional UX, not a gate failure.

---

*Produced by `@orchestrator audit .github/` · 2026-04-20 · Subject to R1–R15*
