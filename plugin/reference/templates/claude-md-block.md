## simple-eng

This project uses the simple-eng plugin. Project knowledge lives in the repository, not in chat or agent memory: `docs/PROJECT.md` holds stable facts, `docs/STATE.md` holds work in progress, `docs/decisions/` and `docs/evidence/` hold records, and `decision-log/events.jsonl` holds decision events. A SessionStart hook loads PROJECT, STATE, knowledge gaps, and pending decisions at startup and after compaction.

### Rules

1. Inspect the repository before asking. Ask only what it cannot answer, a few related questions at a time, and say why each answer matters.
2. Never fabricate requirements, sources, approvals, test results, timestamps, history, or deployment status.
3. Label consequential claims as verified (name the check), user-provided, inferred (name the basis), proposed, or unknown. A config file or passing test proves only what it covers.
4. Consequential actions need explicit approval from a decision owner: major architecture or technology commitments, destructive operations, production security changes, sensitive-data handling, and material cost. Readiness (enough evidence) is separate from authorization (who may decide). Silence, a recommendation, or a passing test is not approval. Minor reversible details need no ceremony.
5. Approval is recorded only when the decision owner types `/simple-eng:approve DEC-####` or `/simple-eng:reject DEC-#### <reason>`. Never write approval events or edit `decision-log/events.jsonl`; propose with `simple-eng add-decision`.
6. Prefer the simplest solution that meets the requirements, and the existing stack. Add dependencies, services, or documents only for a demonstrated need.
7. Use measurable acceptance criteria and test-first where it fits. Never report an unrun check as passed.
8. Preserve history. Change an accepted decision only through a superseding DEC.
9. Write plainly for the reader: main point first, concrete words, no filler or hype, nuance and uncertainty kept.

### Choosing depth

- Proceed when requirements, evidence, and authority suffice. Investigate when the repository or tools can answer. Ask when only a person can.
- A small, reversible change needs no workflow: make it, verify it, report it. For larger or consequential work, use the narrowest `simple-eng:` workflow skill.

### Keeping context

- Write each answer the user gives to its record in the same turn (a PROJECT.md section, requirements, quality scenarios, or a DEC), labeled user-provided with the date. Record "Not applicable: <reason>" the same way, so it is never asked again.
- Before ending a turn that changed the focus, phase, checkpoints, open questions, or pending decisions, update `docs/STATE.md`. Keep it a short index of pointers, current items first.
- Keep project facts only in the repository. Agent memory is for how the user likes to work.
- Run `simple-eng validate` after editing records, and `simple-eng status` to see which knowledge areas are missing.

### Closing report

State what changed, what was verified and how, what was not verified, and the remaining risks.
