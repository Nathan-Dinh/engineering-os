"""End-to-end runs of bin/simple-eng in a temporary project."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import PLUGIN
from simple_eng.dashboard import render_dashboard

CLI = PLUGIN / 'bin/simple-eng'


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PROJECT_DIR'}

    def cli(self, *args, stdin=None, check=True):
        result = subprocess.run(['python3', str(CLI), '--root', str(self.root), *args], input=stdin,
                                capture_output=True, text=True, env=self.env, cwd=self.root)
        if check and result.returncode != 0:
            self.fail(f'simple-eng {args} failed: {result.stderr}')
        return result

    def test_project_lifecycle(self):
        self.assertNotEqual(self.cli('validate', check=False).returncode, 0)
        self.assertIn('Dry run', self.cli('init').stdout)
        self.assertFalse((self.root / 'CLAUDE.md').exists())
        self.cli('init', '--apply')
        self.assertTrue((self.root / 'docs/STATE.md').is_file())
        self.assertIn('Validation passed', self.cli('validate').stdout)
        self.assertIn('- stack: missing', self.cli('status').stdout)
        report = json.loads(self.cli('status', '--json', '--workflow', 'feature-development').stdout)
        self.assertIn('commands', report['blocking'])
        self.cli('add-evidence', '--claim', 'Python project', '--classification', 'verified', '--source', 'pyproject.toml')
        out = self.cli('add-decision', '--title', 'Use SQLite', '--summary', 'small data', '--actor', 'claude', '--evidence', 'EVD-0001').stdout
        self.assertIn('DEC-0001', out)
        self.assertIn('not an approval', out)
        self.assertNotEqual(self.cli('add-decision', '--id', 'DEC-0001', '--event', 'approved', '--actor', 'claude', check=False).returncode, 0)
        self.assertIn('Latest: proposed', self.cli('show', 'DEC-0001').stdout)
        self.assertIn('DEC-0001 "Use SQLite"', self.cli('context').stdout)
        self.cli('dashboard', '--output', str(self.root / 'dash.html'))
        self.assertIn('Use SQLite', (self.root / 'dash.html').read_text())

    def test_hook_entry_points(self):
        self.cli('init', '--apply')
        denied = self.cli('hook', 'pre-tool-use', stdin=json.dumps(
            {'tool_name': 'Write', 'tool_input': {'file_path': str(self.root / 'decision-log/events.jsonl')}})).stdout
        self.assertEqual(json.loads(denied)['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.cli('hook', 'pre-tool-use', stdin='{"tool_name": "Read"}').stdout, '')
        self.assertIn('simple-eng project context', self.cli('hook', 'session-start', stdin='{}').stdout)

    def test_plugin_validation_and_budget(self):
        self.assertIn('Validation passed for plugin guidance', self.cli('validate', '--plugin').stdout)
        self.assertIn('initialize-project', self.cli('budget').stdout)


class DashboardTests(unittest.TestCase):
    def test_escapes_html(self):
        page = render_dashboard([{'decision_id': 'DEC-0001', 'event': 'proposed', 'actor': 'ai',
                                  'timestamp': '2026-01-01T00:00:00+00:00', 'title': '<script>alert(1)</script>', 'summary': 't'}])
        self.assertIn('&lt;script&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)


if __name__ == '__main__':
    unittest.main()
