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

# Bugfix Workflow

Use the default orchestrator as a thin bugfix wrapper.

For this task:
- capture repro evidence before committing to a fault line
- prefer a root-cause fix over a surface patch
- add or update regression coverage for the broken path and its closest neighboring flow
- avoid unrelated refactors unless they are required to fix the bug safely
- apply `frontend-best-practices` and `visual-qa` for user-facing UI bugs

<goal>Fix the bug affecting {{target}}</goal>
<constraints>{{constraints}}</constraints>
<done_when>{{done_when}}</done_when>
<context_packet>
  <goal_anchor>Fix the bug affecting {{target}}</goal_anchor>
  <current_step id="bugfix-classify-and-route">
    <objective>Capture the reproducer, build the atomic investigation DAG, and isolate the first fault-line subtask.</objective>
    <input_contract>Symptoms: {{symptoms}}. Supporting context: {{context}}</input_contract>
    <output_contract>A bounded first-step packet with repro evidence, likely fault line, and explicit route.</output_contract>
    <done_condition>The first executable bugfix subtask is defined and stale context has been trimmed.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: Fix the bug affecting {{target}}</self_check>
</context_packet>