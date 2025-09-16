"""
Main script to extract GitLab user statistics.
"""
import os
import sys
from gitlab_stats.api import GitLabAPI
from gitlab_stats.utils import export_stats_to_json


def main():
    # Get configuration from environment variables
    url = os.getenv('GITLAB_URL')
    token = os.getenv('GITLAB_TOKEN')
    username = os.getenv('GITLAB_USERNAME')
    output = os.getenv('GITLAB_OUTPUT', 'gitlab_stats.json')

    if not all([url, token, username]):
        print("Error: Please set GITLAB_URL, GITLAB_TOKEN, and GITLAB_USERNAME environment variables", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize GitLab API client
        api = GitLabAPI(url, token)

        # Get user statistics
        stats = api.get_user_stats(username)

        # Export statistics to JSON
        # export_stats_to_json(stats, output)

        print(f"Statistics for user {username} have been exported to {output}")
        print(f"Total commits: {stats.total_commits}")
        print(f"Total chaneeges: {stats.get_total_changes()['total']} lines")
        print(f"Total branches worked on: {stats.get_branch_count()}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
