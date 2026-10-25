---
description: Design or change user-facing behavior - journeys, navigation, interaction states, responsive layout, and accessibility, building on the existing design system. Use for UI, UX, or accessibility work.
needs: [problem-users]
---

# UI and UX design

## Discover

Inspect the existing design system, components, tokens, navigation, and conventions. Establish the target users, primary journeys, information architecture, device and responsive needs, the accessibility target if one is known, and the constraints. Ask focused questions when the answer changes behavior or layout.

## Specify interaction behavior

For each relevant journey, describe entry points, transitions, user actions, validation, and the success, loading, empty, error, disabled, and recovery states. Note keyboard and focus behavior, semantics, contrast, reduced motion, responsive behavior, and assistive-technology needs where they apply. Do not assume a compliance target: clarify it or mark it unknown.

## Design and implement

Prefer existing components, tokens, and patterns, and add a new pattern only for an identified need. Make wireframes, mockups, or prototypes only when they reduce real uncertainty. Record consequential design trade-offs as DECs (`${CLAUDE_PLUGIN_ROOT}/reference/policies/decisions.md`) linked to requirements, and keep notes in `docs/design/notes.md` (`${CLAUDE_PLUGIN_ROOT}/reference/templates/design-notes.md`) when they will be reused.

## Verify

Test the critical journeys and their interaction states at representative viewports. Use automated accessibility checks where available, plus manual keyboard and assistive-technology review when needed, and state the limits. An automated scan alone does not establish accessibility compliance.

## Record and hand off

Update `docs/STATE.md` with the journeys covered, open design questions, and the next step.
