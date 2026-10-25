"""Project setup for /simple-eng:init. Dry run by default; only the marked CLAUDE.md block is ever replaced."""
import datetime as dt
import difflib
import json
import re
from pathlib import Path

from . import PLUGIN_ROOT, plugin_version
from .paths import CONFIG, PROJECT, STATE

START = '<!-- simple-eng:start version={version} -->'
END = '<!-- simple-eng:end -->'
BLOCK = re.compile(r'<!-- simple-eng:start[^>]*-->.*?<!-- simple-eng:end -->', re.DOTALL)


def claude_md_block(plugin_root=PLUGIN_ROOT):
    body = (Path(plugin_root) / 'templates/claude-md-block.md').read_text(encoding='utf-8').strip()
    return f'{START.format(version=plugin_version(plugin_root))}\n{body}\n{END}'


def _with_block(existing, block):
    if existing is None:
        return block + '\n'
    if BLOCK.search(existing):
        return BLOCK.sub(lambda _: block, existing, count=1)
    return existing.rstrip('\n') + ('\n\n' if existing.strip() else '') + block + '\n'


def planned_changes(root, plugin_root=PLUGIN_ROOT):
    root = Path(root)
    changes = []

    def plan(rel, new):
        path = root / rel
        old = path.read_text(encoding='utf-8') if path.is_file() else None
        if old == new:
            changes.append({'path': rel, 'action': 'unchanged', 'content': new, 'diff': ''})
            return
        diff = ''.join(difflib.unified_diff((old or '').splitlines(True), new.splitlines(True),
                                            fromfile=f'a/{rel}' if old is not None else '/dev/null', tofile=f'b/{rel}'))
        changes.append({'path': rel, 'action': 'update' if old is not None else 'create', 'content': new, 'diff': diff})

    config_path = root / CONFIG
    config = json.loads(config_path.read_text(encoding='utf-8')) if config_path.is_file() else {}
    config.setdefault('initialized', dt.date.today().isoformat())
    config['framework_version'] = plugin_version(plugin_root)
    config.setdefault('areas', {})
    plan(CONFIG, json.dumps(config, indent=2) + '\n')
    claude = root / 'CLAUDE.md'
    plan('CLAUDE.md', _with_block(claude.read_text(encoding='utf-8') if claude.is_file() else None, claude_md_block(plugin_root)))
    for rel, template in ((PROJECT, 'project.md'), (STATE, 'state.md')):
        if not (root / rel).exists():
            plan(rel, (Path(plugin_root) / 'templates' / template).read_text(encoding='utf-8'))
    return changes


def apply_changes(root, changes):
    for change in changes:
        if change['action'] == 'unchanged':
            continue
        path = Path(root) / change['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(change['content'], encoding='utf-8')
