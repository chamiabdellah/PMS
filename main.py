"""
Main script to extract GitLab user statistics.
"""
import argparse
import sys
from gitlab_stats.api import GitLabAPI
from gitlab_stats.utils import export_stats_to_json

def main():
    parser = argparse.ArgumentParser(description='Extract GitLab user statistics')
    parser.add_argument('--url', required=True, help='GitLab instance URL')
    parser.add_argument('--token', required=True, help='GitLab private token')
    parser.add_argument('--username', required=True, help='GitLab username to analyze')
    parser.add_argument('--output', default='gitlab_stats.json',
                      help='Output JSON file path (default: gitlab_stats.json)')

    args = parser.parse_args()

    try:
        # Initialize GitLab API client
        api = GitLabAPI(args.url, args.token)
        
        # Get user statistics
        stats = api.get_user_stats(args.username)
        
        # Export statistics to JSON
        export_stats_to_json(stats, args.output)
        
        print(f"Statistics for user {args.username} have been exported to {args.output}")
        print(f"Total commits: {stats.total_commits}")
        print(f"Total chaneeges: {stats.get_total_changes()['total']} lines")
        print(f"Total branches worked on: {stats.get_branch_count()}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()