---
description: Design or change system architecture and choose technologies - boundaries, C4 views, alternatives against quality drivers, and decision records needing owner approval. Use for architecture, stack, or major component choices.
needs: [problem-users, requirements, quality-priorities, constraints, decision-owners]
---

# Architecture and technology design

Run `simple-eng status --workflow architecture-design` first. Investigate or ask about the blocking areas before committing to anything consequential.

## Discover and bound

Review requirements, quality scenarios, repository structure, current architecture, dependencies, deployment shape, and existing DECs. Confirm the system's purpose, actors, boundaries, external systems, constraints, and open assumptions. Identify only the capabilities the requirements support (APIs, background processing, real-time, integrations, storage, search, caching, queues, identity, observability, deployment). If a critical input is missing, say so before choosing a component.

## Model

Use C4 at the levels that help:

- **System context**: users, system boundary, external systems, responsibilities, key data exchanges.
- **Container**: deployable or runtime units, responsibilities, interfaces, data stores, communication.
- **Component**: internal responsibilities and dependencies, only when it clarifies a real design or change.
- Code-level detail only when the implementation complexity justifies it.

Document trust boundaries, important data flows, integration contracts, failure modes, and deployment topology where relevant. Use Mermaid only when it communicates more clearly than prose and matches the implementation. Record the result in `docs/architecture/overview.md`, using `${CLAUDE_PLUGIN_ROOT}/reference/templates/architecture.md`.

## Evaluate choices

Follow `${CLAUDE_PLUGIN_ROOT}/reference/rubrics/technology-selection.md`, and check priorities against `${CLAUDE_PLUGIN_ROOT}/reference/rubrics/quality-attributes.md`. Prefer the existing technologies unless evidence justifies a change. Do not introduce a service, abstraction, or dependency without a requirement.

Propose each consequential choice as a DEC (`${CLAUDE_PLUGIN_ROOT}/reference/policies/decisions.md`) with alternatives, evidence, and consequences. Ask the decision owner to type `/simple-eng:approve DEC-####`; until they do, the choice stays proposed. Where a choice also shapes data or security boundaries, assess checkpoint D as well as C.

## Verify and maintain

Trace decisions to requirements, scenarios, and evidence. Define how each relevant quality will be evaluated, and do not call an attribute achieved without a check. When an accepted decision conflicts with new evidence, propose a superseding DEC.

## Record and hand off

Update `docs/STATE.md`: checkpoint C status, pending DECs, open questions, next step.
