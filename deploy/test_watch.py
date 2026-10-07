import unittest
from unittest.mock import patch

import watch


class DeploymentTests(unittest.TestCase):
    def test_only_successful_master_push_from_expected_repository_is_eligible(self):
        run = dict(head_sha='a' * 40, head_branch='master', event='push',
                   status='completed', conclusion='success',
                   head_repository={'full_name': watch.REPO})
        self.assertTrue(watch.eligible(run, 'a' * 40))
        for key, value in [('head_sha', 'b' * 40), ('head_branch', 'feature'),
                           ('event', 'pull_request'), ('conclusion', 'failure'),
                           ('status', 'in_progress'),
                           ('head_repository', {'full_name': 'other/repo'})]:
            with self.subTest(key=key):
                self.assertFalse(watch.eligible(dict(run, **{key: value}), 'a' * 40))

    def state(self):
        return {'pending': {'id': 'a' * 32, 'sha': 'b' * 40,
                            'touched': list(watch.HOSTS),
                            'old_hashes': {host: 'c' * 64 for host in watch.HOSTS}}}

    @patch('watch.save')
    @patch('watch.remote')
    def test_recovery_rolls_back_both_hosts_in_reverse_order_and_blocks_commit(self, remote, save):
        state = self.state()
        watch.recover(state)
        self.assertEqual([call.args[0] for call in remote.call_args_list], list(reversed(watch.HOSTS)))
        self.assertNotIn('pending', state)
        self.assertEqual(state['failed_sha'], 'b' * 40)
        save.assert_called_once_with(state)

    @patch('watch.save')
    @patch('watch.remote', side_effect=[RuntimeError('host unreachable'), ''])
    def test_failed_rollback_retains_pending_state_and_still_tries_other_host(self, remote, save):
        state = self.state()
        with self.assertRaisesRegex(RuntimeError, 'Rollback incomplete'):
            watch.recover(state)
        self.assertIn('pending', state)
        self.assertEqual(remote.call_count, 2)
        save.assert_not_called()


if __name__ == '__main__':
    unittest.main()
