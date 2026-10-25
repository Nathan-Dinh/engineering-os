---
description: Approve a pending decision as its decision owner. Usage - /simple-eng:approve DEC-#### [note]
disable-model-invocation: true
---

# Approval typed by the user: $ARGUMENTS

The plugin's UserPromptExpansion hook records this approval from the command the user typed. You do not record it.

1. Look in this turn's context for a note that starts with `simple-eng recorded event` and names this decision. Confirm on disk with `simple-eng show <DEC-####>`: the latest event must be `approved`.
2. If both confirm it, tell the user the approval was recorded (decision, approver, time). Move the decision out of "Pending decisions" in `docs/STATE.md`, add a "Recent changes" line, and continue only with work inside that decision's scope.
3. If the note is missing or `simple-eng show` does not list `approved` as the latest event, say clearly that the approval was **not** recorded. The likely causes: the command was not typed at the start of a message, the decision is not pending, `git config user.email` is not set, or python3 is unavailable. Treat the decision as still pending.

Never write approval events yourself or edit `decision-log/events.jsonl`.
