"""
===============================================================================
 File Name   : plot_jira.py
 Description : dispalay jira data for specific assignee given in main
 Author      : Chami Abdellah (abdellah.chami_external@hse.com)
 Created     : 2025-09-10
 Last Updated: 2025-09-10
===============================================================================

 Change History:
 ------------------------------------------------------------------------------
 Date        Author             Description
 ----------  -----------------  ----------------------------------------------
 2025-09-10  Chami Abdellah          Initial version

===============================================================================
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re


def parse_duration_to_hours(duration_str):
    if pd.isna(duration_str):
        return None

    match = re.search(r"(?:(\d+)\s*days?)?,?\s*(?:(\d+)\s*hours?)?", str(duration_str))
    if not match:
        return None

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0

    return days * 24 + hours


def plot_jira_timings(jira_df, assignee_name, ax):
    ax.clear()
    sns.set_theme(style="white")

    df = jira_df.copy()
    df.columns = df.columns.str.strip()

    # Standardize assignee names
    df['Assignee_clean'] = df['Assignee'].str.lower().str.replace(r'[^a-z]', '', regex=True)
    assignee_clean = assignee_name.lower().replace(" ", "").replace(".", "")
    df = df[df['Assignee_clean'] == assignee_clean]

    if df.empty:
        ax.text(0.5, 0.5, "No data for selected user", ha='center', va='center', fontsize=12)
        ax.set_title(f"No Jira Data for {assignee_name}", fontsize=14, weight='bold')
        ax.axis('off')
        return

    # Merge Story Points
    df['StoryPoints'] = df['Story points']
    df['StoryPoints'].fillna(df['Parent Story points'], inplace=True)
    df['StoryPoints'] = pd.to_numeric(df['StoryPoints'], errors='coerce')
    df = df.dropna(subset=['StoryPoints'])
    df = df[df['StoryPoints'] > 0]

    # Convert durations to hours
    df['In Progress Time (h)'] = df['In Progress Time'].apply(parse_duration_to_hours)
    df['Code Review Time (h)'] = df['Code Review Time'].apply(parse_duration_to_hours)
    df.dropna(subset=['In Progress Time (h)', 'Code Review Time (h)'], inplace=True)

    if df.empty:
        ax.text(0.5, 0.5, "No time data for selected user", ha='center', va='center', fontsize=12)
        ax.set_title(f"No Jira Time Data for {assignee_name}", fontsize=14, weight='bold')
        ax.axis('off')
        return

    # Aggregate per story point
    grouped = df.groupby('StoryPoints').agg({
        'In Progress Time (h)': 'mean',
        'Code Review Time (h)': 'mean'
    }).reset_index()

    # Plot grouped bar chart
    x = np.arange(len(grouped))  # label locations
    width = 0.35

    ax.bar(x - width/2, grouped['In Progress Time (h)'], width=width,
           color="#00BFFF", label='In Progress')
    ax.bar(x + width/2, grouped['Code Review Time (h)'], width=width,
           color="#FFA500", label='Code Review')

    ax.set_xticks(x)
    ax.set_xticklabels(grouped['StoryPoints'].astype(int), fontsize=10)
    ax.set_xlabel('Story Points', fontsize=12)
    ax.set_ylabel('Avg Time (hours)', fontsize=12)
    # ax.set_title(f'Avg In-Progress & Code Review Time\n(Jira: {assignee_name})',
    #              fontsize=14, weight='bold', pad=15)
    ax.set_title(f'Avg In-Progress & Code Review Time', fontsize=14, weight='bold', pad=15)
    ax.legend(title='Phase')
    ax.set_facecolor("white")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(False)

    plt.tight_layout()
