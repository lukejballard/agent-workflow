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
---

# Test Generation

Use the default orchestrator as a thin test-shaping wrapper for: {{target}}

Stack: {{stack}}

For this task:
- use an active spec as the source of truth when available
- apply `test-hardening` and `requirements-traceability`
- apply `regression-audit` when existing behavior could drift
- cover happy path, failure paths, edge cases, auth boundaries, and neighboring regression risk
- report the verified coverage delta and any gaps you could not cover

<goal>Add or improve tests for {{target}}</goal>
<context_packet>
  <goal_anchor>Add or improve tests for {{target}}</goal_anchor>
  <current_step id="test-classify-and-route">
    <objective>Break the target into atomic test cases and keep only the current case design in working memory.</objective>
    <input_contract>Target: {{target}}. Stack: {{stack}}.</input_contract>
    <output_contract>A bounded first test-case packet with explicit coverage goal and route.</output_contract>
    <done_condition>The first test node is ready and stale case notes are trimmed.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: Add or improve tests for {{target}}</self_check>
</context_packet>
