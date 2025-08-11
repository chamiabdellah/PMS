"""
Utility functions for GitLab statistics.
"""
from typing import Dict, List
from datetime import datetime
import json
from .models import UserStats

def format_datetime(date_str: str) -> str:
    """Format datetime string to a more readable format."""
    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def export_stats_to_json(stats: UserStats, filepath: str) -> None:
    """
    Export user statistics to a JSON file.
    
    Args:
        stats: UserStats object
        filepath: Path to output JSON file
    """
    data = {
        'username': stats.username,
        'total_commits': stats.total_commits,
        'account_created_at': format_datetime(stats.created_at),
        'last_activity_at': format_datetime(stats.last_activity_at),
        'total_changes': stats.get_total_changes(),
        'commits': [
            {
                'sha': commit.sha,
                'title': commit.title,
                'date': format_datetime(commit.authored_date),
                'project': commit.project_name,
                'stats': commit.stats
            }
            for commit in stats.commits
        ]
    }
    
    # amazonq-ignore-next-line
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)