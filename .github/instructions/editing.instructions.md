---
applyTo: "**/*.py,**/*.ts,**/*.tsx,**/*.jsx,**/*.json,**/*.md"
---

# Editing discipline

## Minimal-diff principle
Every edit must change the smallest region necessary to satisfy the requirement.
Prefer adding or modifying specific lines over rewriting whole files or functions.

## Brownfield rules
When modifying existing code (brownfield):
- Read the file before editing. Never edit blind.
- Preserve existing formatting, naming, and structural conventions.
- Change only the lines required by the task. Do not reformat, rename, or restructure adjacent code.
- If a large rewrite is genuinely necessary, state the justification before performing it.
- Never delete code paths, tests, or configuration you do not fully understand.

## SEARCH/REPLACE preference
- For targeted changes, prefer `replace_string_in_file` or `multi_replace_string_in_file` over full file rewrites.
- Include at least 3 lines of unchanged context before and after the target text to anchor the edit.
- For multiple independent edits in the same file or across files, batch them in `multi_replace_string_in_file`.

## Prohibited patterns
- Do not rewrite a file to change one function.
- Do not add docstrings, comments, or type annotations to code outside the changed region.
- Do not refactor or "improve" code adjacent to the change unless the requirement demands it.
- Do not introduce new abstractions, helpers, or wrappers for one-time operations.
- Do not delete unfamiliar files or tests without explicit confirmation.

## Greenfield exceptions
When creating new files (greenfield):
- Full file creation via `create_file` is expected and acceptable.
- Follow the project's existing naming, layout, and import conventions.
- Do not create barrel files, index files, or re-export modules unless the surrounding code already uses them.

## Verification after edits
- After non-trivial edits, run the relevant tests or compile checks.
- If a test fails after an edit, fix the implementation first, not the test, unless the test assertion itself is wrong.
