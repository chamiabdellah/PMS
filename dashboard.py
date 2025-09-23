import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="PMS Dashboard - GitLab & Jira Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Name mapping dictionary - GitLab names (keys) to Jira names (values)
name_combination = {
    'Abdellah CHAMI': 'Chami, Abdellah, HSE DE (External)',
    'AbdellahChami': 'Chami, Abdellah, HSE DE (External)',
    'Badreddine Bendriss': 'Bendriss, Badreddine, HSE DE (External)',
    'younes elmorabit': 'Elmorabit, Younes, HSE DE (External)',
    'ibrahim Ahdadou': 'Ahdadou, Ibrahim, HSE DE (External)',
    'Zakaria Zanati': 'Zanati, Zakaria, HSE DE (External)',
    'tawfiq khnicha': 'Khnicha, Tawfiq, HSE DE (External)',
    'Alok Sharma': 'Sharma, Alok, HSE DE',
    'Anas Boulmane': 'Anas, Boulmane, HSE DE (External)',
    'Ilia Balashov': 'Balashov, Ilia, HSE DE',
    'Abdellah Chami': 'Chami, Abdellah, HSE DE (External)',
    'Abdellah': 'Chami, Abdellah, HSE DE (External)'
}

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 7px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .sidebar-info {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .sidebar-info-unified {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .sidebar-info-features {
        background: #2c2c2c;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #444;
    }
    .feature-link {
        color: white;
        text-decoration: none;
        cursor: pointer;
        padding: 0.2rem 0;
        display: block;
        transition: all 0.3s ease;
    }
    .feature-link:hover {
        color: #ffeb3b;
        text-decoration: underline;
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

def normalize_name(name):
    """Normalize GitLab names to Jira names using the mapping dictionary"""
    if pd.isna(name) or name == '':
        return ''
    
    # Check if the name exists in the mapping dictionary
    if name in name_combination:
        return name_combination[name]
    
    # If not found in mapping, return the original name (could be already a Jira name)
    return name

@st.cache_data
def load_data(file_path):
    """Load and preprocess the CSV data with name normalization"""
    try:
        df = pd.read_csv(file_path)
        
        # Clean column names (remove extra spaces)
        df.columns = df.columns.str.strip()
        
        # Clean data
        df = df.fillna('')
        df = df.replace('Data not available', '')
        
        # Normalize GitLab author names to Jira format
        if 'commit_author_name' in df.columns:
            df['commit_author_name_normalized'] = df['commit_author_name'].apply(normalize_name)
        
        # Keep original Jira assignee names
        if 'jira_assignee' in df.columns:
            df['jira_assignee_normalized'] = df['jira_assignee']
        
        # Convert date columns
        if 'jira_created_on' in df.columns:
            df['jira_created_on'] = pd.to_datetime(df['jira_created_on'], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = ['jira_story_points', 'jira_parent_story_points']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def calculate_user_metrics(df, selected_user=None):
    """Calculate comprehensive metrics for users using normalized names"""
    # Use normalized names for calculations
    if selected_user and selected_user != "All Users":
        user_commits = df[(df['commit_author_name_normalized'] == selected_user) & (df['commit_short_id'] != '')]
        user_jira = df[(df['jira_assignee_normalized'] == selected_user) & (df['jira_key'] != '')]
    else:
        user_commits = df[df['commit_short_id'] != '']
        user_jira = df[df['jira_key'] != '']
    
    # Get all unique users (using normalized names)
    commit_users = set(df[df['commit_author_name_normalized'] != '']['commit_author_name_normalized'].unique())
    jira_users = set(df[df['jira_assignee_normalized'] != '']['jira_assignee_normalized'].unique())
    all_users = list(commit_users.union(jira_users))
    
    user_metrics = {}
    
    for user in all_users:
        if user == '':  # Skip empty names
            continue
            
        user_commits_data = df[(df['commit_author_name_normalized'] == user) & (df['commit_short_id'] != '')]
        user_jira_data = df[(df['jira_assignee_normalized'] == user) & (df['jira_key'] != '')]
        
        # Calculate story points
        total_story_points = (
            user_jira_data['jira_parent_story_points'].sum() + 
            user_jira_data['jira_story_points'].sum()
        )
        
        # Calculate commits per story point
        total_commits = len(user_commits_data)
        commits_per_story_point = total_commits / max(total_story_points, 1)
        
        # Calculate weekly commits
        if not user_jira_data.empty and 'jira_created_on' in user_jira_data.columns:
            date_range = user_jira_data['jira_created_on'].dropna()
            if not date_range.empty:
                weeks = max(1, (date_range.max() - date_range.min()).days / 7)
                commits_per_week = total_commits / weeks
            else:
                commits_per_week = total_commits
        else:
            commits_per_week = total_commits
        
        # Calculate completion rate
        completed_tickets = len(user_jira_data[user_jira_data['jira_status'] == 'Done'])
        total_tickets = len(user_jira_data)
        completion_rate = (completed_tickets / max(total_tickets, 1)) * 100
        
        # Calculate average time per story point (estimated)
        avg_time_per_story_point = completed_tickets * 2.5 / max(total_story_points, 1)  # Mock calculation
        
        # Projects
        projects = list(user_commits_data['project_name'].unique())
        
        user_metrics[user] = {
            'total_commits': total_commits,
            'total_story_points': total_story_points,
            'commits_per_story_point': round(commits_per_story_point, 2),
            'commits_per_week': round(commits_per_week, 2),
            'avg_time_per_story_point': round(avg_time_per_story_point, 2),
            'completed_tickets': completed_tickets,
            'total_tickets': total_tickets,
            'completion_rate': round(completion_rate, 1),
            'projects': projects
        }
    
    return user_metrics, all_users

def create_performance_chart(user_metrics):
    """Create user performance comparison chart"""
    users = list(user_metrics.keys())[:10]  # Top 10 users
    commits = [user_metrics[user]['total_commits'] for user in users]
    story_points = [user_metrics[user]['total_story_points'] for user in users]
    
    fig = make_subplots(
        rows=1, cols=1,
        subplot_titles=['User Performance Overview']
    )
    
    fig.add_trace(
        go.Bar(name='Total Commits', x=users, y=commits, marker_color='#8884d8'),
    )
    
    fig.add_trace(
        go.Bar(name='Story Points', x=users, y=story_points, marker_color='#82ca9d'),
    )
    
    fig.update_layout(
        barmode='group',
        height=400,
        title_text="User Performance Comparison",
        xaxis_tickangle=-45
    )
    
    return fig

def create_project_distribution(df, selected_user=None):
    """Create project distribution pie chart using normalized names"""
    if selected_user and selected_user != "All Users":
        filtered_df = df[
            (df['commit_author_name_normalized'] == selected_user) | 
            (df['jira_assignee_normalized'] == selected_user)
        ]
    else:
        filtered_df = df
    
    project_counts = filtered_df['project_name'].value_counts()
    
    fig = px.pie(
        values=project_counts.values,
        names=project_counts.index,
        title="Project Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(height=400)
    return fig

def create_ticket_types_chart(df, selected_user=None):
    """Create Jira ticket types distribution using normalized names"""
    if selected_user and selected_user != "All Users":
        filtered_df = df[df['jira_assignee_normalized'] == selected_user]
    else:
        filtered_df = df
    
    ticket_types = filtered_df[filtered_df['jira_type'] != '']['jira_type'].value_counts()
    
    if not ticket_types.empty:
        fig = px.pie(
            values=ticket_types.values,
            names=ticket_types.index,
            title="Jira Ticket Types Distribution",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_layout(height=400)
        return fig
    else:
        return go.Figure().add_annotation(text="No ticket type data available", 
                                        xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)

def create_commits_vs_story_points(user_metrics):
    """Create scatter plot of commits vs story points"""
    users = list(user_metrics.keys())
    commits = [user_metrics[user]['total_commits'] for user in users]
    story_points = [user_metrics[user]['total_story_points'] for user in users]
    
    fig = px.scatter(
        x=story_points,
        y=commits,
        hover_name=users,
        labels={'x': 'Story Points', 'y': 'Total Commits'},
        title="Commits vs Story Points Relationship",
        color=commits,
        size=story_points,
        color_continuous_scale='viridis'
    )
    
    fig.update_layout(height=400)
    return fig

def create_name_mapping_overview():
    """Create a visual overview of the name mappings"""
    gitlab_names = list(name_combination.keys())
    jira_names = list(name_combination.values())
    
    mapping_df = pd.DataFrame({
        'GitLab Name': gitlab_names,
        'Jira Name': jira_names
    })
    
    return mapping_df

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h2>🚀 Performance Management Dashboard</h2>
        <p>GitLab & Jira Analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    try:
        df = load_data('combined_gitlab_jira_data.csv')
        
        if df.empty:
            st.error("❌ Could not load data. Please ensure 'combined_gitlab_jira_data.csv' is in the same directory as this script.")
            st.info("Expected columns: project_name, commit_short_id, commit_author_name, jira_assignee, jira_key, jira_type, jira_summary, jira_status, jira_created_on, jira_story_points, jira_parent_story_points")
            return
        
        st.success(f"✅ Successfully loaded {len(df)} records from combined_gitlab_jira_data.csv")
        
        # Show name mapping info
        with st.expander("👥 View Name Mapping (GitLab ↔ Jira)", expanded=False):
            st.info("GitLab author names are automatically mapped to their corresponding Jira assignee names for unified analytics.")
            mapping_df = create_name_mapping_overview()
            st.dataframe(mapping_df, use_container_width=True)
        
    except FileNotFoundError:
        st.error("❌ File 'combined_gitlab_jira_data.csv' not found. Please make sure the file is in the same directory as this script.")
        return
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return
    
    # Sidebar
    st.sidebar.header("🔧 Dashboard Controls")
    
    # Calculate metrics using normalized names
    user_metrics, all_users = calculate_user_metrics(df)
    
    # Filter out empty names and sort
    all_users = [user for user in all_users if user and user.strip()]
    all_users = sorted(all_users)
    
    # User selection
    selected_user = st.sidebar.selectbox(
        "👤 Select User (Jira Names):",
        ["All Users"] + all_users,
        index=0
    )
    
    # Show mapping info in sidebar
    # st.sidebar.markdown("""
    # <div class="sidebar-info-unified">
    #     <h4>🔄 Name Unification</h4>
    #     <p>GitLab names are automatically mapped to Jira names for unified analytics.</p>
    # </div>
    # """, unsafe_allow_html=True)
    
    # Sidebar info with clickable features
    st.sidebar.markdown("""
    <div class="sidebar-info-features">
        <h4>📊 Dashboard Features</h4>
        <a href="#user-performance-overview" class="feature-link">• User Performance Analytics</a>
        <a href="#project-distribution" class="feature-link">• Project Distribution</a>
        <a href="#commits-vs-story-points" class="feature-link">• Commits vs Story Points</a>
        <a href="#jira-ticket-types" class="feature-link">• Jira Ticket Types</a>
        <a href="#gitlab-analytics" class="feature-link">• GitLab Analytics</a>
        <a href="#jira-analytics" class="feature-link">• Jira Analytics</a>
        <a href="#data-overview" class="feature-link">• Data Overview Table</a>
    </div>
    """, unsafe_allow_html=True)
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    # Key metrics
    if selected_user == "All Users":
        total_commits = len(df[df['commit_short_id'] != ''])
        total_story_points = df['jira_parent_story_points'].sum() + df['jira_story_points'].sum()
        total_tickets = len(df[df['jira_key'] != ''])
        completed_tickets = len(df[df['jira_status'] == 'Done'])
        
        with col1:
            st.metric("📝 Total Commits", f"{total_commits:,}")
        with col2:
            st.metric("🎯 Story Points", f"{int(total_story_points):,}")
        with col3:
            st.metric("🎫 Total Tickets", f"{total_tickets:,}")
        with col4:
            completion_rate = (completed_tickets / max(total_tickets, 1)) * 100
            st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
    
    else:
        user_data = user_metrics.get(selected_user, {})
        with col1:
            st.metric("📝 Total Commits", f"{user_data.get('total_commits', 0):,}")
        with col2:
            st.metric("🎯 Story Points", f"{int(user_data.get('total_story_points', 0)):,}")
        with col3:
            st.metric("⚡ Commits/Story Point", f"{user_data.get('commits_per_story_point', 0)}")
        with col4:
            st.metric("📅 Commits/Week", f"{user_data.get('commits_per_week', 0)}")
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div id="user-performance-overview"></div>', unsafe_allow_html=True)
        st.subheader("👥 User Performance Overview")
        if user_metrics:
            fig_performance = create_performance_chart(user_metrics)
            st.plotly_chart(fig_performance, use_container_width=True)
        else:
            st.info("No user performance data available")
    
    with col2:
        st.markdown('<div id="project-distribution"></div>', unsafe_allow_html=True)
        st.subheader("📊 Project Distribution")
        fig_projects = create_project_distribution(df, selected_user)
        st.plotly_chart(fig_projects, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown('<div id="commits-vs-story-points"></div>', unsafe_allow_html=True)
        st.subheader("🔄 Commits vs Story Points")
        if user_metrics:
            fig_scatter = create_commits_vs_story_points(user_metrics)
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data available for scatter plot")
    
    with col4:
        st.markdown('<div id="jira-ticket-types"></div>', unsafe_allow_html=True)
        st.subheader("🎫 Jira Ticket Types")
        fig_tickets = create_ticket_types_chart(df, selected_user)
        st.plotly_chart(fig_tickets, use_container_width=True)
    
    st.markdown("---")
    
    # Separate GitLab and Jira Analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div id="gitlab-analytics"></div>', unsafe_allow_html=True)
        st.subheader("🦊 GitLab Analytics")
        gitlab_container = st.container()
        
        if selected_user == "All Users":
            total_commits = len(df[df['commit_short_id'] != ''])
            active_projects = df['project_name'].nunique()
            
            gitlab_container.metric("Total Commits", f"{total_commits:,}")
            gitlab_container.metric("Active Projects", f"{active_projects}")
            
            # Top contributors (using normalized names)
            top_contributors = df[df['commit_short_id'] != '']['commit_author_name_normalized'].value_counts().head(5)
            gitlab_container.write("**Top Contributors:**")
            for contributor, commits in top_contributors.items():
                if contributor:  # Skip empty names
                    gitlab_container.write(f"• {contributor}: {commits} commits")
        
        else:
            user_data = user_metrics.get(selected_user, {})
            gitlab_container.metric("User Commits", f"{user_data.get('total_commits', 0):,}")
            gitlab_container.metric("Active Projects", f"{len(user_data.get('projects', []))}")
            gitlab_container.metric("Avg Commits/Week", f"{user_data.get('commits_per_week', 0)}")
            
            if user_data.get('projects'):
                gitlab_container.write("**Projects:**")
                for project in user_data.get('projects', []):
                    if project:
                        gitlab_container.write(f"• {project}")
    
    with col2:
        st.markdown('<div id="jira-analytics"></div>', unsafe_allow_html=True)
        st.subheader("🎯 Jira Analytics")
        jira_container = st.container()
        
        if selected_user == "All Users":
            total_tickets = len(df[df['jira_key'] != ''])
            completed_tickets = len(df[df['jira_status'] == 'Done'])
            completion_rate = (completed_tickets / max(total_tickets, 1)) * 100
            
            jira_container.metric("Total Tickets", f"{total_tickets:,}")
            jira_container.metric("Completed Tickets", f"{completed_tickets:,}")
            jira_container.metric("Completion Rate", f"{completion_rate:.1f}%")
            
            # Ticket status distribution
            status_dist = df[df['jira_status'] != '']['jira_status'].value_counts().head(5)
            jira_container.write("**Ticket Status Distribution:**")
            for status, count in status_dist.items():
                jira_container.write(f"• {status}: {count}")
        
        else:
            user_data = user_metrics.get(selected_user, {})
            jira_container.metric("User Tickets", f"{user_data.get('total_tickets', 0):,}")
            jira_container.metric("Completed", f"{user_data.get('completed_tickets', 0):,}")
            jira_container.metric("Completion Rate", f"{user_data.get('completion_rate', 0)}%")
            jira_container.metric("Avg Time/Story Point", f"{user_data.get('avg_time_per_story_point', 0):.1f}h")
    
    # Data table section
    st.markdown("---")
    st.markdown('<div id="data-overview"></div>', unsafe_allow_html=True)
    st.subheader("📋 Data Overview")
    
    # Show filtered data based on user selection
    if selected_user and selected_user != "All Users":
        filtered_data = df[
            (df['commit_author_name_normalized'] == selected_user) | 
            (df['jira_assignee_normalized'] == selected_user)
        ]
        st.write(f"Showing data for: **{selected_user}**")
    else:
        filtered_data = df.head(100)  # Show first 100 rows for performance
        st.write("Showing first 100 rows of data")
    
    # Display columns selector
    available_columns = df.columns.tolist()
    default_columns = ['project_name', 'commit_author_name_normalized', 'jira_assignee_normalized', 'jira_key', 'jira_status', 'jira_story_points']
    # Only include columns that exist in the dataframe
    default_columns = [col for col in default_columns if col in available_columns]
    
    selected_columns = st.multiselect(
        "Select columns to display:",
        available_columns,
        default=default_columns
    )
    
    if selected_columns:
        st.dataframe(filtered_data[selected_columns], use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>📊 PMS Dashboard with Unified User Names - Built with Streamlit | 🔄 Auto-refreshes with new data</p>
        <p>🔗 GitLab names automatically mapped to Jira assignee format</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()