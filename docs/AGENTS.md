# AGENTS.md — docs/

This file provides agent guidance scoped to **documentation** (`docs/`).

---

## Document inventory

| File | Owner | Update when… |
|---|---|---|
| `docs/architecture.md` | Engineering | A new component, endpoint, or table is added |
| `docs/quickstart.md` | Engineering | The startup process or example commands change |
| `docs/roadmap.md` | Maintainers only | A milestone is completed or a new one is planned |
| `docs/copilot-setup.md` | Engineering | The Copilot/agent setup changes |
| `docs/images/` | Engineering | Real screenshots replace placeholder files |

---

## Agent rules

1. **Do not invent information.** If a behaviour is not confirmed by the source code, mark it as `TODO` or omit it.
2. **Keep quickstart commands runnable.** Test any new command you document against the actual code.
3. **Update architecture docs alongside code.** If you add an API endpoint, update the endpoint table in `architecture.md` in the same commit.
4. **No speculation in roadmap.** Only update `roadmap.md` if explicitly asked to.
5. **Plain language.** Avoid jargon; write for a developer who has never seen the repo.

---

## Markdown style checklist

- [ ] H1 used only for the document title (one per file).
- [ ] Code blocks have a language tag (` ```python`, ` ```bash`, etc.).
- [ ] Tables are used for structured comparisons (endpoints, env vars, options).
- [ ] Lines are wrapped at 120 characters.
- [ ] All links are relative and resolve correctly from the `docs/` directory.
- [ ] Diagrams use ASCII art or mermaid — no binary image files in PRs unless replacing a placeholder.

---

## Adding a new documentation page

1. Create the file in `docs/` with a clear, kebab-case filename (e.g. `docs/plugin-guide.md`).
2. Add a link to it from `README.md` in the Documentation table.
3. If it describes an architectural component, cross-reference `docs/architecture.md`.
