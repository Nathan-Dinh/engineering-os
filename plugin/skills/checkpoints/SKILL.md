---
description: Assess an engineering checkpoint (A scope, B quality, C architecture, D data and security, E feature design, F verification, G release) before a consequential step - evidence, readiness, and who must approve.
needs: [decision-owners]
---

# Engineering checkpoints A-G

A checkpoint makes a consequential step traceable; it is not ceremony for minor work. For a task that spans several, assess only the ones its risk and scope call for. Each checkpoint ends as passed, deferred, or blocked.

| Checkpoint | Focus | Ready to proceed when |
|---|---|---|
| **A — Product scope and requirements** | Problem, users, use cases, MVP, constraints, success, requirements, open questions | Important requirements are identified and labeled; material conflicts and unknowns are visible; scope, out-of-scope, and the next discovery step are understood. Unknowns may remain if they are not hidden. |
| **B — Quality attributes** | Priorities, constraints, scenarios, accepted trade-offs | The prioritization method, its limits, and the leading drivers are recorded; scenario measures are evidence-backed, user-accepted, or explicitly open. |
| **C — Architecture and technology** | Boundaries, useful C4 views, alternatives, recommendation, operational consequences | The architecture is tied to requirements and quality drivers; evidence, alternatives, and trade-offs are visible; consequential commitments are approved. |
| **D — Database and security model** | Entities, cardinality, access patterns, tenancy, privacy, lifecycle, migration, recovery | Data and trust boundaries, authorization and isolation, constraints, and migration risks are explicit; schema and security decisions are approved before production-impacting work. |
| **E — Feature design** | User problem, scope, acceptance criteria, affected components, data, UI, API, tests | Behavior and edge cases are observable; dependencies, design, and risks are understood; consequential decisions are approved or remain proposed. |
| **F — Implementation and verification** | Implementation, tests, quality scenarios, docs, deviations | Acceptance criteria have evidence; checks actually ran and their limits are recorded; deviations and unverified risks are visible. |
| **G — Release readiness and maintenance** | Rollout, recovery, monitoring, support, known risks, follow-up | Release and rollback or recovery, operational ownership, critical checks, and remaining risks are understood and accepted by the responsible person. If no release is in scope, say so. |

## At each checkpoint

1. State the question being decided and its decision owner (`docs/PROJECT.md#Decision owners`).
2. Summarize the evidence and its limits. Assess readiness separately from authorization (`${CLAUDE_PLUGIN_ROOT}/reference/policies/decisions.md`).
3. Identify conflicts, unknowns, options, and consequences.
4. For a consequential decision, propose a DEC and ask the owner to type `/simple-eng:approve DEC-####`. The owner may approve, ask for alternatives, or defer.
5. Record the outcome in the "Checkpoints" table in `docs/STATE.md` with a link to the evidence or DEC, plus the next action. A completed checklist or a recommendation is not approval.
