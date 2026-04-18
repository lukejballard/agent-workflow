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

# Greenfield Feature Workflow

Use the default orchestrator as a thin greenfield wrapper.
Keep the work in one conversation.

For this task:
- use `feature-discovery` if the idea is vague
- prefer Speckit artifacts before refreshing an active spec
- compare the preferred approach with at least one viable alternative
- run `spec-validation`, `adversarial-review`, and `requirements-traceability` before finalizing
- apply `observability-inject` when new services, endpoints, jobs, or important code paths are added

---
<goal>{{feature_idea}}</goal>
<constraints>{{constraints}}</constraints>
<done_when>{{done_when}}</done_when>
<context_packet>
  <goal_anchor>{{feature_idea}}</goal_anchor>
  <current_step id="greenfield-classify-and-route">
    <objective>Clarify the feature, build the delivery DAG, and define the first discovery or planning node.</objective>
    <input_contract>{{context}}</input_contract>
    <output_contract>A bounded first-step packet with upstream planning path, routing, and explicit contracts.</output_contract>
    <done_condition>The first executable greenfield subtask is ready with bounded context.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: {{feature_idea}}</self_check>
</context_packet>
<supporting_context>{{context}}</supporting_context>
