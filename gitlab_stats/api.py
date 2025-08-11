"""
GitLab API interaction module.
"""
import gitlab
from typing import Dict, List, Optional
from datetime import datetime
from .models import CommitStats, UserStats

class GitLabAPI:
    def __init__(self, url: str, private_token: str):
        """
        Initialize GitLab API client.
        
        Args:
            url: GitLab instance URL
            private_token: Personal access token
        """
        self.gl = gitlab.Gitlab(url, private_token=private_token)
        print('fetching gitlab user data')
        
    def get_user_stats(self, username: str) -> UserStats:
        """
        Get comprehensive statistics for a GitLab user.
        
        Args:
            username: GitLab username
        
        Returns:
            UserStats object containing user statistics
        """
        users = self.gl.users.list(username=username)
        if not users:
            raise ValueError(f"User '{username}' not found")
        user = users[0]
        commits = self._get_user_commits(user.id)
        return UserStats(
            username=username,
            total_commits=len(commits),
            commits=commits,
            created_at=user.created_at,
            last_activity_at=user.last_activity_on
        )
    
    def _get_user_commits(self, user_id: int) -> List[CommitStats]:
        """
        Get all commits for a user across all projects they have access to.
        
        Args:
            user_id: GitLab user ID
        
        Returns:
            List of CommitStats objects
        """
        commits = []
        for project in self.gl.projects.list(all=True):
            try:
                project_commits = project.commits.list(
                    all=True,
                    query_parameters={'author_id': user_id}
                )
                for commit in project_commits:
                    # Get the branch information for this commit
                    branches = project.commits.get(commit.id).refs('branch')
                    branch = branches[0].name if branches else 'unknown'
                    
                    commits.append(CommitStats(
                        sha=commit.id,
                        title=commit.title,
                        message=commit.message,
                        authored_date=commit.authored_date,
                        project_id=project.id,
                        project_name=project.name,
                        branch=branch,
                        stats=commit.stats
                    ))
            except gitlab.exceptions.GitlabError:
                continue
        return commits