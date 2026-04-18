---
agent: orchestrator
tools:
  - read
  - search
  - browser
  - sequential-thinking/*
  - github/*
  - fetch/*
---

# Launch-Readiness Audit

Use the default orchestrator as a thin launch-audit wrapper.

For this task:
- findings come first and are ordered by severity
- include launch blockers, onboarding friction, time-to-value risks, and quick wins
- use external references only when they materially change the conclusion
- keep the analysis scoped to the highest-signal risk clusters first

<goal>{{goal}}</goal>
<constraints>{{constraints}}</constraints>
<done_when>{{done_when}}</done_when>
<context_packet>
  <goal_anchor>{{goal}}</goal_anchor>
  <current_step id="launch-audit-classify-and-route">
    <objective>Map launch-readiness surfaces, rank the risk clusters, and keep only the first cluster in active context.</objective>
    <input_contract>Audience: {{audience}}. Supporting context: {{context}}</input_contract>
    <output_contract>A bounded first audit packet with severity criteria and explicit risk-cluster routing.</output_contract>
    <done_condition>The first launch-readiness risk cluster is ready for review without carrying every scanned surface live.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: {{goal}}</self_check>
</context_packet>
<supporting_context>{{context}}</supporting_context>