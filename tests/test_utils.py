"""
Tests for the utils module.
"""
import unittest
import os
import json
from gitlab_stats.utils import format_datetime, export_stats_to_json
from gitlab_stats.models import CommitStats, UserStats

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.commit_stats = CommitStats(
            sha='abc123',
            title='Test commit',
            message='Test commit message',
            authored_date='2023-01-01T12:00:00Z',
            project_id=1,
            project_name='test-project',
            stats={'additions': 10, 'deletions': 5, 'total': 15}
        )
        
        self.user_stats = UserStats(
            username='testuser',
            total_commits=1,
            commits=[self.commit_stats],
            created_at='2023-01-01T00:00:00Z',
            last_activity_at='2023-01-01T12:00:00Z'
        )

    def test_format_datetime(self):
        formatted = format_datetime('2023-01-01T12:00:00Z')
        self.assertEqual(formatted, '2023-01-01 12:00:00')

    def test_export_stats_to_json(self):
        test_file = 'test_stats.json'
        export_stats_to_json(self.user_stats, test_file)
        
        self.assertTrue(os.path.exists(test_file))
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['total_commits'], 1)
        self.assertEqual(len(data['commits']), 1)
        
        os.remove(test_file)