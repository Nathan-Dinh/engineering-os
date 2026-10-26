import json
import tempfile
import unittest
from pathlib import Path

from helpers import scaffold


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def plan(self):
        return {c['path']: c for c in scaffold.planned_changes(self.root)}

    def test_fresh_project(self):
        changes = self.plan()
        self.assertEqual({c['action'] for c in changes.values()}, {'create'})
        self.assertEqual(set(changes), {'.simple-eng/config.json', 'CLAUDE.md', 'docs/PROJECT.md', 'docs/STATE.md'})
        self.assertFalse((self.root / 'CLAUDE.md').exists(), 'planning must not write')
        scaffold.apply_changes(self.root, changes.values())
        config = json.loads((self.root / '.simple-eng/config.json').read_text())
        self.assertIn('framework_version', config)
        self.assertIn('<!-- simple-eng:start version=', (self.root / 'CLAUDE.md').read_text())

    def test_existing_claude_md_preserved_and_rerun_idempotent(self):
        (self.root / 'CLAUDE.md').write_text('# My project\n\nUse tabs.\n')
        scaffold.apply_changes(self.root, scaffold.planned_changes(self.root))
        text = (self.root / 'CLAUDE.md').read_text()
        self.assertTrue(text.startswith('# My project\n\nUse tabs.\n'))
        self.assertEqual(text.count('simple-eng:start'), 1)
        self.assertEqual({c['action'] for c in scaffold.planned_changes(self.root)}, {'unchanged'})

    def test_old_block_replaced_and_project_files_kept(self):
        (self.root / 'CLAUDE.md').write_text('Intro\n\n<!-- simple-eng:start version=0.0.1 -->\nold rules\n<!-- simple-eng:end -->\n\nOutro\n')
        (self.root / 'docs').mkdir()
        (self.root / 'docs/PROJECT.md').write_text('# Mine\n')
        changes = self.plan()
        self.assertNotIn('docs/PROJECT.md', changes)
        self.assertIn('-old rules', changes['CLAUDE.md']['diff'])
        scaffold.apply_changes(self.root, changes.values())
        text = (self.root / 'CLAUDE.md').read_text()
        self.assertTrue(text.startswith('Intro\n') and text.rstrip().endswith('Outro'))
        self.assertNotIn('old rules', text)
        self.assertEqual((self.root / 'docs/PROJECT.md').read_text(), '# Mine\n')

    def test_missing_end_marker_refuses_instead_of_adding_a_second_block(self):
        (self.root / 'CLAUDE.md').write_text('Intro\n\n<!-- simple-eng:start version=0.0.1 -->\nold rules\n')
        with self.assertRaisesRegex(ValueError, 'no end marker'):
            scaffold.planned_changes(self.root)

    def test_malformed_config_is_a_clear_error(self):
        (self.root / '.simple-eng').mkdir()
        for text in ('[]', '{"areas": []}'):
            with self.subTest(config=text):
                (self.root / '.simple-eng/config.json').write_text(text)
                with self.assertRaisesRegex(ValueError, 'config.json'):
                    scaffold.planned_changes(self.root)


if __name__ == '__main__':
    unittest.main()
