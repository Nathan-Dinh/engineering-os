"""Structural checks for the plugin's own guidance: skills, references, project map, and token budgets.

Budgets use a bytes/4 estimate of tokens, not a tokenizer.
"""
import json
import re
from pathlib import Path

from . import PLUGIN_ROOT
from .markdown import headings, parse_frontmatter
from .projectmap import load_map, split_record

DESCRIPTION_LIMIT = 1536          # Claude Code truncates skill listings beyond this.
BLOCK_BUDGET = 4800               # CLAUDE.md block, always loaded (~1.2k tokens).
DESCRIPTIONS_BUDGET = 3200        # model-invocable skill descriptions, always loaded (~800 tokens).
LOAD_BUDGET = 12000               # one workflow skill plus the guidance it reads (~3k tokens).
PLUGIN_REF = re.compile(r'\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)')
SKILL_REF = re.compile(r'\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)')
LINK = re.compile(r'\]\((?!https?://|#|mailto:)([^)#\s]+)')
GUIDANCE_DIRS = ('policies', 'rubrics')


def skills(plugin_root=PLUGIN_ROOT):
    found = {}
    for path in sorted((Path(plugin_root) / 'skills').glob('*/SKILL.md')):
        meta, body = parse_frontmatter(path.read_text(encoding='utf-8'))
        found[path.parent.name] = {'path': path, 'meta': meta, 'body': body}
    return found


def _refs(path, plugin_root):
    text = path.read_text(encoding='utf-8')
    refs = [Path(plugin_root) / rel for rel in PLUGIN_REF.findall(text)]
    refs += [path.parent / rel for rel in SKILL_REF.findall(text)]
    refs += [(path.parent / rel) for rel in LINK.findall(text)]
    return refs


def _guidance_refs(path, plugin_root):
    root = Path(plugin_root).resolve()
    out = []
    for ref in _refs(path, plugin_root):
        ref = ref.resolve()
        if ref.is_file() and ref.suffix == '.md' and ref.relative_to(root).parts[0] in GUIDANCE_DIRS:
            out.append(ref)
    return out


def load_sets(plugin_root=PLUGIN_ROOT):
    """Bytes loaded per workflow: SKILL.md plus the policies/rubrics it points to, and for each supporting
    file in the skill directory (such as a phase file) that file plus its own policy/rubric references."""
    table = {}
    for name, skill in skills(plugin_root).items():
        base = {skill['path'].resolve(), *_guidance_refs(skill['path'], plugin_root)}
        size = lambda files: sum(f.stat().st_size for f in files)
        rows = [('SKILL.md', size(base))]
        for ref in sorted(set(r.resolve() for r in _refs(skill['path'], plugin_root))):
            if ref.is_file() and ref.parent == skill['path'].parent.resolve() and ref.name != 'SKILL.md':
                rows.append((ref.name, size(base | {ref} | set(_guidance_refs(ref, plugin_root)))))
        table[name] = rows
    return table


def check_plugin(plugin_root=PLUGIN_ROOT):
    root = Path(plugin_root)
    errors = []
    area_ids = [a['id'] for a in load_map(root)]
    if len(area_ids) != len(set(area_ids)):
        errors.append('project-map.json: duplicate area ids')
    for area in load_map(root):
        path, heading = split_record(area['record'])
        template = root / 'templates' / area.get('template', '')
        if area['source'] not in ('ask', 'investigate'):
            errors.append(f'project-map.json {area["id"]}: source must be ask or investigate')
        if not path.startswith('docs/') or not heading:
            errors.append(f'project-map.json {area["id"]}: record must be docs/<file>.md#<Heading>')
        if not template.is_file():
            errors.append(f'project-map.json {area["id"]}: template {area.get("template")} not found')
        elif heading.lower() not in (h.lower() for h in headings(template.read_text(encoding='utf-8'))):
            errors.append(f'project-map.json {area["id"]}: heading "{heading}" not in templates/{area["template"]}')
    found = skills(root)
    if not found:
        errors.append('no skills found under skills/')
    descriptions = 0
    for name, skill in found.items():
        meta = skill['meta']
        where = f'skills/{name}/SKILL.md'
        description = str(meta.get('description', ''))
        if not description:
            errors.append(f'{where}: description is required')
        if len(description) > DESCRIPTION_LIMIT:
            errors.append(f'{where}: description is {len(description)} characters (limit {DESCRIPTION_LIMIT})')
        if 'disable-model-invocation' in meta and not isinstance(meta['disable-model-invocation'], bool):
            errors.append(f'{where}: disable-model-invocation must be true or false')
        if not meta.get('disable-model-invocation'):
            descriptions += len(description)
        for need in meta.get('needs', []):
            if need not in area_ids:
                errors.append(f'{where}: needs unknown area {need!r}')
    for path in sorted([*root.glob('skills/**/*.md'), *root.glob('policies/*.md'), *root.glob('rubrics/*.md')]):
        for ref in _refs(path, root):
            if not ref.exists():
                errors.append(f'{path.relative_to(root)}: reference to missing file {ref}')
    block = (root / 'templates/claude-md-block.md').stat().st_size
    if block > BLOCK_BUDGET:
        errors.append(f'templates/claude-md-block.md is {block} bytes (budget {BLOCK_BUDGET})')
    if descriptions > DESCRIPTIONS_BUDGET:
        errors.append(f'model-invocable skill descriptions total {descriptions} characters (budget {DESCRIPTIONS_BUDGET})')
    for name, rows in load_sets(root).items():
        for part, size in rows:
            if size > LOAD_BUDGET:
                errors.append(f'skills/{name} ({part}) loads {size} bytes (budget {LOAD_BUDGET})')
    hooks = json.loads((root / 'hooks/hooks.json').read_text(encoding='utf-8'))
    for event, groups in hooks.get('hooks', {}).items():
        for group in groups:
            for handler in group.get('hooks', []):
                for rel in PLUGIN_REF.findall(json.dumps(handler)):
                    if not (root / rel).exists():
                        errors.append(f'hooks/hooks.json {event}: missing {rel}')
    return errors


def budget_report(plugin_root=PLUGIN_ROOT):
    root = Path(plugin_root)
    found = skills(root)
    always = sum(len(str(s['meta'].get('description', ''))) for s in found.values() if not s['meta'].get('disable-model-invocation'))
    lines = ['Estimated tokens (bytes / 4):',
             f'- always loaded: CLAUDE.md block {(root / "templates/claude-md-block.md").stat().st_size // 4}, '
             f'skill descriptions {always // 4}, SessionStart context up to {6000 // 4} (hard cap {9000 // 4})']
    for name, rows in load_sets(root).items():
        lines.append(f'- {name}: ' + ', '.join(f'{part} {size // 4}' for part, size in rows))
    return '\n'.join(lines)
