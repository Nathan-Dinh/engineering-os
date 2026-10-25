"""Decision events, evidence records, and traceability-ID validation.

Events live in decision-log/events.jsonl (append-only by convention, not tamper-proof).
The CLI writes only low-authority events; approve/reject events are written by the
UserPromptExpansion hook from a command the user typed.
"""
import datetime as dt
import json
import re
import uuid
from pathlib import Path

from . import PLUGIN_ROOT
from .paths import DECISIONS, DOCS, EVIDENCE, LOG

EVENTS = ('proposed', 'evaluated', 'deferred', 'approved', 'rejected', 'implemented', 'verified', 'superseded')
LOW_AUTHORITY = ('proposed', 'evaluated', 'deferred', 'superseded')
USER_DECISIONS = ('approved', 'rejected')
PENDING = ('proposed', 'evaluated', 'deferred')
CLASSIFICATIONS = ('verified', 'user-provided', 'inferred', 'proposed', 'unknown')
FIELDS = {'event_id', 'decision_id', 'event', 'timestamp', 'actor', 'source', 'title', 'summary',
          'evidence_ids', 'attestation', 'superseded_by'}
REQUIRED = {'event_id', 'decision_id', 'event', 'timestamp', 'actor', 'source'}
CLI_SOURCE = 'simple-eng-cli'
HOOK_SOURCE = 'user-prompt-hook'
HOOK_ATTESTATION = re.compile(r'^UserPromptExpansion;session=[^;\s]+;prompt-sha256=[0-9a-f]{64}$')

DEC_ID = re.compile(r'^DEC-\d{4,}$')
EVD_ID = re.compile(r'^EVD-\d{4,}$')
ANY_ID = re.compile(r'\b(?:REQ|QA|EVD|DEC|FEAT|TEST)-\d{4,}\b')
DEFINED_IN_MARKDOWN = ('REQ', 'QA', 'FEAT', 'TEST')
DEFINITION_SITES = (
    re.compile(r'^\s*\|\s*((?:REQ|QA|FEAT|TEST)-\d{4,})\s*\|'),        # first table cell
    re.compile(r'^\s*#{1,6}\s+((?:REQ|QA|FEAT|TEST)-\d{4,})\b'),         # heading
    re.compile(r'^\s*[-*]\s*ID:\s*((?:REQ|QA|FEAT|TEST)-\d{4,})\b', re.IGNORECASE),
)
STATUS_LINE = re.compile(r'^(\s*[-*]\s*Status:\s*)(\S*)(.*)$', re.MULTILINE)

# What each event may follow. None means "first event for the decision".
ALLOWED_AFTER = {
    'proposed': {None},
    'evaluated': set(PENDING),
    'deferred': set(PENDING),
    'approved': set(PENDING),
    'rejected': set(PENDING),
    'implemented': {'approved'},
    'verified': {'implemented'},
    'superseded': set(PENDING) | {'approved', 'implemented', 'verified'},
}


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_events(root):
    path = Path(root) / LOG
    if not path.exists():
        return []
    events = []
    for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'{LOG} line {n}: invalid JSON: {exc}') from exc
        if not isinstance(obj, dict):
            raise ValueError(f'{LOG} line {n}: event must be a JSON object')
        events.append(obj)
    return events


def latest_by_decision(events):
    latest = {}
    for event in events:
        latest[event.get('decision_id')] = event
    return latest


def is_trusted(event):
    """False for approve/reject events not written by the approval hook, and for unattested implemented/verified events."""
    kind = event.get('event')
    if kind in USER_DECISIONS:
        return event.get('source') == HOOK_SOURCE and bool(HOOK_ATTESTATION.match(str(event.get('attestation', ''))))
    if kind in ('implemented', 'verified'):
        return bool(str(event.get('attestation', '')).strip())
    return True


def pending_decisions(events):
    """Decisions whose latest trustworthy event leaves them waiting for the decision owner."""
    latest = latest_by_decision([e for e in events if is_trusted(e)])
    return {dec: e for dec, e in latest.items() if e.get('event') in PENDING}


def _valid_timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_events(events):
    errors = []
    seen_ids = set()
    state = {}
    for i, e in enumerate(events, 1):
        where = f'{LOG} event {i}'
        missing = REQUIRED - e.keys()
        if missing:
            errors.append(f'{where}: missing {sorted(missing)}')
        unknown = e.keys() - FIELDS
        if unknown:
            errors.append(f'{where}: unknown fields {sorted(unknown)}')
        if not re.fullmatch(r'EVT-[0-9a-f]{32}', str(e.get('event_id', ''))):
            errors.append(f'{where}: invalid event_id')
        elif e['event_id'] in seen_ids:
            errors.append(f'{where}: duplicate event_id')
        seen_ids.add(e.get('event_id'))
        dec = e.get('decision_id')
        if not DEC_ID.match(str(dec or '')):
            errors.append(f'{where}: invalid decision_id')
        kind = e.get('event')
        if kind not in EVENTS:
            errors.append(f'{where}: invalid event {kind!r}')
        for field in ('actor', 'source'):
            if not isinstance(e.get(field), str) or not e.get(field).strip():
                errors.append(f'{where}: invalid {field}')
        for field in ('title', 'summary', 'attestation'):
            if field in e and not isinstance(e[field], str):
                errors.append(f'{where}: {field} must be a string')
        if not _valid_timestamp(e.get('timestamp')):
            errors.append(f'{where}: timestamp must be ISO 8601 with a timezone')
        evidence = e.get('evidence_ids', [])
        if not isinstance(evidence, list) or any(not EVD_ID.match(str(x)) for x in evidence):
            errors.append(f'{where}: evidence_ids must be a list of EVD-#### IDs')
        if kind == 'superseded' and not DEC_ID.match(str(e.get('superseded_by', ''))):
            errors.append(f'{where}: superseded event needs superseded_by DEC-####')
        if 'superseded_by' in e and kind != 'superseded':
            errors.append(f'{where}: superseded_by is only valid on superseded events')
        if not is_trusted(e):
            if kind in USER_DECISIONS:
                errors.append(f'{where}: {kind} events must come from the approval hook ({HOOK_SOURCE} with a typed-command attestation)')
            else:
                errors.append(f'{where}: {kind} events need an attestation')
        if kind in ALLOWED_AFTER and DEC_ID.match(str(dec or '')):
            previous = state.get(dec)
            if previous not in ALLOWED_AFTER[kind]:
                after = f'after {previous!r}' if previous else 'as the first event'
                errors.append(f'{where}: {kind!r} is not allowed {after} for {dec}')
            state[dec] = kind
    return errors


def _markdown_files(root, extra=()):
    root = Path(root)
    files = sorted((root / DOCS).rglob('*.md')) if (root / DOCS).is_dir() else []
    for rel in extra:
        path = root / rel
        if path.is_file() and path not in files:
            files.append(path)
    return files


def scan_ids(root, extra_files=()):
    """Return (definitions, references). Each maps ID -> list of 'path:line' locations.

    DEC IDs are defined by `proposed` events, EVD IDs by their record files, and REQ/QA/FEAT/TEST IDs
    by a definition site in markdown (first table cell, heading, or `- ID:` line). Every other mention is a reference.
    """
    root = Path(root)
    definitions, references = {}, {}
    for n, e in enumerate(read_events(root), 1):
        if e.get('event') == 'proposed':
            definitions.setdefault(e.get('decision_id'), []).append(f'{LOG}:{n}')
        for ref in list(e.get('evidence_ids') or []) + ([e['superseded_by']] if e.get('superseded_by') else []):
            references.setdefault(ref, []).append(f'{LOG}:{n}')
    evidence_dir = root / EVIDENCE
    if evidence_dir.is_dir():
        for path in sorted(evidence_dir.glob('EVD-*.md')):
            definitions.setdefault(path.stem, []).append(str(path.relative_to(root)))
    for path in _markdown_files(root, extra_files):
        rel = str(path.relative_to(root))
        own = path.stem if path.parent in (root / DECISIONS, evidence_dir) else None
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            defined_here = set()
            for pattern in DEFINITION_SITES:
                m = pattern.match(line)
                if m:
                    definitions.setdefault(m.group(1), []).append(f'{rel}:{n}')
                    defined_here.add(m.group(1))
            for ref in ANY_ID.findall(line):
                if ref not in defined_here and ref != own:
                    references.setdefault(ref, []).append(f'{rel}:{n}')
    return definitions, references


def validate_records(root, extra_files=()):
    root = Path(root)
    try:
        events = read_events(root)
    except ValueError as exc:
        return [str(exc)]
    errors = validate_events(events)
    definitions, references = scan_ids(root, extra_files)
    for ident, sites in sorted(definitions.items()):
        if ident.split('-')[0] in DEFINED_IN_MARKDOWN and len(sites) > 1:
            errors.append(f'{ident} is defined more than once: {", ".join(sites)}')
    for ident, sites in sorted(references.items()):
        if ident not in definitions:
            errors.append(f'{ident} is referenced but never defined ({", ".join(sites[:3])})')
    latest = latest_by_decision(events)
    decision_dir = root / DECISIONS
    if decision_dir.is_dir():
        for path in sorted(decision_dir.glob('DEC-*.md')):
            rel = path.relative_to(root)
            if path.stem not in latest:
                errors.append(f'{rel}: no events for {path.stem}; create decisions with `simple-eng add-decision`')
                continue
            m = STATUS_LINE.search(path.read_text(encoding='utf-8'))
            expected = latest[path.stem].get('event')
            if not m:
                errors.append(f'{rel}: missing "- Status:" line (expected {expected})')
            elif m.group(2) != expected:
                errors.append(f'{rel}: Status is {m.group(2)!r} but the latest event is {expected!r}')
    return errors


def _append(root, event):
    events = read_events(root)
    existing = validate_events(events)
    if existing:
        raise ValueError('event log is invalid; fix it before appending: ' + '; '.join(existing[:3]))
    problems = validate_events(events + [event])
    if problems:
        raise ValueError('; '.join(problems))
    path = Path(root) / LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


def set_record_status(root, decision_id, status):
    path = Path(root) / DECISIONS / f'{decision_id}.md'
    if not path.is_file():
        return False
    text = path.read_text(encoding='utf-8')
    if STATUS_LINE.search(text):
        text = STATUS_LINE.sub(lambda m: f'{m.group(1)}{status}', text, count=1)
    else:
        lines = text.split('\n', 1)
        text = lines[0] + f'\n\n- Status: {status}\n' + (lines[1] if len(lines) > 1 else '')
    path.write_text(text, encoding='utf-8')
    return True


def next_id(root, prefix):
    numbers = [int(i.split('-')[1]) for i in scan_ids(root)[0] if i.startswith(prefix + '-')]
    if prefix == 'EVD' and (Path(root) / EVIDENCE).is_dir():
        numbers += [int(p.stem.split('-')[1]) for p in (Path(root) / EVIDENCE).glob('EVD-*.md')]
    return f'{prefix}-{max(numbers, default=0) + 1:04d}'


def _clean(text):
    return ' '.join(str(text).split())


def add_decision(root, *, decision_id=None, event='proposed', title='', summary='', actor, evidence=(), superseded_by=None):
    root = Path(root)
    if event not in LOW_AUTHORITY:
        raise ValueError(f'simple-eng records only {", ".join(LOW_AUTHORITY)} events; approval is typed by the decision owner')
    if not actor.strip():
        raise ValueError('actor is required')
    decision_id = decision_id or (next_id(root, 'DEC') if event == 'proposed' else None)
    if not decision_id or not DEC_ID.match(decision_id):
        raise ValueError('decision ID must look like DEC-0001')
    known = scan_ids(root)[0]
    for ref in evidence:
        if not EVD_ID.match(ref) or ref not in known:
            raise ValueError(f'unknown evidence {ref}; create it first with `simple-eng add-evidence`')
    if event == 'proposed' and not title.strip():
        raise ValueError('a proposal needs a title')
    record = {'event_id': 'EVT-' + uuid.uuid4().hex, 'decision_id': decision_id, 'event': event,
              'timestamp': now(), 'actor': actor.strip(), 'source': CLI_SOURCE,
              'title': _clean(title), 'summary': _clean(summary), 'evidence_ids': list(evidence)}
    if superseded_by:
        record['superseded_by'] = superseded_by
    _append(root, record)
    path = root / DECISIONS / f'{decision_id}.md'
    if event == 'proposed' and not path.exists():
        template = (PLUGIN_ROOT / 'reference/templates/decision-record.md').read_text(encoding='utf-8')
        text = template.replace('DEC-XXXX: <title>', f'{decision_id}: {_clean(title)}', 1)
        text = text.replace('- Date:', f'- Date: {record["timestamp"][:10]}', 1)
        if evidence:
            text = text.replace('- Evidence:', '- Evidence: ' + ', '.join(evidence), 1)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    set_record_status(root, decision_id, event)
    return record


def record_user_decision(root, *, decision_id, kind, note, actor, attestation):
    """Append an approved/rejected event. Called only by the UserPromptExpansion hook."""
    if kind not in USER_DECISIONS:
        raise ValueError(f'invalid user decision {kind!r}')
    latest = latest_by_decision(read_events(root)).get(decision_id)
    if latest is None:
        raise ValueError(f'{decision_id} does not exist')
    if latest.get('event') not in PENDING:
        raise ValueError(f'{decision_id} is {latest.get("event")}, not pending')
    record = {'event_id': 'EVT-' + uuid.uuid4().hex, 'decision_id': decision_id, 'event': kind,
              'timestamp': now(), 'actor': actor, 'source': HOOK_SOURCE, 'title': latest.get('title', ''),
              'summary': _clean(note), 'evidence_ids': [], 'attestation': attestation}
    _append(root, record)
    set_record_status(root, decision_id, kind)
    return record


def add_evidence(root, *, evidence_id=None, claim, classification, source, method='', scope=''):
    root = Path(root)
    evidence_id = evidence_id or next_id(root, 'EVD')
    if not EVD_ID.match(evidence_id):
        raise ValueError('evidence ID must look like EVD-0001')
    if classification not in CLASSIFICATIONS:
        raise ValueError(f'classification must be one of {", ".join(CLASSIFICATIONS)}')
    if not claim.strip():
        raise ValueError('a claim is required')
    path = root / EVIDENCE / f'{evidence_id}.md'
    if path.exists():
        raise ValueError(f'{evidence_id} already exists')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'# {evidence_id}: {_clean(claim)}\n\n'
        f'- Classification: {classification}\n'
        f'- Source: {_clean(source) or "not stated"}\n'
        f'- Verification method: {_clean(method) or "not independently verified by simple-eng"}\n'
        f'- Date: {now()[:10]}\n'
        f'- Scope and limitations: {_clean(scope) or "verify source and scope before relying on this claim"}\n',
        encoding='utf-8')
    return path
