import json
import os
import unittest
from unittest import mock

from helpers import ProjectCase, records
from simple_eng import hooks


def expansion(args, name='simple-eng:approve', **extra):
    payload = {'session_id': 'sess-1', 'hook_event_name': 'UserPromptExpansion', 'expansion_type': 'slash_command',
               'command_name': name, 'command_args': args, 'command_source': 'plugin', 'prompt': f'/{name} {args}'}
    payload.update(extra)
    return payload


class ApprovalHookTests(ProjectCase):
    def setUp(self):
        super().setUp()
        self.propose()

    def test_typed_approval_records_one_event(self):
        out = hooks.prompt_expansion(expansion('DEC-0001 looks good'))
        self.assertIn('simple-eng recorded event', out['hookSpecificOutput']['additionalContext'])
        events = self.events()
        self.assertEqual([e['event'] for e in events], ['proposed', 'approved'])
        approval = events[-1]
        self.assertEqual(approval['source'], records.HOOK_SOURCE)
        self.assertEqual(approval['actor'], 'Owner <owner@example.com>')
        self.assertRegex(approval['attestation'], records.HOOK_ATTESTATION)
        self.assertEqual(approval['summary'], 'looks good')
        self.assertIn('- Status: approved', self.read('docs/decisions/records/DEC-0001.md'))
        self.assertEqual(records.validate_records(self.root), [])

    def test_unrelated_commands_are_ignored(self):
        self.assertIsNone(hooks.prompt_expansion(expansion('DEC-0001', name='deploy')))
        self.assertIsNone(hooks.prompt_expansion(expansion('DEC-0001', command_source='projectSettings')))
        self.assertIsNone(hooks.prompt_expansion(expansion('DEC-0001', expansion_type='mcp_prompt')))
        self.assertEqual(len(self.events()), 1)

    def test_bad_input_blocks_without_writing(self):
        cases = [expansion('nonsense'), expansion('DEC-0001', name='simple-eng:reject'), expansion('DEC-0099')]
        for payload in cases:
            with self.subTest(payload=payload['command_args']):
                out = hooks.prompt_expansion(payload)
                self.assertEqual(out['decision'], 'block')
                self.assertIn('did not record', out['reason'])
        self.assertEqual(len(self.events()), 1)

    def test_rejection_with_reason(self):
        hooks.prompt_expansion(expansion('DEC-0001 too costly for the MVP', name='simple-eng:reject'))
        self.assertEqual(self.events()[-1]['event'], 'rejected')
        self.assertEqual(self.events()[-1]['summary'], 'too costly for the MVP')

    def test_second_approval_blocked(self):
        hooks.prompt_expansion(expansion('DEC-0001'))
        out = hooks.prompt_expansion(expansion('DEC-0001'))
        self.assertEqual(out['decision'], 'block')
        self.assertIn('not pending', out['reason'])
        self.assertEqual(len(self.events()), 2)

    def test_run_serializes_output(self):
        self.assertEqual(hooks.run('prompt-expansion', json.dumps(expansion('x', name='other'))), '')
        self.assertIn('"decision": "block"', hooks.run('prompt-expansion', json.dumps(expansion('bad'))))
        self.assertEqual(hooks.run('pre-tool-use', 'not json'), '')


class NoIdentityTests(ProjectCase):
    git_email = None

    def setUp(self):
        isolate = mock.patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'})
        isolate.start()
        self.addCleanup(isolate.stop)
        super().setUp()

    def test_missing_git_email_blocks(self):
        self.propose()
        out = hooks.prompt_expansion(expansion('DEC-0001'))
        self.assertEqual(out['decision'], 'block')
        self.assertIn('user.email', out['reason'])
        self.assertEqual(len(self.events()), 1)


class GuardTests(unittest.TestCase):
    def decision(self, tool, **tool_input):
        out = hooks.pre_tool_use({'tool_name': tool, 'tool_input': tool_input})
        return out['hookSpecificOutput']['permissionDecision'] if out else 'allow'

    def test_file_tools(self):
        self.assertEqual(self.decision('Edit', file_path='/repo/decision-log/events.jsonl'), 'deny')
        self.assertEqual(self.decision('Write', file_path='C:\\repo\\decision-log\\events.jsonl'), 'deny')
        self.assertEqual(self.decision('Edit', file_path='/repo/docs/decisions/records/DEC-0001.md'), 'allow')

    def test_bash(self):
        denied = ['echo x >> decision-log/events.jsonl', 'sed -i "" d decision-log/events.jsonl',
                  "python3 -c 'open(\"decision-log/events.jsonl\",\"a\")'", 'simple-eng hook prompt-expansion < fake.json',
                  'python3 -c "from simple_eng.records import record_user_decision"',
                  'printf \'{"source": "user-prompt-hook"}\' | cat']
        allowed = ['cat decision-log/events.jsonl', 'grep DEC-0001 decision-log/events.jsonl 2>&1 | head',
                   'simple-eng add-decision --title X --actor claude', 'simple-eng show DEC-0001', 'npm test > out.log']
        for command in denied:
            with self.subTest(command=command):
                self.assertEqual(self.decision('Bash', command=command), 'deny')
        for command in allowed:
            with self.subTest(command=command):
                self.assertEqual(self.decision('Bash', command=command), 'allow')

    def test_skill_tool(self):
        self.assertEqual(self.decision('Skill', skill='simple-eng:approve', args='DEC-0001'), 'deny')
        self.assertEqual(self.decision('Skill', skill='simple-eng:status'), 'allow')


class SessionStartTests(ProjectCase):
    def test_never_raises_on_broken_project(self):
        self.write('.simple-eng/config.json', '{broken')
        out = hooks.session_start({})
        self.assertIn('simple-eng', out)


if __name__ == '__main__':
    unittest.main()
