---
description: Set up simple-eng in this project - the CLAUDE.md rules block, project profile, working state, and a first pass over missing project knowledge.
disable-model-invocation: true
---

# Set up simple-eng in this project

1. Run `simple-eng init` (a dry run). Show the user the planned files and the CLAUDE.md diff. If CLAUDE.md already exists, say that only the block between the `simple-eng` markers is managed and the rest stays untouched. After the user confirms, run `simple-eng init --apply`. Re-running after a plugin update refreshes only the block and the version marker; it never overwrites `docs/PROJECT.md` or `docs/STATE.md`.
2. Run `simple-eng status` to list the knowledge areas and their records.
3. Investigate the areas marked `investigate` (stack, commands, environments, architecture, data model, UI): read manifests, build and CI files, entry points, schemas and migrations, and UI code. Write findings into each area's record section, labeled verified with the file paths, or inferred with the basis. Do not run destructive commands, install dependencies, or call external services. For an area that clearly does not apply, write `Not applicable: <reason and evidence>`.
4. If a fact already lives in another file (for example `ARCHITECTURE.md`), point the area at it instead of copying: in `.simple-eng/config.json`, set `"areas": {"architecture": {"record": "ARCHITECTURE.md#Overview"}}`.
5. Ask about the areas marked `ask`, a few related questions at a time, starting with what the user's current goal needs. Ask about decision owners early, because approvals depend on them. Say why each answer matters. Write each answer to its section in the same turn, labeled user-provided with today's date.
6. In `docs/STATE.md`, list unanswered areas under "Open questions" (with why each matters), set "Current focus", and add a "Recent changes" line.
7. Run `simple-eng validate` and `simple-eng status`. Report what was recorded, what is still missing, and the suggested next workflow: `simple-eng:analyze-existing-project` for an existing codebase, or `simple-eng:initialize-project` for a new one.
