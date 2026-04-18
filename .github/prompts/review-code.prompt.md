---
agent: orchestrator
tools:
  - read
  - search
  - github/*
---

# Code Review

Use the default orchestrator as a thin review-only wrapper for an independent
adversarial review of the changes at {{target}} (file path, PR number, or branch).

For this task:
- findings come first and are ordered by severity
- apply `requirements-traceability` to the review scope
- issue a PASS or REJECT decision at the top for implementation reviews
- separate required changes from optional improvements

<goal>Review the changes at {{target}}</goal>
<context_packet>
  <goal_anchor>Review the changes at {{target}}</goal_anchor>
  <current_step id="review-classify-and-route">
    <objective>Map the changed surfaces, group them into risk clusters, and keep only the highest-risk cluster in working memory.</objective>
    <input_contract>{{context}}</input_contract>
    <output_contract>A bounded review packet with severity-focused findings and explicit next risk cluster.</output_contract>
    <done_condition>The first risk cluster is ready for review without dragging the full diff history into active context.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: Review the changes at {{target}}</self_check>
</context_packet>
<supporting_context>{{context}}</supporting_context>
