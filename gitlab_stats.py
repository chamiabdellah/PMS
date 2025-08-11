#!/usr/bin/env python3
import requests
from datetime import datetime
from typing import Dict, List, Optional
import os

class GitLabStats:
    """Class to extract and analyze GitLab developer account statistics."""
    
    def __init__(self, private_token: str, gitlab_url: str = "https://gitlab.com"):
        """
        Initialize GitLab statistics collector.
        
        Args:
            private_token (str): GitLab personal access token
            gitlab_url (str): Base URL of GitLab instance (default: https://gitlab.com)
        """
        self.gitlab_url = gitlab_url.rstrip('/')
        self.headers = {'PRIVATE-TOKEN': private_token}
        
    def get_user_info(self) -> Dict:
        """Get current user information."""
        try:
            response = requests.get(
                f"{self.gitlab_url}/api/v4/user",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching user info: {str(e)}")
    
    def get_user_commits(self, since: Optional[str] = None, until: Optional[str] = None) -> List[Dict]:
        """
        Get all commits made by the current user.
        
        Args:
            since (str, optional): ISO 8601 formatted date to fetch commits from
            until (str, optional): ISO 8601 formatted date to fetch commits until
        
        Returns:
            List[Dict]: List of commit details
        """
        params = {
            'author': True,  # Only get commits authored by the current user
            'all': True,     # Get commits from all branches
        }
        if since:
            params['since'] = since
        if until:
            params['until'] = until
            
        commits = []
        page = 1
        
        while True:
            params['page'] = page
            response = requests.get(
                f"{self.gitlab_url}/api/v4/events",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            if not data:
                break
                
            commits.extend([
                event for event in data 
                if event['action_name'] == 'pushed to'
            ])
            page += 1
            
        return commits
    
    def get_commit_stats(self, project_id: int, commit_sha: str) -> Dict:
        """
        Get detailed statistics for a specific commit.
        
        Args:
            project_id (int): ID of the project
            commit_sha (str): SHA of the commit
            
        Returns:
            Dict: Commit statistics including additions, deletions, etc.
        """
        response = requests.get(
            f"{self.gitlab_url}/api/v4/projects/{project_id}/repository/commits/{commit_sha}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_contribution_summary(self, since: Optional[str] = None) -> Dict:
        """
        Get a summary of user's contributions.
        
        Args:
            since (str, optional): ISO 8601 formatted date to start counting from
            
        Returns:
            Dict: Summary of contributions including:
                - total_commits
                - total_additions
                - total_deletions
                - projects_contributed_to
                - commit_dates
        """
        commits = self.get_user_commits(since=since)
        
        summary = {
            'total_commits': len(commits),
            'total_additions': 0,
            'total_deletions': 0,
            'projects_contributed_to': set(),
            'commit_dates': []
        }
        
        for commit in commits:
            project_id = commit.get('project_id')
            if project_id:
                summary['projects_contributed_to'].add(project_id)
                
            if 'created_at' in commit:
                summary['commit_dates'].append(commit['created_at'])
                
            # Get detailed commit stats if project_id is available
            if project_id and 'push_data' in commit and 'commit_id' in commit['push_data']:
                try:
                    stats = self.get_commit_stats(project_id, commit['push_data']['commit_id'])
                    summary['total_additions'] += stats.get('stats', {}).get('additions', 0)
                    summary['total_deletions'] += stats.get('stats', {}).get('deletions', 0)
                except requests.exceptions.RequestException:
                    continue
        
        # Convert set to length for JSON serialization
        summary['projects_contributed_to'] = len(summary['projects_contributed_to'])
        
        return summary

def main():
    """Example usage of the GitLabStats class."""
    # Get token from environment variable for security
    token = os.getenv('GITLAB_TOKEN')
    if not token:
        print("Please set the GITLAB_TOKEN environment variable")
        return
    
    # Initialize GitLab stats
    stats = GitLabStats(token)
    
    try:
        # Get user info
        user = stats.get_user_info()
        print(f"Analyzing stats for user: {user['name']} ({user['username']})")
        
        # Get contribution summary for the last year
        last_year = datetime.now().replace(year=datetime.now().year - 1).isoformat()
        summary = stats.get_contribution_summary(since=last_year)
        
        # Print results
        print("\nContribution Summary (Last Year):")
        print(f"Total Commits: {summary['total_commits']}")
        print(f"Total Additions: {summary['total_additions']}")
        print(f"Total Deletions: {summary['total_deletions']}")
        print(f"Projects Contributed To: {summary['projects_contributed_to']}")
        # amazonq-ignore-next-line
        print(f"Branches worked on: {stats.get_branch_count()}")
        print(f"First Commit Date: {min(summary['commit_dates'], default='No commits')}")
        print(f"Last Commit Date: {max(summary['commit_dates'], default='No commits')}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing GitLab API: {e}")

if __name__ == "__main__":
    main()