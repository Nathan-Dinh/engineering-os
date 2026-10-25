---
description: Build a feature end to end - discover the user problem, specify observable acceptance criteria, design, implement test-first where it fits, and verify. Use for new features, user stories, or substantial behavior changes.
needs: [problem-users, commands]
---

# Feature development

## 1. Discover

Establish the user problem, actors, expected behavior, success measure, edge cases, affected components, required data, dependencies, and security and privacy implications. Inspect the existing code and DECs first. Ask a small group of consequential questions and mark what stays unresolved.

## 2. Specify

For a substantial feature, write a short spec at `docs/features/FEAT-####.md` from `${CLAUDE_PLUGIN_ROOT}/reference/templates/feature.md`: problem, scope and out-of-scope, stories, requirements with observable acceptance criteria, dependencies, affected components and data, relevant quality attributes, and open questions. A small change needs no document. Resolve conflicting requirements or acceptance criteria with the user; do not invent a target, business rule, or permission. When the feature design is consequential, assess checkpoint E.

## 3. Design

Work out the contract or API, schema and migration, UI, state, integration boundaries, error behavior, security, tests, rollout, and rollback. Hand off to `simple-eng:architecture-design`, `simple-eng:database-engineering`, or `simple-eng:ui-ux-design` where their scope applies. Check for conflicts with DECs, and propose consequential choices as DECs before implementing them.

## 4. Test and implement

Choose the verification approach with `${CLAUDE_SKILL_DIR}/tdd.md`. Follow the existing architecture and conventions, make the smallest complete change, and avoid unrelated refactoring. Record any significant deviation from the accepted design.

## 5. Verify

Check each acceptance criterion and applicable quality scenario. Run targeted tests and relevant regression checks. Review security and privacy, migrations, error behavior, observability, accessibility where relevant, and docs. Update the feature's status only from work that actually happened.

## Record and hand off

Update `docs/STATE.md` (feature, checkpoint E or F status, next step). The closing report covers what changed, requirement and acceptance coverage, checks run with exact commands and results, checks not run, deviations, and remaining risks.
