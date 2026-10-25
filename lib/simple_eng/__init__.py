"""simple-eng: project state, records, and hooks for the Claude Code plugin."""
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def plugin_version(plugin_root=PLUGIN_ROOT):
    try:
        manifest = json.loads((plugin_root / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        return str(manifest.get('version', '0.0.0'))
    except (OSError, ValueError):
        return '0.0.0'
