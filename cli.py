#!/usr/bin/env python3
import argparse
import os
from gitlab_stats import GitLabStats

def main():
    parser = argparse.ArgumentParser(description='GitLab Developer Statistics')
    parser.add_argument('--token', help='GitLab personal access token')
    parser.add_argument('--url', default='https://gitlab.com', help='GitLab instance URL')
    parser.add_argument('--username', help='Username to analyze (optional)')
    
    args = parser.parse_args()
    
    # Get token from argument or environment
    token = args.token or os.getenv('GITLAB_TOKEN')
    if not token:
        print("Error: Please provide token via --token argument or GITLAB_TOKEN environment variable")
        return
    
    stats = GitLabStats(token, args.url)
    
    try:
        user = stats.get_user_info()
        print(f"Analyzing stats for: {user['name']} ({user['username']})")
        
        summary = stats.get_contribution_summary()
        
        print(f"\nTotal Commits: {summary['total_commits']}")
        print(f"Projects Contributed To: {summary['projects_contributed_to']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()