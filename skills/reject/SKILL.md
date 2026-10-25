---
description: Reject a pending decision as its decision owner. Usage - /simple-eng:reject DEC-#### <reason>
disable-model-invocation: true
---

# Rejection typed by the user: $ARGUMENTS

The plugin's UserPromptExpansion hook records this rejection from the command the user typed. You do not record it.

1. Look in this turn's context for a note that starts with `simple-eng recorded event` and names this decision. Confirm on disk with `simple-eng show <DEC-####>`: the latest event must be `rejected`.
2. If both confirm it, acknowledge the rejection and its reason. Update `docs/STATE.md` (remove the decision from pending, add a "Recent changes" line) and stop any work that depended on the decision. If an alternative is still needed, propose a new DEC instead of reusing this one.
3. If the note is missing or the latest event is not `rejected`, say the rejection was **not** recorded, and treat the decision as still pending.

Never write decision events yourself or edit `decision-log/events.jsonl`.
