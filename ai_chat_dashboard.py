import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QFont

class AIChatDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chat Dashboard 🎛️")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()
        self.ai_chat_process = None

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title = QLabel("AI Chat Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # AI Chat הפעלת כפתור
        self.ai_chat_button = self.create_action_button("🤖", "Start AI Chat", self.toggle_ai_chat)
        layout.addWidget(self.ai_chat_button)

        # מחוון סטטוס
        self.status_indicator = QLabel("🔴 Inactive")
        self.status_indicator.setAlignment(Qt.AlignCenter)
        self.status_indicator.setFont(QFont("Arial", 14))
        layout.addWidget(self.status_indicator)

        # כפתורי פונקציות נוספות
        features_layout = QHBoxLayout()
        features_layout.addWidget(self.create_action_button("🔍", "Advanced Search", self.advanced_search))
        features_layout.addWidget(self.create_action_button("📊", "Analytics", self.show_analytics))
        features_layout.addWidget(self.create_action_button("🔧", "Settings", self.open_settings))
        features_layout.addWidget(self.create_action_button("🔌", "Plugins", self.manage_plugins))
        layout.addLayout(features_layout)

    def create_action_button(self, emoji, text, action):
        button = QPushButton(f"{emoji} {text}")
        button.setFont(QFont("Arial", 12))
        button.clicked.connect(action)
        return button

    def toggle_ai_chat(self):
        if self.ai_chat_process is None or self.ai_chat_process.state() == QProcess.NotRunning:
            self.start_ai_chat()
        else:
            self.stop_ai_chat()

    def start_ai_chat(self):
        self.ai_chat_process = QProcess()
        script_path = os.path.join(os.path.dirname(__file__), "X-AI-Chat.py")
        self.ai_chat_process.start(sys.executable, [script_path])
        self.ai_chat_process.finished.connect(self.on_ai_chat_finished)
        self.status_indicator.setText("🟢 Active")
        self.ai_chat_button.setText("🤖 Stop AI Chat")

    def stop_ai_chat(self):
        if self.ai_chat_process:
            self.ai_chat_process.terminate()
            self.ai_chat_process.waitForFinished(5000)
            if self.ai_chat_process.state() == QProcess.Running:
                self.ai_chat_process.kill()
        self.status_indicator.setText("🔴 Inactive")
        self.ai_chat_button.setText("🤖 Start AI Chat")

    def on_ai_chat_finished(self):
        self.status_indicator.setText("🔴 Inactive")
        self.ai_chat_button.setText("🤖 Start AI Chat")
        self.ai_chat_process = None

    def advanced_search(self):
        print("Advanced Search clicked")
        # יישום פונקציונליות חיפוש מתקדם

    def show_analytics(self):
        print("Analytics clicked")
        # יישום תצוגת אנליטיקה

    def open_settings(self):
        print("Settings clicked")
        # יישום דיאלוג הגדרות

    def manage_plugins(self):
        print("Plugins clicked")
        # יישום ניהול תוספים

    def closeEvent(self, event):
        self.stop_ai_chat()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = AIChatDashboard()
    dashboard.show()
    sys.exit(app.exec_())
