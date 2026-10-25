---
description: Show which project knowledge areas are recorded, missing, or not applicable, and which gaps block a workflow. Use before starting a workflow or when unsure what is already known.
---

# Project knowledge status

Run `simple-eng status`. When preparing a workflow, add `--workflow <skill-name>` (for example `--workflow architecture-design`) to see which missing areas block it.

Then:

1. For missing areas marked `investigate`, look in the repository first and record what you find, labeled verified (with file paths) or inferred (with the basis).
2. For missing areas marked `ask`, ask the user a few related questions at a time, starting with the ones blocking the current work, and say why each answer matters.
3. Write each answer to the area's record in the same turn. Record `Not applicable: <reason>` for areas that do not apply, so they are not asked again.

`simple-eng status` checks only that a record exists and has content. Whether the content is correct is for the user to confirm.
