"""
Tests for the models module.
"""
import unittest
from gitlab_stats.models import CommitStats, UserStats

class TestModels(unittest.TestCase):
    def setUp(self):
        self.commit_stats = CommitStats(
            sha='abc123',
            title='Test commit',
            message='Test commit message',
            authored_date='2023-01-01T12:00:00Z',
            project_id=1,
            project_name='test-project',
            branch='main',
            stats={'additions': 10, 'deletions': 5, 'total': 15}
        )
        
        self.commit_stats2 = CommitStats(
            sha='def456',
            title='Test commit 2',
            message='Test commit message 2',
            authored_date='2023-01-02T12:00:00Z',
            project_id=1,
            project_name='test-project',
            branch='feature',
            stats={'additions': 5, 'deletions': 3, 'total': 8}
        )
        
        self.user_stats = UserStats(
            username='testuser',
            total_commits=2,
            commits=[self.commit_stats, self.commit_stats2],
            created_at='2023-01-01T00:00:00Z',
            last_activity_at='2023-01-02T12:00:00Z'
        )

    def test_commit_size(self):
        self.assertEqual(self.commit_stats.size, 15)

    def test_user_stats_total_changes(self):
        changes = self.user_stats.get_total_changes()
        self.assertEqual(changes['additions'], 10)
        self.assertEqual(changes['deletions'], 5)
        self.assertEqual(changes['total'], 15)

    def test_user_stats_commit_dates(self):
        dates = self.user_stats.get_commit_dates()
        self.assertEqual(len(dates), 2)
        self.assertEqual(dates[0], '2023-01-01T12:00:00Z')
        self.assertEqual(dates[1], '2023-01-02T12:00:00Z')
        
    def test_user_stats_branch_count(self):
        """Test counting unique branches."""
        self.assertEqual(self.user_stats.get_branch_count(), 2)