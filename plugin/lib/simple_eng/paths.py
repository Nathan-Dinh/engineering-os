"""Project layout and project-root discovery."""
import json
import os
import subprocess
from pathlib import Path

CONFIG = '.simple-eng/config.json'
PROJECT = 'docs/PROJECT.md'
STATE = 'docs/STATE.md'
LOG = 'decision-log/events.jsonl'
DECISIONS = 'docs/decisions/records'
EVIDENCE = 'docs/evidence/records'
DOCS = 'docs'


def git_toplevel(start):
    try:
        out = subprocess.run(['git', '-C', str(start), 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return Path(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None


def project_root(start=None):
    """CLAUDE_PROJECT_DIR when set, else the nearest directory holding .simple-eng/, else the git top level, else cwd."""
    env = os.environ.get('CLAUDE_PROJECT_DIR')
    if env and Path(env).is_dir():
        return Path(env).resolve()
    here = Path(start or os.getcwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / '.simple-eng').is_dir():
            return candidate
    return git_toplevel(here) or here


def is_initialized(root):
    return (Path(root) / CONFIG).is_file()


def load_config(root):
    path = Path(root) / CONFIG
    if not path.is_file():
        return {}
    try:
        config = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as exc:
        raise ValueError(f'{CONFIG} is not valid JSON: {exc}') from exc
    if not isinstance(config, dict):
        raise ValueError(f'{CONFIG} must contain a JSON object')
    if not isinstance(config.get('areas', {}), dict):
        raise ValueError(f'{CONFIG}: "areas" must be an object keyed by area id')
    return config
