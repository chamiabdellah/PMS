"""
Data models for GitLab statistics.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class CommitStats:
    """Statistics for a single commit."""
    sha: str
    title: str
    message: str
    authored_date: str
    project_id: int
    project_name: str
    branch: str
    stats: Dict[str, int]  # Contains additions, deletions, total

    @property
    def size(self) -> int:
        """Total size of the commit (additions + deletions)."""
        return self.stats.get('total', 0)

@dataclass
class UserStats:
    """Comprehensive statistics for a GitLab user."""
    username: str
    total_commits: int
    commits: List[CommitStats]
    created_at: str
    last_activity_at: str

    def get_commit_dates(self) -> List[str]:
        """Get list of all commit dates."""
        return [commit.authored_date for commit in self.commits]

    def get_total_changes(self) -> Dict[str, int]:
        """Get total number of additions, deletions, and changes."""
        additions = sum(commit.stats.get('additions', 0) for commit in self.commits)
        deletions = sum(commit.stats.get('deletions', 0) for commit in self.commits)
        return {
            'additions': additions,
            'deletions': deletions,
            'total': additions + deletions
        }
        
    def get_branch_count(self) -> int:
        """Get the number of unique branches the user has committed to."""
        unique_branches = {commit.branch for commit in self.commits}
        return len(unique_branches)