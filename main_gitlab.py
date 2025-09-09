"""
===============================================================================
 File Name   : main_gitlab.py
 Description : extract gitlab commits information for specific group
 Author      : Chami Abdellah (abdellah.chami_external@hse.com)
 Created     : 2025-09-09
 Last Updated: 2025-09-09
===============================================================================

 Change History:
 ------------------------------------------------------------------------------
 Date        Author             Description
 ----------  -----------------  ----------------------------------------------
 2025-09-09  Chami Abdellah          Initial version
===============================================================================
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gitlab
import time

gl = gitlab.Gitlab("https://gitlab.com/",private_token="")

gl.auth()  # optional but confirms auth works

print(gl.user.username)





'''
get all the projects from a specific group
'''
def get_all_group_projects(group_path):
    """Recursively get all projects in a group and its subgroups."""
    all_projects = []
    group = gl.groups.get(group_path)
    
    # Add projects from this group
    all_projects.extend(group.projects.list(all=True))

    # Recurse into subgroups
    subgroups = group.subgroups.list(all=True)
    for subgroup in subgroups:
        sub_projects = get_all_group_projects(subgroup.full_path)
        all_projects.extend(sub_projects)

    return all_projects







# Function to extract full commit info
def extract_commit_info(commit_obj):
    try:
        # Get full commit details
        commit = project.commits.get(commit_obj.id)

        # # Get stats (additions, deletions, total)
        stats = commit.stats

        # Get commit comments
        comment_texts = []
        comments = commit.comments.list(all=True)

        # for note in comments:
        #     # Some attributes may be missing, so use .get() on the dict level
        #     text = getattr(note, 'note', '').strip().replace('\n', ' ')
        #     if text:
        #         comment_texts.append(text)

        # comments_combined = " | ".join(comment_texts) if comment_texts else ""

        return {
            'short_id': commit.short_id,
            'author_name': commit.author_name,
            'author_email': commit.author_email,
            'committed_date': commit.committed_date,
            'title': commit.title.strip(),
            'additions': stats['additions'],
            'deletions': stats['deletions'],
            'total_changes': stats['total']
            # 'comments': comments_combined
        }

    except Exception as e:
        return {
            'short_id': commit_obj.id,
            'error': str(e)
        }

'''
count number of commits
'''
def count_commits(branch):
    try:
        commits = project.commits.list(ref_name=branch.name,per_page=100,page=1)
        return branch.name, len(commits)
    except Exception as e:
        return branch.name, f"Error: {e}"

'''
count number of commits
'''
def extract_commitScount():
    results = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_branch = {executor.submit(count_commits, branch): branch for branch in branches}
        for future in as_completed(future_to_branch):
            branch_name, commit_count = future.result()
            results.append((branch_name, commit_count))

    # Print results
    for branch_name, commit_count in sorted(results):
        print(f"Branch: {branch_name} → {commit_count} commits")


'''
create csv file to save the output
'''
def write_header():
    fieldnames = [
            'short_id', 'author_name', 'author_email', 'committed_date', 'title',
            'additions', 'deletions', 'total_changes', 'comments', 'error'
        ]

    with open('commit_details.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

'''
function that extracts the information regarding the commits for each branch
'''
def extract_commitsInfo(branch):
    results = []
    try:
        commits = project.commits.list(ref_name=branch.name,per_page=100,page=1)
    
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(extract_commit_info, c) for c in commits]
            for future in as_completed(futures):
                results.append(future.result())

        # Save to CSV
        fieldnames = [
            'short_id', 'author_name', 'author_email', 'committed_date', 'title',
            'additions', 'deletions', 'total_changes', 'comments', 'error'
        ]

        with open('commit_details.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            #writer.writeheader()
            for row in results:
                for key in fieldnames:
                    if key not in row:
                        row[key] = ''
                writer.writerow(row)
    except Exception as e:
        return branch.name, f"Error: {e}"






if __name__ == '__main__':

    print(" start processing ....")
    write_header()
    start_time2 = time.time()
    #group = gl.groups.get('hse24')  # Or whatever the actual path is

    # # Get all projects in the group

    subgroup_path = 'hse24/ecom/team-scom'
    group = gl.groups.get(subgroup_path)

    # Step 2: Get all projects inside that subgroup
    projects = group.projects.list(all=True)
    for p in projects:
        project = gl.projects.get(p.id)
        print(project.name)
        branches = project.branches.list(get_all=True)
        if not branches:
            print("   ⚠️ No branches found.")
        else:
            for branch in branches:
                extract_commitsInfo(branch)
        # for bra in branches:
        #     extract_commitsInfo(bra)



    end_time2 = time.time()

    elapsed_time2 = end_time2 - start_time2  # Calculate elapsed time

    print(f"Elapsed time parallel: {elapsed_time2:.2f} seconds")