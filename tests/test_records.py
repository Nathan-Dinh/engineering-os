import unittest

from helpers import ProjectCase, event, records


class EventValidationTests(unittest.TestCase):
    def test_valid_proposal(self):
        self.assertEqual(records.validate_events([event()]), [])

    def test_duplicate_event_id(self):
        errors = records.validate_events([event(), event(event='evaluated')])
        self.assertTrue(any('duplicate event_id' in e for e in errors))

    def test_unknown_field_rejected(self):
        errors = records.validate_events([event(extra='x')])
        self.assertTrue(any('unknown fields' in e for e in errors))

    def test_first_event_must_be_proposed(self):
        errors = records.validate_events([event(event='evaluated')])
        self.assertTrue(any("'evaluated' is not allowed as the first event" in e for e in errors))

    def test_nothing_after_rejection(self):
        rejected = event(event_id='EVT-' + 'b' * 32, event='rejected', source=records.HOOK_SOURCE,
                         attestation='UserPromptExpansion;session=s1;prompt-sha256=' + '0' * 64)
        later = event(event_id='EVT-' + 'c' * 32, event='evaluated')
        errors = records.validate_events([event(), rejected, later])
        self.assertTrue(any("'evaluated' is not allowed after 'rejected'" in e for e in errors))

    def test_approval_from_cli_rejected(self):
        approval = event(event_id='EVT-' + 'b' * 32, event='approved', attestation='anything')
        errors = records.validate_events([event(), approval])
        self.assertTrue(any('must come from the approval hook' in e for e in errors))

    def test_approval_from_hook_accepted(self):
        approval = event(event_id='EVT-' + 'b' * 32, event='approved', source=records.HOOK_SOURCE,
                         attestation='UserPromptExpansion;session=s1;prompt-sha256=' + 'f' * 64)
        self.assertEqual(records.validate_events([event(), approval]), [])

    def test_implemented_needs_prior_approval_and_attestation(self):
        errors = records.validate_events([event(), event(event_id='EVT-' + 'b' * 32, event='implemented')])
        self.assertTrue(any('need an attestation' in e for e in errors))
        self.assertTrue(any("'implemented' is not allowed after 'proposed'" in e for e in errors))

    def test_superseded_needs_target(self):
        errors = records.validate_events([event(), event(event_id='EVT-' + 'b' * 32, event='superseded')])
        self.assertTrue(any('superseded_by' in e for e in errors))

    def test_types_and_timestamp(self):
        errors = records.validate_events([event(title=3, timestamp='2026-01-01T00:00:00')])
        self.assertTrue(any('title must be a string' in e for e in errors))
        self.assertTrue(any('timezone' in e for e in errors))


class RecordTests(ProjectCase):
    def test_fresh_project_validates(self):
        self.assertEqual(records.validate_records(self.root), [])

    def test_invalid_json_reported(self):
        self.write('decision-log/events.jsonl', '{bad json}\n')
        with self.assertRaises(ValueError):
            records.read_events(self.root)
        self.assertTrue(records.validate_records(self.root))

    def test_dangling_requirement_reference(self):
        self.write('docs/features/FEAT-0001.md', '# FEAT-0001: Search\n\nImplements REQ-0099.\n')
        errors = records.validate_records(self.root)
        self.assertTrue(any('REQ-0099 is referenced but never defined' in e for e in errors))

    def test_mention_in_a_record_does_not_define_it(self):
        # The old validator treated any mention as a definition, so this passed silently.
        self.propose(title='Cache results')
        path = self.root / 'docs/decisions/records/DEC-0001.md'
        path.write_text(path.read_text() + '\nSatisfies REQ-0042.\n')
        self.assertTrue(any('REQ-0042' in e for e in records.validate_records(self.root)))

    def test_table_definition_resolves_and_duplicates_fail(self):
        self.write('docs/product/requirements.md', '## Requirements\n\n| ID | Requirement |\n|---|---|\n| REQ-0001 | Fast search |\n')
        self.write('docs/features/FEAT-0001.md', '# FEAT-0001: Search\n\nCovers REQ-0001.\n')
        self.assertEqual(records.validate_records(self.root), [])
        self.write('docs/other.md', '| REQ-0001 | Duplicate |\n')
        self.assertTrue(any('REQ-0001 is defined more than once' in e for e in records.validate_records(self.root)))

    def test_add_decision_creates_record_with_status(self):
        rec = self.propose()
        self.assertEqual(rec['decision_id'], 'DEC-0001')
        text = self.read('docs/decisions/records/DEC-0001.md')
        self.assertIn('# DEC-0001: Use PostgreSQL', text)
        self.assertIn('- Status: proposed', text)
        self.assertEqual(self.propose(title='Second')['decision_id'], 'DEC-0002')
        records.add_decision(self.root, decision_id='DEC-0001', event='evaluated', actor='claude')
        self.assertIn('- Status: evaluated', self.read('docs/decisions/records/DEC-0001.md'))
        self.assertEqual(records.validate_records(self.root), [])

    def test_add_decision_refuses_high_authority(self):
        self.propose()
        for kind in ('approved', 'rejected', 'implemented', 'verified'):
            with self.assertRaises(ValueError):
                records.add_decision(self.root, decision_id='DEC-0001', event=kind, actor='claude')

    def test_status_mismatch_detected(self):
        self.propose()
        path = self.root / 'docs/decisions/records/DEC-0001.md'
        path.write_text(path.read_text().replace('- Status: proposed', '- Status: approved'))
        self.assertTrue(any("Status is 'approved' but the latest event is 'proposed'" in e
                            for e in records.validate_records(self.root)))

    def test_record_without_events(self):
        self.write('docs/decisions/records/DEC-0007.md', '# DEC-0007: Orphan\n\n- Status: proposed\n')
        self.assertTrue(any('no events for DEC-0007' in e for e in records.validate_records(self.root)))

    def test_evidence_links(self):
        with self.assertRaises(ValueError):
            self.propose(evidence=['EVD-0001'])
        records.add_evidence(self.root, claim='Uses Django', classification='verified', source='requirements.txt')
        rec = self.propose(evidence=['EVD-0001'])
        self.assertEqual(rec['evidence_ids'], ['EVD-0001'])
        self.assertIn('- Evidence: EVD-0001', self.read('docs/decisions/records/DEC-0001.md'))
        self.assertEqual(records.validate_records(self.root), [])

    def test_add_evidence_rules(self):
        path = records.add_evidence(self.root, claim='Has CI', classification='inferred', source='.github/')
        self.assertEqual(path.name, 'EVD-0001.md')
        with self.assertRaises(ValueError):
            records.add_evidence(self.root, evidence_id='EVD-0001', claim='x', classification='inferred', source='y')
        with self.assertRaises(ValueError):
            records.add_evidence(self.root, claim='x', classification='certain', source='y')

    def test_supersede(self):
        self.propose(title='Old')
        self.propose(title='New')
        records.add_decision(self.root, decision_id='DEC-0001', event='superseded', actor='claude', superseded_by='DEC-0002')
        self.assertEqual(records.validate_records(self.root), [])
        with self.assertRaises(ValueError):
            records.add_decision(self.root, decision_id='DEC-0002', event='superseded', actor='claude')

    def test_hook_decision_requires_pending(self):
        self.propose()
        attestation = 'UserPromptExpansion;session=s;prompt-sha256=' + '1' * 64
        records.record_user_decision(self.root, decision_id='DEC-0001', kind='approved', note='', actor='o', attestation=attestation)
        with self.assertRaises(ValueError):
            records.record_user_decision(self.root, decision_id='DEC-0001', kind='approved', note='', actor='o', attestation=attestation)
        self.assertEqual(records.validate_records(self.root), [])


if __name__ == '__main__':
    unittest.main()
