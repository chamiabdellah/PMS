"""
===============================================================================
 File Name   : combined_gitlab_jira.py
 Description : Extract GitLab commits and associated JIRA ticket data
 Author      : Combined from Chami Abdellah scripts
 Created     : 2025-09-16
 Last Updated: 2025-09-16
===============================================================================

 Change History:
 ------------------------------------------------------------------------------
 Date        Author             Description
 ----------  -----------------  ----------------------------------------------
 2025-09-16  Combined           Merged GitLab and JIRA extraction scripts

===============================================================================
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gitlab
import time
import re
from jira import JIRA
import pandas as pd
from datetime import datetime

# GitLab configuration
gl = gitlab.Gitlab("https://gitlab.com/", private_token="glpat-MycCz9jBsNjQx2tokcsx")
gl.auth()
print(f"GitLab user: {gl.user.username}")

# JIRA configuration
jiraOptions = {'server': "https://xlibxli.atlassian.net/"}
jira = JIRA(options=jiraOptions, basic_auth=("abdellah.chami_external@hse.com", "ATATT3xFfGF0rOO9y1y3Gl3XfM0dzlTjyocc9aUjkjAJnsceXnl7z_e-gjXv5htAqHEvQ_qxvKzs6uAZjbKZF7x1w0KYI2PpIx2WZuF0OvN5HZ5DSamwZ7tz6ziDoH2AkV1MVdQEytmJhR-Ud8GJvayesoukAM_yQdry-rL0M9BVuHRsQmlnULE=1846DEEB"))

# Global variables to store processed tickets and their data
processed_tickets = set()
jira_data_cache = {}  # Cache to store JIRA data by ticket key
all_combined_data = []

def extract_jira_ticket_from_title(title):
    """Extract JIRA ticket number from commit title using regex"""
    # Common JIRA ticket patterns: PROJECT-123, PROJ-456, etc.
    # Looks for uppercase letters followed by hyphen and numbers
    pattern = r'\b([A-Z]{2,}-\d+)\b'
    matches = re.findall(pattern, title)
    
    # Debug: Print what we're searching and what we found
    if matches:
        print(f"    Found JIRA ticket(s) in '{title[:50]}...': {matches}")
        return matches[0]  # Return first match
    else:
        print(f"    No JIRA ticket found in: '{title[:50]}...'")
        return None

def fetch_jira_data(ticket_key):
    """Fetch JIRA data for a specific ticket key"""
    # Check if we already have data for this ticket
    if ticket_key in jira_data_cache:
        print(f"    ↺ Using cached JIRA data for: {ticket_key}")
        return jira_data_cache[ticket_key]
    
    if ticket_key in processed_tickets:
        print(f"    ⚠️  JIRA ticket {ticket_key} was processed but data not cached")
        return None
    
    processed_tickets.add(ticket_key)
    
    try:
        print(f"    → Fetching JIRA data for: {ticket_key}")
        
        # Fields to be extracted
        fields = "key,assignee,issuetype,summary,status,created,customfield_10002,parent"
        
        # Get the specific issue by key
        singleIssue = jira.issue(ticket_key, fields=fields, expand="changelog")
        
        jira_data = {}
        jira_data["jira_assignee"] = str(singleIssue.fields.assignee) if singleIssue.fields.assignee else ""
        jira_data["jira_key"] = singleIssue.key
        jira_data["jira_type"] = str(singleIssue.fields.issuetype) if singleIssue.fields.issuetype else ""
        jira_data["jira_summary"] = singleIssue.fields.summary if singleIssue.fields.summary else ""
        jira_data["jira_status"] = str(singleIssue.fields.status) if singleIssue.fields.status else ""
        jira_data["jira_created_on"] = singleIssue.fields.created if singleIssue.fields.created else ""
        
        # Handle story points
        if hasattr(singleIssue.fields, 'customfield_10002') and singleIssue.fields.customfield_10002:
            jira_data["jira_story_points"] = singleIssue.fields.customfield_10002
        else:
            jira_data["jira_story_points"] = 0
        
        # Handle parent issue information
        if hasattr(singleIssue.fields, 'parent') and singleIssue.fields.parent:
            jira_data["jira_parent"] = singleIssue.fields.parent.key 
            try:
                parent_issue = jira.issue(jira_data["jira_parent"])
                jira_data["jira_parent_type"] = str(parent_issue.fields.issuetype) if parent_issue.fields.issuetype else ""
                if parent_issue and hasattr(parent_issue.fields, 'customfield_10002') and parent_issue.fields.customfield_10002:
                    jira_data["jira_parent_story_points"] = parent_issue.fields.customfield_10002
                else:
                    jira_data["jira_parent_story_points"] = 0
            except Exception as e:
                print(f"    ⚠️  Warning: Could not fetch parent issue details for {ticket_key}: {e}")
                jira_data["jira_parent_type"] = ""
                jira_data["jira_parent_story_points"] = 0
        else:
            jira_data["jira_parent"] = ""        
            jira_data["jira_parent_type"] = ""
            jira_data["jira_parent_story_points"] = 0
        
        # Cache the data for future use
        jira_data_cache[ticket_key] = jira_data
        
        print(f"    ✅ Successfully fetched and cached JIRA data for: {ticket_key}")
        return jira_data
        
    except Exception as e:
        print(f"    ❌ ERROR processing JIRA ticket {ticket_key}: {e}")
        # Cache error data so we don't keep retrying failed tickets
        error_data = {
            "jira_assignee": "",
            "jira_key": ticket_key,
            "jira_type": "",
            "jira_summary": "",
            "jira_status": f"Error: {str(e)}",
            "jira_created_on": "",
            "jira_story_points": 0,
            "jira_parent": "",
            "jira_parent_type": "",
            "jira_parent_story_points": 0
        }
        jira_data_cache[ticket_key] = error_data
        return error_data

def extract_commit_info(commit_obj, project):
    """Extract full commit info including changes"""
    try:
        # Get full commit details
        commit = project.commits.get(commit_obj.id)

        # Get stats (additions, deletions, total)
        stats = commit.stats

        # Get commit diff/changes
        commit_changes = []
        try:
            # Get the diff for this commit
            diffs = commit.diff()
            for diff in diffs:
                # Extract file changes
                file_path = diff.get('new_path', diff.get('old_path', 'unknown'))
                change_type = 'modified'
                
                if diff.get('new_file'):
                    change_type = 'added'
                elif diff.get('deleted_file'):
                    change_type = 'deleted'
                elif diff.get('renamed_file'):
                    change_type = 'renamed'
                
                # Get the actual diff content (limited to avoid huge strings)
                diff_content = diff.get('diff', '')[:500]  # Limit to first 500 chars
                
                change_info = f"{file_path} ({change_type}): {diff_content.replace(chr(10), ' ').replace(chr(13), ' ')}"
                commit_changes.append(change_info)
                
        except Exception as diff_error:
            commit_changes.append(f"Error extracting diff: {str(diff_error)}")

        # Combine all changes into a single string
        changes_combined = " | ".join(commit_changes) if commit_changes else "No changes detected"

        # Extract JIRA ticket from commit title
        jira_ticket = extract_jira_ticket_from_title(commit.title)
        
        # Base commit data
        commit_data = {
            'project_name': project.name,
            'commit_short_id': commit.short_id,
            'commit_author_name': commit.author_name,
            'commit_author_email': commit.author_email,
            'commit_date': commit.committed_date,
            'commit_title': commit.title.strip(),
            'commit_additions': stats['additions'],
            'commit_deletions': stats['deletions'],
            'commit_total_changes': stats['total'],
            'commit_changes': changes_combined,
            'extracted_jira_ticket': jira_ticket if jira_ticket else ""
        }

        # If JIRA ticket found, fetch JIRA data
        if jira_ticket:
            jira_data = fetch_jira_data(jira_ticket)
            if jira_data:
                commit_data.update(jira_data)
            else:
                # This shouldn't happen with the new caching logic, but just in case
                commit_data.update({
                    "jira_assignee": "",
                    "jira_key": jira_ticket,
                    "jira_type": "Data not available",
                    "jira_summary": "",
                    "jira_status": "",
                    "jira_created_on": "",
                    "jira_story_points": 0,
                    "jira_parent": "",
                    "jira_parent_type": "",
                    "jira_parent_story_points": 0
                })
        else:
            # Add empty JIRA fields if no ticket found
            commit_data.update({
                "jira_assignee": "",
                "jira_key": "",
                "jira_type": "",
                "jira_summary": "",
                "jira_status": "",
                "jira_created_on": "",
                "jira_story_points": 0,
                "jira_parent": "",
                "jira_parent_type": "",
                "jira_parent_story_points": 0
            })

        return commit_data

    except Exception as e:
        return {
            'project_name': project.name if 'project' in locals() else 'Unknown',
            'commit_short_id': commit_obj.id,
            'error': str(e),
            'commit_changes': 'Error extracting changes',
            'extracted_jira_ticket': "",
            # Add empty JIRA fields
            "jira_assignee": "",
            "jira_key": "",
            "jira_type": "",
            "jira_summary": "",
            "jira_status": "",
            "jira_created_on": "",
            "jira_story_points": 0,
            "jira_parent": "",
            "jira_parent_type": "",
            "jira_parent_story_points": 0
        }

def extract_commits_info(branch, project):
    """Extract commit information for a specific branch, filtered by year"""
    results = []
    try:
        commits = project.commits.list(ref_name=branch.name, per_page=100, page=1)
        print(f"Processing {len(commits)} commits from branch: {branch.name}")
    
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            for c in commits:
                # Filter commits by year 2024 and 2025 only
                commit_date = datetime.strptime(c.committed_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                if commit_date.year not in [2024, 2025]:
                    print(f"   ⏩ Skipping commit {c.short_id} from year {commit_date.year}")
                    continue

                futures.append(executor.submit(extract_commit_info, c, project))

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        return results
        
    except Exception as e:
        print(f"Error processing branch {branch.name}: {e}")
        return []


def write_combined_csv(all_data, filename='gitlab_jira_data.csv'):
    """Write all combined data to a single CSV file"""
    if not all_data:
        print("No data to write to CSV")
        return
    
    # Define all possible fieldnames
    fieldnames = [
        'project_name', 'commit_short_id', 'commit_author_name', 'commit_author_email', 
        'commit_date', 'commit_title', 'commit_additions', 'commit_deletions', 
        'commit_total_changes', 'commit_changes', 'extracted_jira_ticket',
        'jira_assignee', 'jira_key', 'jira_type', 'jira_summary', 'jira_status',
        'jira_created_on', 'jira_story_points', 'jira_parent', 'jira_parent_type',
        'jira_parent_story_points', 'error'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in all_data:
            # Ensure all fields exist in the row
            for field in fieldnames:
                if field not in row:
                    row[field] = ''
            writer.writerow(row)
    
    print(f"Combined CSV file saved as: {filename}")

def main():
    """Main function to process GitLab projects and extract commit/JIRA data"""
    global all_combined_data
    
    print("Starting combined GitLab-JIRA extraction...")
    start_time = time.time()

    # GitLab group configuration
    subgroup_path = 'hse24/ecom/team-scom'
    group = gl.groups.get(subgroup_path)

    # Get all projects inside that subgroup
    projects = group.projects.list(all=True)
    print(f"Found {len(projects)} projects in group: {subgroup_path}")
    for p in projects:
        try:
            project = gl.projects.get(p.id)
            print(f"\n--- Processing project: {project.name} ---")
            
            branches = project.branches.list(get_all=True)
            if not branches:
                print("   ⚠️ No branches found.")
            else:
                print(f"   Found {len(branches)} branches")
                for branch in branches:
                    print(f"   Processing branch: {branch.name}")
                    branch_results = extract_commits_info(branch, project)
                    all_combined_data.extend(branch_results)
                    
        except Exception as e:
            print(f"Error processing project {p.name if hasattr(p, 'name') else 'Unknown'}: {e}")
    # Write all combined data to CSV
    write_combined_csv(all_combined_data)

    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print(f"\n--- Summary ---")
    print(f"Total commits processed: {len(all_combined_data)}")
    print(f"Unique JIRA tickets found: {len(jira_data_cache)}")
    print(f"JIRA tickets processed: {len(processed_tickets)}")
    
    # Show which tickets were found
    if jira_data_cache:
        print(f"JIRA tickets found: {list(jira_data_cache.keys())}")
    
    # Count commits with JIRA tickets vs without
    commits_with_jira = sum(1 for commit in all_combined_data if commit.get('extracted_jira_ticket'))
    commits_without_jira = len(all_combined_data) - commits_with_jira
    
    print(f"Commits with JIRA tickets: {commits_with_jira}")
    print(f"Commits without JIRA tickets: {commits_without_jira}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")

if __name__ == '__main__':
    main()