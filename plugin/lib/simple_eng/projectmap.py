"""Knowledge areas a project should record, and whether each one is recorded.

Status only checks presence and structure. Whether the recorded content is correct is for the user to confirm.
"""
import json
from pathlib import Path

from . import PLUGIN_ROOT
from .markdown import meaningful_lines, not_applicable_reason, parse_frontmatter, section
from .paths import load_config

PRESENT, MISSING, NOT_APPLICABLE, BROKEN = 'present', 'missing', 'not applicable', 'broken'


def load_map(plugin_root=PLUGIN_ROOT):
    data = json.loads((Path(plugin_root) / 'reference/project-map.json').read_text(encoding='utf-8'))
    return data['areas']


def split_record(record):
    path, _, heading = record.partition('#')
    return path, heading


def area_record(area, config):
    override = (config.get('areas') or {}).get(area['id'], {})
    record = override.get('record') if isinstance(override, dict) else None
    return (record or area['record']), bool(record)


def area_status(root, area, config):
    record, overridden = area_record(area, config)
    path, heading = split_record(record)
    result = {'id': area['id'], 'record': record, 'source': area['source'],
              'question': area['question'], 'applies_when': area.get('applies_when')}
    override = (config.get('areas') or {}).get(area['id'], {})
    if isinstance(override, dict) and str(override.get('not_applicable', '')).strip():
        return dict(result, status=NOT_APPLICABLE, detail=override['not_applicable'].strip())
    file = Path(root) / path
    if not file.is_file():
        return dict(result, status=BROKEN if overridden else MISSING,
                    detail=f'{path} does not exist' + (' (configured override)' if overridden else ''))
    text = file.read_text(encoding='utf-8')
    body = section(text, heading) if heading else text
    if body is None:
        return dict(result, status=MISSING, detail=f'no "{heading}" heading in {path}')
    reason = not_applicable_reason(body)
    if reason:
        return dict(result, status=NOT_APPLICABLE, detail=reason)
    if not meaningful_lines(body):
        return dict(result, status=MISSING, detail=f'"{heading or path}" has no recorded content')
    return dict(result, status=PRESENT, detail='')


def workflow_needs(workflow, plugin_root=PLUGIN_ROOT):
    skill = Path(plugin_root) / 'skills' / workflow / 'SKILL.md'
    if not skill.is_file():
        raise ValueError(f'unknown workflow {workflow!r}')
    meta, _ = parse_frontmatter(skill.read_text(encoding='utf-8'))
    return list(meta.get('needs', []))


def status_report(root, plugin_root=PLUGIN_ROOT, workflow=None):
    config = load_config(root)
    areas = [area_status(root, area, config) for area in load_map(plugin_root)]
    report = {'areas': areas, 'workflow': workflow, 'blocking': []}
    if workflow:
        needs = set(workflow_needs(workflow, plugin_root))
        report['blocking'] = [a['id'] for a in areas if a['id'] in needs and a['status'] in (MISSING, BROKEN)]
    return report


def render_status(report):
    lines = ['Knowledge areas (presence and structure only; correctness is for the user to confirm):']
    for a in report['areas']:
        note = f' ({a["detail"]})' if a['detail'] and a['status'] != PRESENT else ''
        cond = f' [applies when {a["applies_when"]}]' if a.get('applies_when') and a['status'] in (MISSING, BROKEN) else ''
        lines.append(f'- {a["id"]}: {a["status"]} -> {a["record"]}{note}{cond}')
    gaps = [a for a in report['areas'] if a['status'] in (MISSING, BROKEN)]
    if gaps:
        lines.append('Missing areas to investigate in the repository first: '
                     + (', '.join(a['id'] for a in gaps if a['source'] == 'investigate') or 'none'))
        lines.append('Missing areas only a person can answer: '
                     + (', '.join(a['id'] for a in gaps if a['source'] == 'ask') or 'none'))
    if report['workflow']:
        blocking = ', '.join(report['blocking']) or 'none'
        lines.append(f'Missing areas that block {report["workflow"]}: {blocking}')
    return '\n'.join(lines)


def summary_line(report):
    groups = {}
    for a in report['areas']:
        key = f'missing ({a["source"]})' if a['status'] == MISSING else a['status']
        groups.setdefault(key, []).append(a['id'])
    order = ('missing (investigate)', 'missing (ask)', BROKEN, NOT_APPLICABLE, PRESENT)
    return '; '.join(f'{key}: {", ".join(groups[key])}' for key in order if key in groups)
