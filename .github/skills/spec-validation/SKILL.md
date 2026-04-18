# Spec Validation Skill

## When to use
Run this on every spec before handing it to the implementer.
A spec that fails validation will produce implementation drift, ambiguous code,
and incomplete tests. Fix the spec, not the code.

## Validation checklist

### Completeness
- [ ] Problem statement is clear and specific (not "improve UX")
- [ ] All functional requirements are stated as concrete behaviours
- [ ] All non-functional requirements are stated (performance, security, accessibility)
- [ ] External context is captured or explicitly declared unnecessary when outside references matter
- [ ] Documentation impact is captured or explicitly declared unchanged
- [ ] API design includes: method, path, auth requirement, full request schema, full response schema
  for BOTH success and every error case
- [ ] Data model changes list every new column, type, nullability, and default value
- [ ] Every edge case from the requirements has a defined handling strategy
- [ ] Testing strategy specifies what will be unit tested, integration tested, and E2E tested
- [ ] All acceptance criteria are checkboxes, not prose

### Ambiguity check
- [ ] No requirement uses vague language: "fast", "secure", "user-friendly", "handle errors"
  without defining what that means quantitatively or behaviourally
- [ ] Every external dependency is named and its contract is described
- [ ] Authorisation rules are explicit: which roles can perform which actions

### Safety check (brownfield only)
- [ ] Breaking changes are explicitly identified
- [ ] Migration path for existing data is described
- [ ] Rollback plan is present if the change involves a schema migration

### Size check
- [ ] If complexity estimate is XL, the spec is flagged for breakdown
- [ ] Each acceptance criterion can be implemented and verified independently

## Output
- PASS: list of confirmed items
- FAIL: list of gaps with specific questions the planner must answer before the spec is valid
