---
agent: orchestrator
tools:
  - read
  - search
  - edit
  - execute
  - browser
  - sequential-thinking/*
  - github/*
  - fetch/*
---

# Brownfield Improvement Workflow

Use the default orchestrator as a thin brownfield wrapper.
Goal: higher quality, better safety, and cleaner reasoning in one conversation.

For this task:
- analyse the current code, tests, coupling, docs, and risks before changing behavior
- prefer an OpenSpec change when the work is non-trivial, then refresh an active spec before code
- compare the preferred improvement with a smaller or safer alternative
- apply `test-hardening`, `regression-audit`, and `adversarial-review` before finalizing
- use `observability-inject` only when the target surface needs more signal

---
<goal>{{goal}}</goal>
<constraints>{{constraints}}</constraints>
<done_when>{{done_when}}</done_when>
<context_packet>
  <goal_anchor>{{goal}}</goal_anchor>
  <current_step id="brownfield-classify-and-route">
    <objective>Map the target module, classify the improvement, and build the first atomic brownfield subtask.</objective>
    <input_contract>Target module: {{target_path}}. Supporting context: {{context}}.</input_contract>
    <output_contract>A bounded first-step packet with explicit routing, risk focus, and regression-sensitive context only.</output_contract>
    <done_condition>The first executable brownfield subtask is ready with explicit contracts and local scratchpad scope.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: {{goal}}</self_check>
</context_packet>
