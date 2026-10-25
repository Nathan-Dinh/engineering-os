# Decision policy

## When to record

Record a decision (DEC) for consequential choices that shape architecture, data, security, operations, cost, or future change. Routine code details do not need one. `DEC-####` is the only decision ID: `simple-eng add-decision --title ... --summary ... --actor <who> [--evidence EVD-####]` appends the `proposed` event and creates `docs/decisions/records/DEC-####.md` from the template. Fill in its context, drivers, alternatives, decision, trade-offs, related requirements and quality attributes, and evidence.

## Readiness, authorization, ownership

Before asking for approval, check **readiness**: are the requirements, constraints, evidence, alternatives, and consequences enough to decide responsibly? Name the unknowns and unresolved trade-offs. Then identify **authorization**: who in `docs/PROJECT.md#Decision owners` may accept it. If no owner is recorded, ask. Note the **owner** accountable for implementing and following up, and how the result will be **verified**.

## Lifecycle

Events go in `decision-log/events.jsonl`, in this order:

- `proposed`, then optionally `evaluated` or `deferred` (written by `simple-eng add-decision --event ...`).
- `approved` or `rejected`, recorded only by the plugin's hook when the decision owner types `/simple-eng:approve DEC-####` or `/simple-eng:reject DEC-#### <reason>`. If authorization is unavailable, keep the decision proposed and stop before the consequential action.
- `implemented` and `verified` need an attestation. No simple-eng command writes them yet; record the implementation and the checks that ran in the DEC record instead.
- `superseded` (`simple-eng add-decision --event superseded --id DEC-#### --superseded-by DEC-####`). Never rewrite an accepted decision; propose a new DEC that supersedes it, and keep the original rationale.

`simple-eng` keeps each record's `Status:` line equal to its latest event, and `simple-eng validate` flags any mismatch. The event format is `${CLAUDE_PLUGIN_ROOT}/reference/decision-event.schema.json`.

## Limits

The event log is a local append-only convention, not a tamper-proof audit trail. Git history helps but gives no cryptographic assurance. The approval hook identifies the approver by `git config user.email` and records a hash of the typed command; anyone with shell access could still edit the file.
