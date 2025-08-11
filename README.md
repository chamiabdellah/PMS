# GitLab Developer Statistics

This Python script allows you to extract and analyze various statistics from a GitLab developer account, including:
- Number of commits
- Dates of commits
- Size of commits (additions/deletions)
- Projects contributed to
- And more!

## Requirements

- Python 3.6+
- GitLab Personal Access Token
- `requests` library

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Set your GitLab personal access token as an environment variable:
```bash
export GITLAB_TOKEN='your-token-here'
```

2. Run the script:
```bash
python gitlab_stats.py
```

The script will output a summary of your GitLab activity, including:
- Total number of commits
- Total lines added/deleted
- Number of projects contributed to
- First and last commit dates

## Using as a Library

You can also use the `GitLabStats` class in your own code:

```python
from gitlab_stats import GitLabStats

# Initialize with your token
stats = GitLabStats('your-token-here')

# Get user information
user_info = stats.get_user_info()

# Get contribution summary for the last year
summary = stats.get_contribution_summary(since='2023-01-01T00:00:00Z')

# Get specific commit details
commit_stats = stats.get_commit_stats(project_id=123, commit_sha='abc123')
```

## Running Tests

To run the unit tests:
```bash
python -m unittest test_gitlab_stats.py
```

## Features

- Get user information
- Fetch commit history with date filtering
- Calculate contribution statistics
- Get detailed commit information
- Support for self-hosted GitLab instances
- Pagination handling for large result sets

## Security Note

Always keep your GitLab token secure and never commit it to version control. Use environment variables or secure secret management systems to handle the token.