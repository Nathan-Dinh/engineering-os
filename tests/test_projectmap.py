import json
import unittest

from helpers import ProjectCase
from simple_eng import projectmap


def statuses(root, workflow=None):
    report = projectmap.status_report(root, workflow=workflow)
    return {a['id']: a['status'] for a in report['areas']}, report


class ProjectMapTests(ProjectCase):
    def test_fresh_project_is_all_missing(self):
        found, _ = statuses(self.root)
        self.assertEqual(set(found.values()), {'missing'})
        self.assertIn('stack', found)

    def test_filled_section_is_present(self):
        text = self.read('docs/PROJECT.md').replace('## Stack\n', '## Stack\n\n- Python 3.12, Django 5 (verified: pyproject.toml)\n')
        self.write('docs/PROJECT.md', text)
        self.assertEqual(statuses(self.root)[0]['stack'], 'present')

    def test_placeholder_only_content_is_missing(self):
        template = (projectmap.PLUGIN_ROOT / 'reference/templates/requirements.md').read_text()
        self.write('docs/product/requirements.md', template)
        self.assertEqual(statuses(self.root)[0]['requirements'], 'missing')
        self.write('docs/product/requirements.md', template.replace(
            '|---|---|---|---|---|---|\n', '|---|---|---|---|---|---|\n| REQ-0001 | functional | Search under 1s | user-provided | open | user, 2026-10-25 |\n', 1))
        self.assertEqual(statuses(self.root)[0]['requirements'], 'present')

    def test_not_applicable_in_record(self):
        self.write('docs/design/notes.md', '## Users and primary journeys\n\nNot applicable: CLI tool with no UI (verified: no frontend code).\n')
        found, report = statuses(self.root)
        self.assertEqual(found['ui'], 'not applicable')
        self.assertIn('CLI tool', next(a['detail'] for a in report['areas'] if a['id'] == 'ui'))

    def test_overrides(self):
        self.write('ARCHITECTURE.md', '# Overview\n\nTwo services and a queue.\n')
        config = json.loads(self.read('.simple-eng/config.json'))
        config['areas'] = {'architecture': {'record': 'ARCHITECTURE.md#Overview'},
                           'data-model': {'record': 'docs/missing.md#Entities'},
                           'ui': {'not_applicable': 'library with no interface'}}
        self.write('.simple-eng/config.json', json.dumps(config))
        found, _ = statuses(self.root)
        self.assertEqual(found['architecture'], 'present')
        self.assertEqual(found['data-model'], 'broken')
        self.assertEqual(found['ui'], 'not applicable')

    def test_workflow_blocking(self):
        _, report = statuses(self.root, 'architecture-design')
        self.assertEqual(set(report['blocking']), {'problem-users', 'requirements', 'quality-priorities', 'constraints', 'decision-owners'})
        self.assertIn('Missing areas that block architecture-design', projectmap.render_status(report))
        with self.assertRaises(ValueError):
            projectmap.status_report(self.root, workflow='no-such-skill')

    def test_summary_groups_by_source(self):
        summary = projectmap.summary_line(statuses(self.root)[1])
        self.assertIn('missing (investigate): stack', summary)
        self.assertIn('missing (ask): problem-users', summary)


if __name__ == '__main__':
    unittest.main()
