---
agent: orchestrator
tools:
  - read
  - search
  - github/*
  - fetch/*
---

# Research-First Workflow

Use the default orchestrator as a thin research-first wrapper.

For this task:
- use the researcher fallback pattern only when external research dominates the task
- scan broadly first, then go deep on the highest-signal sources
- save a brief to `docs/specs/research/<slug>-research.md` when outside references materially shape the work
- be explicit about missing whole-web search or credential setup instead of implying it exists
- keep the final research brief clear about verified findings versus inference

---
Feature or topic: {{topic}}
Specific questions to answer: {{questions}}

<context_packet>
  <goal_anchor>{{topic}}</goal_anchor>
  <current_step id="research-classify-and-route">
    <objective>Break the research ask into bounded questions, scan broadly, and keep only the highest-signal source cluster in active context.</objective>
    <input_contract>Topic: {{topic}}. Questions: {{questions}}</input_contract>
    <output_contract>A bounded first research packet with source plan, routing, and context-health status.</output_contract>
    <done_condition>The first research node is ready without dragging the full source set into working memory.</done_condition>
  </current_step>
  <self_check>Before responding, verify your output directly addresses: {{topic}}</self_check>
</context_packet>
