import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1] / 'plugin'
sys.path.insert(0, str(PLUGIN / 'lib'))

from simple_eng import records, scaffold  # noqa: E402


class ProjectCase(unittest.TestCase):
    """A temporary, initialized simple-eng project with a git identity."""

    git_email = 'owner@example.com'

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        env = mock.patch.dict(os.environ, {'CLAUDE_PROJECT_DIR': str(self.root)})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(self._tmp.cleanup)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        if self.git_email:
            subprocess.run(['git', '-C', str(self.root), 'config', 'user.email', self.git_email], check=True)
            subprocess.run(['git', '-C', str(self.root), 'config', 'user.name', 'Owner'], check=True)
        scaffold.apply_changes(self.root, scaffold.planned_changes(self.root))

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def read(self, rel):
        return (self.root / rel).read_text(encoding='utf-8')

    def events(self):
        return records.read_events(self.root)

    def propose(self, title='Use PostgreSQL', **kw):
        return records.add_decision(self.root, title=title, summary='s', actor='claude', **kw)


def event(**overrides):
    base = {'event_id': 'EVT-' + 'a' * 32, 'decision_id': 'DEC-0001', 'event': 'proposed',
            'timestamp': '2026-01-01T00:00:00+00:00', 'actor': 'claude', 'source': records.CLI_SOURCE}
    base.update(overrides)
    return base


def plugin_copy(test):
    """Copy the plugin to a temp dir so a test can break it."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    dest = Path(tmp.name) / 'plugin'
    shutil.copytree(PLUGIN, dest, ignore=shutil.ignore_patterns('.git', 'tests', '__pycache__'))
    return dest


def dump(obj):
    return json.dumps(obj)
