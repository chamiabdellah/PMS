import unittest
from unittest.mock import patch, MagicMock
from gitlab_stats import GitLabStats

class TestGitLabStats(unittest.TestCase):
    def setUp(self):
        self.gitlab_stats = GitLabStats('dummy_token')
        
    @patch('requests.get')
    def test_get_user_info(self, mock_get):
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Test User',
            'username': 'test_user'
        }
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.gitlab_stats.get_user_info()
        
        # Verify the results
        self.assertEqual(result['name'], 'Test User')
        self.assertEqual(result['username'], 'test_user')
        mock_get.assert_called_once_with(
            'https://gitlab.com/api/v4/user',
            headers={'PRIVATE-TOKEN': 'dummy_token'}
        )
        
    @patch('requests.get')
    def test_get_user_commits(self, mock_get):
        # Prepare mock responses
        mock_response = MagicMock()
        mock_response.json.side_effect = [
            [  # First page
                {
                    'action_name': 'pushed to',
                    'project_id': 1,
                    'push_data': {'commit_id': 'abc123'}
                }
            ],
            []  # Second page (empty, ends pagination)
        ]
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.gitlab_stats.get_user_commits()
        
        # Verify the results
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['project_id'], 1)
        self.assertEqual(result[0]['push_data']['commit_id'], 'abc123')
        
    @patch('requests.get')
    def test_get_commit_stats(self, mock_get):
        # Prepare mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'id': 'abc123',
            'stats': {
                'additions': 10,
                'deletions': 5
            }
        }
        mock_get.return_value = mock_response
        
        # Test the method
        result = self.gitlab_stats.get_commit_stats(1, 'abc123')
        
        # Verify the results
        self.assertEqual(result['stats']['additions'], 10)
        self.assertEqual(result['stats']['deletions'], 5)
        mock_get.assert_called_once_with(
            'https://gitlab.com/api/v4/projects/1/repository/commits/abc123',
            headers={'PRIVATE-TOKEN': 'dummy_token'}
        )
        
    @patch('gitlab_stats.GitLabStats.get_user_commits')
    @patch('gitlab_stats.GitLabStats.get_commit_stats')
    def test_get_contribution_summary(self, mock_get_stats, mock_get_commits):
        # Prepare mock responses
        mock_get_commits.return_value = [
            {
                'project_id': 1,
                'created_at': '2023-01-01T12:00:00Z',
                'push_data': {'commit_id': 'abc123'}
            },
            {
                'project_id': 2,
                'created_at': '2023-01-02T12:00:00Z',
                'push_data': {'commit_id': 'def456'}
            }
        ]
        
        mock_get_stats.side_effect = [
            {'stats': {'additions': 10, 'deletions': 5}},
            {'stats': {'additions': 20, 'deletions': 8}}
        ]
        
        # Test the method
        result = self.gitlab_stats.get_contribution_summary()
        
        # Verify the results
        self.assertEqual(result['total_commits'], 2)
        self.assertEqual(result['total_additions'], 30)
        self.assertEqual(result['total_deletions'], 13)
        self.assertEqual(result['projects_contributed_to'], 2)
        self.assertEqual(len(result['commit_dates']), 2)
        self.assertEqual(min(result['commit_dates']), '2023-01-01T12:00:00Z')
        self.assertEqual(max(result['commit_dates']), '2023-01-02T12:00:00Z')

if __name__ == '__main__':
    unittest.main()