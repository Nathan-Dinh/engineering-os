---
description: Discovery for a new project or a fresh start - problem, users, scope, constraints, requirements, quality priorities, then architecture. Runs in phases across sessions; use when no established codebase or product definition exists.
needs: []
---

# Initialize a project

Begin with discovery, not code generation or a large set of documents. Ask a few related questions per turn, never the whole question bank. When the user is unsure, recommend a default and its implications, and keep it proposed until they confirm it.

## Phases

Read only the phase file for the current phase. `docs/STATE.md` "Current focus" records which phase is current, so a new session resumes in the right place.

| Phase | File | Done when |
|---|---|---|
| 1. Problem, users, success | `${CLAUDE_SKILL_DIR}/phase-1-problem.md` | problem, users, outcome, MVP and out-of-scope recorded or explicitly unknown |
| 2. Constraints and risk | `${CLAUDE_SKILL_DIR}/phase-2-constraints.md` | constraints and decision owners recorded; conflicts visible |
| 3. Requirements | `${CLAUDE_SKILL_DIR}/phase-3-requirements.md` | important requirements have IDs, claim labels, and statuses; checkpoint A assessed |
| 4. Quality attributes | `${CLAUDE_SKILL_DIR}/phase-4-quality.md` | priorities, method, and top scenarios recorded or unresolved; checkpoint B assessed |
| 5. Architecture and technology | `${CLAUDE_SKILL_DIR}/phase-5-architecture.md` | recommendation tied to drivers; consequential choices proposed as DECs |
| 6. Data and interface | `${CLAUDE_SKILL_DIR}/phase-6-data-ui.md` | data and UI discovery done where they apply |

Do not skip ahead. A later phase can start while minor unknowns remain, as long as they are visible in STATE.md. If no problem or user is established, do not choose a stack or design a solution.

## Record and hand off

- Every answer goes to its record in the same turn (see each phase for where).
- After each turn that moves discovery forward, update `docs/STATE.md`: current phase, next question group, open questions with why they matter, checkpoint status, and a "Recent changes" line.
- When initialization is ready to move on, summarize confirmed facts, assumptions, recommendations, open questions, and deferred decisions separately, and name the next checkpoint and the highest-impact remaining questions. Readiness does not require every unknown to be resolved.
