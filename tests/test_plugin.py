"""Structural tests of the plugin's own guidance. They check text and layout, not live agent behavior."""
import json
import re
import unittest

from helpers import PLUGIN, plugin_copy, records
from simple_eng import guidance, markdown

CONSEQUENTIAL = 'production security changes'
USER_ONLY = ('init', 'approve', 'reject')


class PluginStructureTests(unittest.TestCase):
    def test_plugin_checks_pass(self):
        self.assertEqual(guidance.check_plugin(PLUGIN), [])

    def test_manifests(self):
        manifest = json.loads((PLUGIN / '.claude-plugin/plugin.json').read_text())
        market = json.loads((PLUGIN / '.claude-plugin/marketplace.json').read_text())
        self.assertEqual(manifest['name'], 'simple-eng')
        self.assertRegex(manifest['version'], r'^\d+\.\d+\.\d+$')
        self.assertEqual(market['plugins'][0]['name'], manifest['name'])
        self.assertFalse((PLUGIN / 'CLAUDE.md').exists(), 'a CLAUDE.md at the plugin root is not loaded and fails --strict validation')

    def test_hooks_cover_each_handler(self):
        hooks = json.loads((PLUGIN / 'hooks/hooks.json').read_text())['hooks']
        self.assertEqual(set(hooks), {'SessionStart', 'UserPromptExpansion', 'PreToolUse'})
        self.assertIn('compact', hooks['SessionStart'][0]['matcher'])
        commands = json.dumps(hooks)
        for name in ('session-start', 'prompt-expansion', 'pre-tool-use'):
            self.assertIn(name, commands)

    def test_user_only_skills(self):
        skills = guidance.skills(PLUGIN)
        for name in USER_ONLY:
            self.assertIs(skills[name]['meta'].get('disable-model-invocation'), True, name)
        for name, skill in skills.items():
            if name not in USER_ONLY:
                self.assertNotIn('disable-model-invocation', skill['meta'], name)

    def test_consequential_list_stated_once(self):
        holders = [p.relative_to(PLUGIN).as_posix() for p in PLUGIN.glob('**/*.md')
                   if 'tests' not in p.parts and CONSEQUENTIAL in p.read_text()]
        self.assertEqual(holders, ['templates/claude-md-block.md'])

    def test_claim_labels_agree(self):
        block = (PLUGIN / 'templates/claude-md-block.md').read_text()
        policy = (PLUGIN / 'policies/evidence.md').read_text()
        policy_labels = tuple(re.findall(r'^- \*\*([a-z-]+)\*\*:', policy, re.MULTILINE))
        self.assertEqual(policy_labels, records.CLASSIFICATIONS)
        for label in records.CLASSIFICATIONS:
            self.assertIn(label, block)

    def test_checkpoints_present(self):
        skill = (PLUGIN / 'skills/checkpoints/SKILL.md').read_text()
        state = (PLUGIN / 'templates/state.md').read_text()
        for letter in 'ABCDEFG':
            self.assertIn(f'**{letter} —', skill)
            self.assertIn(f'| {letter} —', state)

    def test_initialize_phases_ordered_and_loaded_lazily(self):
        skill = (PLUGIN / 'skills/initialize-project/SKILL.md').read_text()
        phases = re.findall(r'\$\{CLAUDE_SKILL_DIR\}/(phase-(\d)-[\w-]+\.md)', skill)
        self.assertEqual([int(n) for _, n in phases], [1, 2, 3, 4, 5, 6])
        for name, _ in phases:
            self.assertTrue((PLUGIN / 'skills/initialize-project' / name).is_file(), name)

    def test_block_and_state_template_have_no_real_ids(self):
        for rel in ('templates/claude-md-block.md', 'templates/state.md', 'templates/requirements.md'):
            self.assertEqual(records.ANY_ID.findall((PLUGIN / rel).read_text()), [], rel)

    def test_event_schema_matches_validator(self):
        schema = json.loads((PLUGIN / 'schemas/decision-event.schema.json').read_text())
        self.assertEqual(set(schema['properties']), records.FIELDS)
        self.assertEqual(set(schema['required']), records.REQUIRED)
        self.assertEqual(tuple(schema['properties']['event']['enum']), records.EVENTS)

    def test_frontmatter_parser(self):
        meta, body = markdown.parse_frontmatter('---\ndescription: a: b\nneeds: [x, y]\nflag: true\n---\n\nBody\n')
        self.assertEqual(meta, {'description': 'a: b', 'needs': ['x', 'y'], 'flag': True})
        self.assertEqual(body.strip(), 'Body')


class BrokenPluginTests(unittest.TestCase):
    def test_each_check_fails_on_a_broken_copy(self):
        breakages = {
            'unknown area': ('skills/status/SKILL.md', lambda t: t.replace('description:', 'needs: [nope]\ndescription:', 1), 'unknown area'),
            'missing reference': ('skills/maintain-project/SKILL.md', lambda t: t + '\nSee ${CLAUDE_PLUGIN_ROOT}/policies/gone.md\n', 'missing file'),
            'long description': ('skills/status/SKILL.md', lambda t: t.replace('description: ', 'description: ' + 'x' * 1600, 1), 'limit 1536'),
            'over budget': ('policies/evidence.md', lambda t: t + 'y' * 13000, 'budget'),
            'map heading': ('templates/project.md', lambda t: t.replace('## Stack', '## Tech'), 'heading "Stack"'),
        }
        for label, (rel, change, expected) in breakages.items():
            with self.subTest(label):
                root = plugin_copy(self)
                path = root / rel
                path.write_text(change(path.read_text()))
                errors = guidance.check_plugin(root)
                self.assertTrue(any(expected in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
