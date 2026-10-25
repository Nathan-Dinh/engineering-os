---
description: Research external facts for a decision - find and evaluate primary sources, check currency, and record reusable references and evidence. Use when a choice depends on vendor, standard, pricing, compatibility, or other external information.
needs: []
---

# Research

## Find and evaluate

Start by naming the decision or question the research should inform. Prefer primary sources: official documentation, standards, API specifications, vendor pricing and security pages, original research. Treat tutorials and examples as leads, not authority, unless they are independently corroborated.

Check each source's relevance, publication or update date, version, scope, authority, and known limitations. For claims that change over time (pricing, support, compatibility, security advisories), check a current source before relying on it. Keep what the source says separate from what you infer for this project.

## Record

For claims that a decision depends on, create evidence with `simple-eng add-evidence --claim ... --classification ... --source <url>` (see `${CLAUDE_PLUGIN_ROOT}/policies/evidence.md`). For references likely to be reused, add a note under `docs/resources/` from `${CLAUDE_PLUGIN_ROOT}/templates/research-reference.md`. Never claim a page was read or checked if it was not, and never store credentials.

A reference is not approval and does not by itself make a technology suitable. Mark references stale when a later decision depends on time-sensitive facts.

## Record and hand off

Link the evidence from the DEC it informs, and note any research still open in `docs/STATE.md`.
