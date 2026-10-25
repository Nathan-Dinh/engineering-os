"""`simple-eng`: the simple-eng command line. Claude runs it through the Bash tool; hooks run it with `hook <name>`."""
import argparse
import json
import sys
from pathlib import Path

from . import PLUGIN_ROOT, plugin_version
from .context import DEFAULT_LIMIT, build_context, record_files
from .dashboard import render_dashboard
from .guidance import budget_report, check_plugin
from .hooks import HANDLERS, run as run_hook
from .paths import is_initialized, project_root
from .projectmap import render_status, status_report
from .records import (CLASSIFICATIONS, LOW_AUTHORITY, add_decision, add_evidence, read_events,
                      validate_events, validate_records)
from .scaffold import apply_changes, planned_changes


def _root(args):
    return Path(args.root).resolve() if args.root else project_root()


def cmd_validate(args):
    if args.plugin:
        errors = check_plugin(PLUGIN_ROOT)
        label = 'plugin guidance'
    else:
        root = _root(args)
        if not is_initialized(root):
            print(f'{root} is not a simple-eng project (run /simple-eng:init).', file=sys.stderr)
            return 1
        errors = validate_records(root, record_files(root))
        label = 'project records'
    for error in errors:
        print('ERROR:', error, file=sys.stderr)
    if errors:
        return 1
    print(f'Validation passed for {label} (structure and references only; it does not prove claims are true).')
    return 0


def cmd_status(args):
    report = status_report(_root(args), PLUGIN_ROOT, args.workflow)
    print(json.dumps(report, indent=2) if args.json else render_status(report))
    return 0


def cmd_context(args):
    print(build_context(_root(args), PLUGIN_ROOT, args.limit))
    return 0


def cmd_init(args):
    root = _root(args)
    changes = planned_changes(root, PLUGIN_ROOT)
    for change in changes:
        print(f'{change["action"]:>9}  {change["path"]}')
    for change in changes:
        if change['path'] == 'CLAUDE.md' and change['diff']:
            print('\nCLAUDE.md diff (only the marked simple-eng block is managed):\n' + change['diff'])
    if args.apply:
        apply_changes(root, changes)
        print(f'\nApplied to {root} (simple-eng {plugin_version()}).')
    else:
        print('\nDry run. Re-run with --apply to write these changes.')
    return 0


def cmd_add_decision(args):
    record = add_decision(_root(args), decision_id=args.id, event=args.event, title=args.title, summary=args.summary,
                          actor=args.actor, evidence=args.evidence or (), superseded_by=args.superseded_by)
    print(f'Recorded {record["event"]} for {record["decision_id"]} ({record["event_id"]}). '
          'This is not an approval; the decision owner approves by typing /simple-eng:approve.')
    return 0


def cmd_add_evidence(args):
    path = add_evidence(_root(args), evidence_id=args.id, claim=args.claim, classification=args.classification,
                        source=args.source, method=args.method, scope=args.scope)
    print(f'Created {path.relative_to(_root(args))} (simple-eng does not verify the claim).')
    return 0


def cmd_show(args):
    events = [e for e in read_events(_root(args)) if e.get('decision_id') == args.id]
    if not events:
        print(f'No events for {args.id}.', file=sys.stderr)
        return 1
    for e in events:
        print(f'{e.get("timestamp")}  {e.get("event"):<11} {e.get("actor")}  [{e.get("source")}]  {e.get("summary", "")}'.rstrip())
    print(f'Latest: {events[-1].get("event")}')
    return 0


def cmd_dashboard(args):
    events = read_events(_root(args))
    errors = validate_events(events)
    if errors:
        raise ValueError('; '.join(errors))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_dashboard(events), encoding='utf-8')
    print('Wrote', output)
    return 0


def cmd_budget(args):
    print(budget_report(PLUGIN_ROOT))
    return 0


def cmd_hook(args):
    out = run_hook(args.name, sys.stdin.read())
    if out:
        print(out)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog='simple-eng', description=__doc__)
    parser.add_argument('--root', help='project root (default: CLAUDE_PROJECT_DIR, nearest .simple-eng/, or git top level)')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('validate', help='check project records, or the plugin itself with --plugin')
    p.add_argument('--plugin', action='store_true')
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser('status', help='report which knowledge areas are recorded')
    p.add_argument('--workflow', help='also list missing areas that block this workflow skill')
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_status)
    p = sub.add_parser('context', help='print the session context the SessionStart hook injects')
    p.add_argument('--limit', type=int, default=DEFAULT_LIMIT)
    p.set_defaults(func=cmd_context)
    p = sub.add_parser('init', help='set up a project (dry run unless --apply)')
    p.add_argument('--apply', action='store_true')
    p.set_defaults(func=cmd_init)
    p = sub.add_parser('add-decision', help='record a low-authority decision event')
    p.add_argument('--id', help='DEC-#### (default for proposals: next free ID)')
    p.add_argument('--event', choices=LOW_AUTHORITY, default='proposed')
    p.add_argument('--title', default='')
    p.add_argument('--summary', default='')
    p.add_argument('--actor', required=True)
    p.add_argument('--evidence', action='append', metavar='EVD-####')
    p.add_argument('--superseded-by', metavar='DEC-####')
    p.set_defaults(func=cmd_add_decision)
    p = sub.add_parser('add-evidence', help='create an evidence record')
    p.add_argument('--id', help='EVD-#### (default: next free ID)')
    p.add_argument('--claim', required=True)
    p.add_argument('--classification', choices=CLASSIFICATIONS, required=True)
    p.add_argument('--source', default='')
    p.add_argument('--method', default='')
    p.add_argument('--scope', default='')
    p.set_defaults(func=cmd_add_evidence)
    p = sub.add_parser('show', help='list the events for one decision')
    p.add_argument('id', metavar='DEC-####')
    p.set_defaults(func=cmd_show)
    p = sub.add_parser('dashboard', help='write a static, read-only HTML decision report')
    p.add_argument('--output', default='decision-dashboard.html')
    p.set_defaults(func=cmd_dashboard)
    p = sub.add_parser('budget', help='print estimated token cost of the plugin guidance')
    p.set_defaults(func=cmd_budget)
    p = sub.add_parser('hook', help='hook entry point (used by hooks/hooks.json)')
    p.add_argument('name', choices=sorted(HANDLERS))
    p.set_defaults(func=cmd_hook)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print('ERROR:', exc, file=sys.stderr)
        return 1
