---
applyTo: "**/*.py,**/*.ts,**/*.tsx"
---

# Tool usage contracts

## General tool rules
- Read before writing. Never edit a file you have not read in this session.
- Use the right tool for the job: `grep_search` for exact text, `semantic_search` for concepts, `file_search` for paths.
- Do not call the same tool with the same arguments twice. If the first call failed, change the approach.
- Do not run destructive terminal commands (`rm -rf`, `git reset --hard`, `git clean`) without explicit user approval.

## Read tools
**Expected behavior**: Return file contents or search results.
- `read_file`: Returns file content for specified line range. Use large ranges to minimize calls.
- `grep_search`: Returns exact text matches. Use regex alternation for multiple patterns.
- `semantic_search`: Returns conceptually relevant code. Do not call in parallel.
- `file_search`: Returns file paths matching a glob pattern.
- `list_dir`: Returns directory contents.

**Failure handling**:
- File not found → check the path, try `file_search` to locate the correct file.
- Empty results → broaden the search pattern or try a different tool.
- Truncated output → narrow the line range or use more specific queries.

## Edit tools
**Expected behavior**: Modify file contents.
- `replace_string_in_file`: Replace one exact occurrence. Include 3+ lines of context.
- `multi_replace_string_in_file`: Batch multiple replacements. Prefer over sequential single replacements.
- `create_file`: Create a new file. Never use on existing files.

**Failure handling**:
- Match not found → re-read the file to get the current content, then retry with corrected text.
- Multiple matches → add more context lines to make the match unique.
- Do not retry the same failed edit more than once without changing the approach.

## Terminal tools
**Expected behavior**: Execute commands and return output.
- `run_in_terminal`: Run shell commands. Use `mode=sync` for short commands, `mode=async` for long-running processes.

**Failure handling**:
- Command fails → read the error output, diagnose, and fix before retrying.
- Command hangs → use `get_terminal_output` to check async terminals.
- Never retry the same failed command without changing arguments or approach.
- Never use `Start-Sleep` or similar wait commands.

## Tool call budget
- The total tool call budget per session defaults to 50.
- If you approach the limit, the hooks will flag it.
- Reduce tool calls by: reading larger file ranges, batching edits, using specific search queries.

## Timeout handling
- All tool calls have implicit timeouts.
- If a tool call times out, do not immediately retry. Consider whether the operation is appropriate for the tool.
- For long-running builds or test suites, use async terminal mode.

## Malformed input handling
- If a tool returns unexpected output (empty, garbled, wrong format), log the issue and try an alternative approach.
- Do not pass tool output directly to another tool without inspecting it first.
- Treat unexpected tool output as a signal to re-examine your approach, not just retry.
