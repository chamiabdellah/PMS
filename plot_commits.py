"""
===============================================================================
 File Name   : plot_commits.py
 Description : dispalay Gitlab  commits for specific assignee given in main
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

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.interpolate import make_interp_spline
import pandas as pd

def plot_author_commits(df, author_name, ax):
    ax.clear()
    sns.set_theme(style="white")

    # Ensure commit_day is datetime
    df['commit_day'] = pd.to_datetime(df['commit_day'], errors='coerce')

    # Filter for selected author
    filtered = df[df['author_canonical'] == author_name]

    if filtered.empty:
        ax.text(0.5, 0.5, f"No data for {author_name}", ha='center', va='center', fontsize=12)
        ax.set_title(f"Commits per Day: {author_name}", fontsize=14, weight='bold')
        ax.axis('off')
        return

    # Group and limit to max 10 most recent days
    daily_counts = (
        filtered.groupby('commit_day')
        .size()
        .sort_index(ascending=False)       # Get latest dates first
        .head(20)                          # Max 10 entries
        .sort_index()                      # Re-sort for chronological order
    )

    avg_commits = daily_counts.mean()

    x = np.arange(len(daily_counts))
    y = daily_counts.values

    if len(x) >= 4:
        x_smooth = np.linspace(x.min(), x.max(), 300)
        spline = make_interp_spline(x, y, k=3)
        y_smooth = spline(x_smooth)
    else:
        x_smooth, y_smooth = x, y

    ax.fill_between(x_smooth, y_smooth, alpha=0.25, color="#A6C1F8")
    ax.plot(x_smooth, y_smooth, color="#719DF6", linewidth=2.5)
    ax.scatter(x, y, edgecolor="#79A4FB", s=80, zorder=5)

    ax.axhline(avg_commits, color='orange', linestyle='--', linewidth=1.5,
               label=f'Avg: {avg_commits:.2f}')

    ax.set_title(f'Average Commits per Day', fontsize=14, weight='bold')
    #ax.set_title(f'Commits per Day for : {author_name}', fontsize=14, weight='bold')

    ax.set_ylabel('Commits')
    ax.set_xticks(x)
    ax.set_xticklabels(daily_counts.index.strftime('%Y-%m-%d'), rotation=45, ha='right', fontsize=9)
    ax.set_xlabel("Date")

    ax.grid(False)
    ax.set_facecolor("white")
    ax.legend()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
