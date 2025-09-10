import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QProgressDialog,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from rapidfuzz import process, fuzz

from plot_commits import plot_author_commits
from plot_jira import plot_jira_timings
from jiraExtract import StartExtraction

# Developer to Jira assignee name mapping
name_combination = {
    'AbdellahChami': 'Chami, Abdellah, HSE DE (External)',
    'Abdellah Chami': 'Chami, Abdellah, HSE DE (External)',
    'Abdellah': 'Chami, Abdellah, HSE DE (External)',
    'Badreddine Bendriss': 'Bendriss, Badreddine, HSE DE (External)',
    'yelmorabit': 'Elmorabit, Younes, HSE DE (External)',
    'younes elmorabit': 'Elmorabit, Younes, HSE DE (External)',
    'YounesElmorabit': 'Elmorabit, Younes, HSE DE (External)',
    'Yassine El Kasmy': 'ElKasmy, Yassine, HSE DE (External)',
    'elkasmyyassine': 'ElKasmy, Yassine, HSE DE (External)',
    'yassineelkasmy': 'ElKasmy, Yassine, HSE DE (External)',
    'ibrahim Ahdadou': 'Ahdadou, Ibrahim, HSE DE (External)',
    'IbrahimAhdadou': 'Ahdadou, Ibrahim, HSE DE (External)',
    'ilyass ayach': 'Ayach, Ilyass, HSE DE (External)',
    'IlyassAyach': 'Ayach, Ilyass, HSE DE (External)',
    'Zakaria Zanati': 'Zanati, Zakaria, HSE DE (External)',
    'ZakariaZanati': 'Zanati, Zakaria, HSE DE (External)',
    'Zakaria.Zanati': 'Zanati, Zakaria, HSE DE (External)',
}


# Background thread for Jira extraction
class ExtractionThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, assignee_key):
        super().__init__()
        self.assignee_key = assignee_key

    def run(self):
        current_assignee = name_combination.get(self.assignee_key)
        if current_assignee:
            StartExtraction(current_assignee)
            self.finished_signal.emit(current_assignee)
        else:
            self.finished_signal.emit("")


# Main UI class
class CommitAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Developer Analysis Dashboard")
        self.resize(1100, 800)  # Increased height

        self.commit_df = None
        self.jira_df = None
        self.canonical_map = None
        self.summary_sorted = None

        self.initUI()
        self.load_data()
        self.populate_dropdown()

    def initUI(self):
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        plot_layout = QVBoxLayout()

        # Dropdown
        self.combo_authors = QComboBox()
        self.combo_authors.setMinimumWidth(300)
        control_layout.addWidget(QLabel("Select Developer:"))
        control_layout.addWidget(self.combo_authors)

        # Plot button
        self.btn_plot = QPushButton("Generate Plots")
        self.btn_plot.clicked.connect(self.plot_selected_author)
        control_layout.addWidget(self.btn_plot)

        # Plot areas
        self.fig1, self.ax1 = plt.subplots(figsize=(8, 5))
        self.canvas1 = FigureCanvas(self.fig1)

        self.fig2, self.ax2 = plt.subplots(figsize=(8, 5))
        self.canvas2 = FigureCanvas(self.fig2)

        # Add plots and spacing
        plot_layout.addWidget(self.canvas1)
        plot_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        plot_layout.addWidget(self.canvas2)

        # Apply layouts
        main_layout.addLayout(control_layout)
        main_layout.addLayout(plot_layout)
        self.setLayout(main_layout)

    def normalize_name(self, name):
        return ''.join(e for e in name.lower() if e.isalnum())

    def load_data(self):
        #import data from gitlab export
        self.commit_df = pd.read_csv("commit_details.csv")
        self.commit_df['committed_date'] = pd.to_datetime(self.commit_df['committed_date'], errors='coerce', utc=True)
        self.commit_df.dropna(subset=['author_name', 'committed_date'], inplace=True)
        self.commit_df['commit_day'] = self.commit_df['committed_date'].dt.date

        unique_names = self.commit_df['author_name'].unique()
        normalized_names = [self.normalize_name(n) for n in unique_names]
        self.canonical_map = {}

        for i, name in enumerate(unique_names):
            norm_name = normalized_names[i]
            if name in self.canonical_map:
                continue
            matches = process.extract(norm_name, normalized_names, scorer=fuzz.ratio, score_cutoff=90)
            canonical = name
            for match_norm, score, idx in matches:
                variant = unique_names[idx]
                self.canonical_map[variant] = canonical

        self.commit_df['author_canonical'] = self.commit_df['author_name'].map(self.canonical_map)

        grouped = self.commit_df.groupby('author_canonical').agg(
            total_commits=('commit_day', 'count'),
            unique_days=('commit_day', 'nunique')
        )
        grouped['avg_commits_per_day'] = grouped['total_commits'] / grouped['unique_days']
        self.summary_sorted = grouped.sort_values(by='avg_commits_per_day', ascending=False).reset_index()

    def populate_dropdown(self):
        authors = self.summary_sorted['author_canonical'].tolist()
        self.combo_authors.clear()
        self.combo_authors.addItems(authors)

    def plot_selected_author(self):
        author = self.combo_authors.currentText()

        for ax, canvas in [(self.ax1, self.canvas1), (self.ax2, self.canvas2)]:
            ax.clear()
            ax.text(0.5, 0.5, "Loading...", ha='center', va='center', fontsize=14, color='gray', alpha=0.6)
            ax.axis('off')
            canvas.draw()

        self.btn_plot.setEnabled(False)

        self.progress = QProgressDialog("Jira data extraction ongoing, please wait...", None, 0, 0, self)
        self.progress.setWindowTitle("Processing")
        self.progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress.setCancelButton(None)
        self.progress.show()

        self.thread = ExtractionThread(author)
        self.thread.finished_signal.connect(self.on_extraction_finished)
        self.thread.start()

    def on_extraction_finished(self, assignee_name):
        self.progress.close()

        if not assignee_name:
            print("Invalid or unmapped author.")
            self.btn_plot.setEnabled(True)
            return

        try:
            # read the Jira extraction 
            self.jira_df = pd.read_csv(f"{assignee_name}.csv")
        except FileNotFoundError:
            print(f"Jira file not found for: {assignee_name}")
            self.btn_plot.setEnabled(True)
            return

        author = self.combo_authors.currentText()

        # Plot Git commits
        plot_author_commits(self.commit_df, author, self.ax1)
        self.ax1.figure.tight_layout()
        self.canvas1.draw()

        # Plot Jira timings
        cleaned_assignee = assignee_name.replace(",", "").replace("(", "").replace(")", "")
        plot_jira_timings(self.jira_df, cleaned_assignee, self.ax2)
        self.ax2.figure.tight_layout()
        self.canvas2.draw()

        self.btn_plot.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = CommitAnalyzer()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
