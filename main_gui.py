import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QProgressDialog,
    QSpacerItem, QSizePolicy, QCheckBox
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
    'Abdellah CHAMI': 'Chami, Abdellah, HSE DE (External)',
    'Badreddine Bendriss': 'Bendriss, Badreddine, HSE DE (External)',
    'younes elmorabit': 'Elmorabit, Younes, HSE DE (External)',
    'ibrahim Ahdadou': 'Ahdadou, Ibrahim, HSE DE (External)',
    'Zakaria Zanati': 'Zanati, Zakaria, HSE DE (External)',
    'tawfiq khnicha': 'Khnicha, Tawfiq, HSE DE (External)',
    'Alok Sharma': 'Sharma, Alok, HSE DE',
    'Anas Boulmane': 'Anas, Boulmane, HSE DE (External)',
    'Ilia Balashov': 'Balashov, Ilia, HSE DE'
}


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


class CommitAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Developer Analysis Dashboard")
        self.resize(1100, 800)

        self.commit_df = None
        self.jira_df = None
        self.canonical_map = None
        self.summary_sorted = None

        self.initUI()
        self.load_data()
        self.populate_dropdown()

    def initUI(self):
        # Futuristic light gradient theme
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f0f4ff, stop:1 #e8f0ff
                );
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }

            QLabel {
                color: #333;
                font-weight: bold;
            }

            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 200px;
                selection-background-color: #d0e9ff;
            }

            QPushButton {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a6d8ff, stop:1 #85c1ff
                );
                color: #003366;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #91cfff, stop:1 #6fb7ff
                );
            }

            QProgressDialog {
                background-color: #ffffff;
                border: 1px solid #aaa;
            }
        """)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        plot_layout = QVBoxLayout()

        # Developer dropdown
        self.combo_authors = QComboBox()
        control_layout.addWidget(QLabel("Select Developer:"))
        control_layout.addWidget(self.combo_authors)

        # Curve/Bar checkbox
        self.checkbox_curve = QCheckBox("Show as curve")
        control_layout.addWidget(self.checkbox_curve)

        # Plot button
        self.btn_plot = QPushButton("Generate Plots")
        self.btn_plot.clicked.connect(self.plot_selected_author)
        control_layout.addWidget(self.btn_plot)

        # First plot
        self.fig1, self.ax1 = plt.subplots(figsize=(8, 5))
        self.canvas1 = FigureCanvas(self.fig1)

        # Second plot
        self.fig2, self.ax2 = plt.subplots(figsize=(8, 5))
        self.canvas2 = FigureCanvas(self.fig2)

        # Add spacing between plots
        plot_layout.addWidget(self.canvas1)
        plot_layout.addItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        plot_layout.addWidget(self.canvas2)

        # Combine layouts
        main_layout.addLayout(control_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(plot_layout)
        self.setLayout(main_layout)

    def normalize_name(self, name):
        return ''.join(e for e in name.lower() if e.isalnum())

    def load_data(self):
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
            ax.text(0.5, 0.5, "Loading...", ha='center', va='center', fontsize=14, color='black', alpha=0.6)
            ax.axis('off')
            canvas.draw()

        self.btn_plot.setEnabled(False)

        self.progress = QProgressDialog("Data extraction ongoing, please wait...", None, 0, 0, self)
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
            self.jira_df = pd.read_csv(f"{assignee_name}.csv")
        except FileNotFoundError:
            print(f"Jira file not found for: {assignee_name}")
            self.btn_plot.setEnabled(True)
            return

        author = self.combo_authors.currentText()

        # Plot Git commits
        plot_type = 'curve' if self.checkbox_curve.isChecked() else 'bar'
        plot_author_commits(self.commit_df, author, self.ax1, plot_type)
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
