"""Session context for the SessionStart hook: factual, size-capped, read from files on disk."""
from pathlib import Path

from . import PLUGIN_ROOT, plugin_version
from .markdown import EMPTY_LABEL, TABLE_SEPARATOR, strip_comments
from .paths import CONFIG, PROJECT, STATE, is_initialized, load_config
from .projectmap import area_record, load_map, split_record, status_report, summary_line
from .records import pending_decisions, read_events, validate_records

DEFAULT_LIMIT = 6000
HARD_LIMIT = 9000  # Claude Code moves hook output over 10,000 characters to a file.

NOT_INITIALIZED = ('simple-eng: this project has not been initialized (no {config}). '
                   'The user can run /simple-eng:init to set up project state, or ignore this if the project does not use it.')


def record_files(root, plugin_root=PLUGIN_ROOT):
    """Area record files outside docs/ that the user pointed the map at."""
    config = load_config(root)
    files = []
    for area in load_map(plugin_root):
        record, overridden = area_record(area, config)
        if overridden:
            files.append(split_record(record)[0])
    return files


def _clip(text, budget, path):
    text = text.strip()
    if len(text) <= budget:
        return text
    marker = f'\n[... truncated; {len(text) - budget} more characters in {path}]'
    keep = max(budget - len(marker), 0)
    cut = text.rfind('\n', 0, keep)
    return text[:cut if cut > keep // 2 else keep].rstrip() + marker


def compact(text):
    """Drop comments, blank lines, empty `- Label:` items, and table rows with nothing filled in beyond the first cell.
    A table left with no rows is dropped entirely, header included."""
    out, table = [], []

    def flush():
        rows = [r for r in table[2:] if sum(1 for c in r.strip().strip('|').split('|') if c.strip()) >= 2]
        if len(table) >= 2 and TABLE_SEPARATOR.match(table[1]):
            out.extend(table[:2] + rows if rows else [])
        else:
            out.extend(table)
        table.clear()

    for line in strip_comments(text).splitlines():
        if line.strip().startswith('|'):
            table.append(line)
            continue
        if table:
            flush()
        if line.strip() and not EMPTY_LABEL.match(line):
            out.append(line)
    if table:
        flush()
    return '\n'.join(out)


def _read(root, rel):
    path = Path(root) / rel
    if not path.is_file():
        return None
    return compact(path.read_text(encoding='utf-8'))


def build_context(root, plugin_root=PLUGIN_ROOT, limit=DEFAULT_LIMIT):
    limit = min(limit, HARD_LIMIT)
    if not is_initialized(root):
        return NOT_INITIALIZED.format(config=CONFIG)
    head = ['simple-eng project context, generated from files on disk at session start. '
            'The files named below are the source of truth.']
    try:
        config = load_config(root)
        report = status_report(root, plugin_root)
        head.append('Knowledge areas: ' + summary_line(report) + '. Details: `simple-eng status`.')
    except ValueError as exc:
        config = {}
        head.append(f'Knowledge areas unavailable: {exc}')
    try:
        pending = pending_decisions(read_events(root))
    except ValueError:
        pending = {}
    if pending:
        items = [f'{dec} "{e.get("title", "")}" (latest: {e.get("event")}, {str(e.get("timestamp", ""))[:10]})'
                 for dec, e in sorted(pending.items())]
        head.append('Decisions waiting for the decision owner (/simple-eng:approve or /simple-eng:reject): '
                    + '; '.join(items) + '.')
    else:
        head.append('No decisions are waiting for approval.')
    errors = validate_records(root, record_files(root, plugin_root))
    if errors:
        shown = '; '.join(errors[:5]) + (f'; and {len(errors) - 5} more' if len(errors) > 5 else '')
        head.append(f'`simple-eng validate` reports {len(errors)} problem(s): {shown}.')
    installed, current = config.get('framework_version'), plugin_version(plugin_root)
    if installed and installed != current:
        head.append(f'The project was initialized with simple-eng {installed}; the plugin is {current}. '
                    'Running /simple-eng:init again refreshes the CLAUDE.md block.')
    header = '\n'.join(head)
    remaining = limit - len(header) - 40
    parts = [header]
    state, project = _read(root, STATE), _read(root, PROJECT)
    # STATE first: it is what the next session needs most. PROJECT gets what is left.
    for rel, text, share in ((STATE, state, 0.55), (PROJECT, project, 1.0)):
        if text is None:
            parts.append(f'{rel} does not exist yet.')
            continue
        budget = int(remaining * share) if rel == STATE and project else remaining
        clipped = _clip(text, max(budget, 200), rel)
        parts.append(f'--- {rel} ---\n{clipped}')
        remaining -= len(clipped) + len(rel) + 10
    out = '\n\n'.join(parts)
    return out if len(out) <= limit else _clip(out, limit, 'the files above')
