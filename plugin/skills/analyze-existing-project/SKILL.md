---
description: Understand an existing codebase before changing it - inspect structure, stack, tests, CI, data, docs, and past decisions, separate facts from inference, then ask only what the code cannot answer.
needs: []
---

# Analyze an existing project

## Inspect before asking

Work out what kind of repository this is (application, library, infrastructure, other). Inspect, with bounded reads, the file tree, entry points, dependency manifests, build and run configuration, architecture, persistence layer, tests, CI and deployment configuration, security and privacy controls, docs, and decision history. A config file shows intent, not deployed state.

Run safe, focused checks when useful (for example the test suite, if it is cheap and has no side effects) and note the exact commands and results. Do not run destructive commands, install dependencies, call external services, or touch production without authorization.

## Findings and questions

Summarize verified facts with paths. Keep user-provided context, inferences, proposed improvements, and unknowns apart (labels in `${CLAUDE_PLUGIN_ROOT}/reference/policies/evidence.md`). Identify existing conventions and accepted decisions; never invent the history behind them.

Treat contradictions between docs and code as drift candidates, not proof of intent. Before treating either one as authoritative, ask when the difference is consequential.

Then ask a small group of material questions the repository cannot answer: users and outcomes, expected usage, unrecorded constraints, operational expectations, data classification, ownership, target environments, success criteria. Say why each answer matters.

## Prioritize

Identify the highest-impact gaps and whether they block a safe change. Do not turn discovery into an unsolicited redesign. For architecture work, review quality priorities and prior DECs first; for database work, look at the schema, migrations, tenancy, and tests; for features, use `simple-eng:feature-development`.

## Record and hand off

- Write findings into `docs/PROJECT.md` sections (stack, commands, environments) and the other area records that `simple-eng status` lists, with labels and paths.
- In `docs/STATE.md`, record the lifecycle stage, open questions, drift candidates, and one proposed next checkpoint or action.
- If there is no change request, stop at discovery and ask only the highest-impact next question.
