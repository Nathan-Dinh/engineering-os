# Evidence policy

## Two scales, kept separate

**Claim label**: where a claim comes from. Use it for consequential claims in records and reports.

- **verified**: checked directly by a stated method against a cited source or system, within a stated scope. Give the check and its limits.
- **user-provided**: stated by the user. Record the date; do not imply independent verification.
- **inferred**: reasoned from cited evidence. Give the reasoning and the uncertainty.
- **proposed**: a recommendation or intended future state, not a fact.
- **unknown**: not established with the information available.

**Requirement status**: whether a requirement is in force. `open` (raised, not yet agreed), `accepted` (agreed by its owner), `deferred` (agreed to postpone), `dropped` (agreed out of scope). A requirement can be user-provided and still open; an inference never becomes accepted without its owner agreeing.

## What evidence establishes

A checked-in configuration, a passing test, or a documentation page is evidence only for what it covers. None of them alone proves production behavior. A source existing does not prove its claims are true or apply here. For facts that change over time (prices, versions, support, advisories), check a current primary source before relying on it.

## Recording

For consequential decisions, link evidence with an `EVD-####` record (`simple-eng add-evidence --claim ... --classification ... --source ...`) or a direct, durable reference. State the source, claim, label, verification method, date when relevant, scope, and limitations. Prefer primary sources and say why a source matters.

Run `simple-eng validate` after editing records. It checks structure and references only: it does not authenticate sources, check that they are reachable, or prove claims. Report factual verification separately.
