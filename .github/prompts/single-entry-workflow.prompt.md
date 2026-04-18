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

# Single-Entry Workflow

Use the default orchestrator as a thin wrapper for this task.
Keep the work in one conversation and let the orchestrator own the generic workflow,
critique loop, and verification discipline.

For this task:
- treat `.github/agent-platform/workflow-manifest.json`, `.github/agent-platform/repo-map.json`,
  `.github/agent-platform/skill-registry.json`, and
  `.github/agent-platform/context-packet.schema.json` as the canonical control-plane layer
- use existing requirement sources before inventing a new plan
- create or refresh an active spec before code when the work is non-trivial
- keep workflow docs and metadata aligned in the same change set when control-plane behavior changes
- state assumptions and proceed unless a blocking ambiguity remains

<goal>{{task}}</goal>
<constraints>{{constraints}}</constraints>
<done_when>{{done_when}}</done_when>
<context_packet>
  <goal_anchor>{{task}}</goal_anchor>
  <current_step id="classify-and-route">
    <objective>Classify the task, build the atomic task DAG, and define the first executable subtask with bounded context.</objective>
    <input_contract>{{context}}</input_contract>
    <output_contract>Task classification, first-step routing, and a bounded current-step packet.</output_contract>
    <done_condition>The first executable subtask is ready without carrying more context than needed.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: {{task}}</self_check>
</context_packet>
<supporting_context>{{context}}</supporting_context>
