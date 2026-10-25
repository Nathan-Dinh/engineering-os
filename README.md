# simple-eng

A Claude Code plugin that helps you discover, decide, build, and verify incrementally in any project. Your project's knowledge stays in its repository, so Claude doesn't lose it on compaction, `/clear`, or in a new session: requirements and their sources, open questions, where discovery stands, and which decisions you have approved.

## Install

In Claude Code:

```text
/plugin install simple-eng --marketplace Nathan-Dinh/simple-eng
```

On older Claude Code versions, add the marketplace first:

```text
/plugin marketplace add Nathan-Dinh/simple-eng
/plugin install simple-eng@simple-eng
```

The plugin's command line and hooks need `python3` (3.9 or later, standard library only). Without it, sessions keep working but project state isn't loaded, and a one-line notice says so.

## First run in a project

Open Claude Code in the project and type:

```text
/simple-eng:init
```

Claude shows what it will create, including a diff of `CLAUDE.md`, and asks before writing anything. Then it fills in what it can learn from the repository and asks you about the rest, a few questions at a time. Run it in each project you want to use this in. Running it again after a plugin update refreshes only the managed part of `CLAUDE.md`.

What a project gets:

| File | Purpose | Who changes it |
|---|---|---|
| `CLAUDE.md` (a block between `simple-eng` markers) | The always-on rules: evidence labels, what needs approval, how to keep state | `/simple-eng:init`; your own text outside the markers is never touched |
| `docs/PROJECT.md` | Stable facts: problem, users, scope, constraints, decision owners, stack, commands, environments | Claude, from what it finds and what you tell it |
| `docs/STATE.md` | Work in progress: current workflow and phase, checkpoints, open questions, pending decisions | Claude, as work moves forward |
| `.simple-eng/config.json` | Plugin version marker, and optional pointers to facts that already live elsewhere | `/simple-eng:init`, or you |
| `docs/decisions/records/DEC-####.md`, `docs/evidence/records/EVD-####.md`, `decision-log/events.jsonl` | Decision and evidence records, plus the decision event log | `simple-eng` commands and the approval hook |

Commit these files. They are the project's memory.

## How it keeps context

- **Session start and after compaction**, a hook loads `docs/STATE.md`, `docs/PROJECT.md`, missing knowledge areas, pending decisions, and record problems into Claude's context, capped at 6,000 characters.
- **The rules in `CLAUDE.md`** tell Claude to write each answer you give to its record in the same turn, to update `STATE.md` whenever progress changes, and to keep project facts in the repository rather than in its private memory.
- **Workflows are skills.** Only their one-line descriptions sit in context until one is needed. Claude Code re-attaches the most recent ones after compaction.

If you already keep a fact somewhere, point at it instead of duplicating it:

```json
{ "areas": { "architecture": { "record": "ARCHITECTURE.md#Overview" },
             "ui": { "not_applicable": "command-line tool with no interface" } } }
```

## Skills

| Skill | Use it for |
|---|---|
| `/simple-eng:init` | Set up or refresh a project (you run it) |
| `/simple-eng:status` | See which project facts are recorded or missing |
| `/simple-eng:approve DEC-#### [note]` | Approve a pending decision (only you can) |
| `/simple-eng:reject DEC-#### <reason>` | Reject a pending decision (only you can) |
| `initialize-project` | Discovery for a new project, in phases that resume across sessions |
| `analyze-existing-project` | Understand an existing codebase before changing it |
| `architecture-design` | Architecture and technology choices |
| `database-engineering` | Schema, migrations, tenancy, data lifecycle |
| `feature-development` | Features, from acceptance criteria through test-first implementation |
| `ui-ux-design` | Journeys, interaction states, accessibility |
| `research-management` | External facts and sources behind a decision |
| `maintain-project` | Bugs, upgrades, incidents, refactors |
| `checkpoints` | Checkpoints A–G before consequential steps |

Claude picks the workflow skills on its own when they fit. You can also invoke any of them by name, for example `/simple-eng:architecture-design`. A small change needs no workflow.

## Approvals

Consequential decisions (major architecture, destructive operations, production security, sensitive data, material cost) are proposed as `DEC-####` records. They take effect only when you type:

```text
/simple-eng:approve DEC-0003
```

That must be at the start of your message. A hook, not Claude, then writes the approval to `decision-log/events.jsonl`, using your `git config user.email` and a hash of what you typed. Claude can't invoke the approve skill, and another hook blocks it from editing the log or calling the approval code directly. If `git config user.email` isn't set, the approval is refused and you're told why.

## The `simple-eng` command

Claude runs `simple-eng` through its Bash tool; the plugin puts it on Claude's PATH. You can run it yourself with `python3 <plugin-dir>/bin/simple-eng`.

```text
simple-eng status [--workflow NAME]        which knowledge areas are recorded, missing, or not applicable
simple-eng validate                        check records: event order, approvals, ID references, record status
simple-eng context                         print what the session-start hook injects
simple-eng add-decision --title T --summary S --actor A [--evidence EVD-####]
simple-eng add-evidence --claim C --classification verified|user-provided|inferred|proposed|unknown --source S
simple-eng show DEC-####                   list a decision's events
simple-eng dashboard --output report.html  static, read-only decision report
simple-eng init [--apply]                  what /simple-eng:init runs
```

## Boundaries

- **Guidance is not enforcement.** Hooks guarantee that state is *loaded*. Whether Claude *writes* it on time depends on Claude following the rules. `simple-eng validate` catches broken references and status mismatches, not stale content.
- **The event log is not tamper-proof.** It's a local, append-only convention. The hook records who approved and a hash of the command, but anyone with shell access can edit the file, and git history gives no cryptographic assurance.
- **`simple-eng status` checks presence, not truth.** It reports whether a fact is recorded, not whether it's correct. Only you can confirm that.
- **`implemented` and `verified` events** need an attestation, and no `simple-eng` command writes them yet. Record implementation and test results in the decision record.
- **Claude Code only.** Other agents won't pick up the skills or hooks.
- **Token figures are estimates** (bytes ÷ 4). `simple-eng budget` prints them.
- **Not built:** live evaluation of conversations, automatic checking of external sources, and comparing documentation with code behavior.

## Developing

```text
.claude-plugin/marketplace.json   the marketplace; points at ./plugin
plugin/                           everything that installs (only this folder is copied to users)
├── .claude-plugin/plugin.json    name and version
├── skills/                       workflow and command skills
├── hooks/hooks.json              session start, approval capture, log guard
├── bin/simple-eng                command-line entry point, on Claude's PATH
├── lib/simple_eng/               the code behind bin/ and the hooks
└── reference/                    files skills read on demand: policies, rubrics, templates,
                                  project-map.json, decision-event.schema.json
tests/                            maintainer tests; not installed
```

```bash
python3 -m unittest discover -s tests -v          # unit, fixture, and end-to-end CLI tests
python3 plugin/bin/simple-eng validate --plugin   # skill frontmatter, references, project map, token budgets
python3 plugin/bin/simple-eng budget              # estimated tokens per workflow
claude plugin validate . --strict                 # marketplace manifest
claude plugin validate ./plugin --strict          # plugin manifest and components
claude --plugin-dir ./plugin                      # try the plugin locally without installing
```

To release, bump `version` in `plugin/.claude-plugin/plugin.json`. Installed copies stay on their version until it changes.

The tests check code and guidance structure. They don't run an agent or prove how a conversation will go.

## References

- Claude Code plugin, hook, and skill documentation: https://code.claude.com/docs
- On plain language: https://www.learningguild.com/articles/be-concrete-why-simple-language-matters-in-the-ai-age
