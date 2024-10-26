from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QLabel, QListWidget, 
                             QSplitter, QComboBox, QPlainTextEdit, QTextEdit,
                             QListWidgetItem, QInputDialog, QMessageBox, QDialog,
                             QFormLayout, QDialogButtonBox, QAbstractItemView, QAction)
from PyQt5.QtCore import Qt, QUrl, QSize, QThread, pyqtSignal, QTimer, QPoint, QMimeData
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QPalette, QColor, QDrag
from PyQt5.QtWidgets import QStyleFactory, QApplication
import json
import re
import os
from datetime import datetime
from ollama_handler import OllamaThread, get_available_models

class AIToolConfigDialog(QDialog):
    def __init__(self, tool_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Configure {tool_name}")
        self.layout = QVBoxLayout(self)
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Enter default prompt for this tool...")
        self.layout.addWidget(self.prompt_edit)
        
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.copy_prompt)
        self.layout.addWidget(self.copy_button)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def copy_prompt(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.prompt_edit.toPlainText())
        QMessageBox.information(self, "Copied", "Prompt copied to clipboard.")

class AIWorkStationHub(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("AI WorkStation Hub v0.5")
        self.setGeometry(200, 200, 300, 600)  # שינוי הגודל ההתחלתי
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.ai_tools_sidebar = QListWidget()
        self.populate_ai_tools_sidebar()
        self.ai_tools_sidebar.itemClicked.connect(self.ai_tool_selected)
        self.layout.addWidget(self.ai_tools_sidebar)

        # הוספת אפשרות לשינוי גודל
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)

    def populate_ai_tools_sidebar(self):
        self.ai_categories = {
            "📝 Content Creation": ["✍️ Article Writer", "📱 Social Media Post Generator", "🎬 Script Writer", "💻 Code Generator", "📧 Email Composer"],
            "🎨 Graphic Design": ["🖼️ Logo Creator", "📊 Infographic Maker", "🖌️ Illustration Generator", "🖥️ UI Designer"],
            "🖼️ Image & Video": ["🔍 Image Enhancer", "🎭 Animation Creator", "🎞️ Video Editor", "👁️ Object Detector"],
            "📊 Data Analysis": ["📈 Predictive Analytics", "🏷️ Classification Tool", "😃 Sentiment Analyzer", "💡 Insight Generator"],
            "🤖 Customer Service": ["💬 Chatbot Creator", "🗣️ Virtual Assistant", "🆘 Automated Support"],
            "👨‍💻 Software Development": ["⌨️ Code Writer", "🐛 Bug Detector", "⚙️ Process Automator"]
        }
        
        for category, tools in self.ai_categories.items():
            category_item = QListWidgetItem(category)
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            font = category_item.font()
            font.setBold(True)
            category_item.setFont(font)
            category_item.setBackground(QColor(70, 70, 70))
            category_item.setForeground(QColor(200, 200, 200))
            self.ai_tools_sidebar.addItem(category_item)
            
            for tool in tools:
                tool_item = QListWidgetItem(tool)
                tool_item.setData(Qt.UserRole, tool)
                self.ai_tools_sidebar.addItem(tool_item)

    def ai_tool_selected(self, item):
        tool_name = item.data(Qt.UserRole)
        if tool_name:
            self.configure_ai_tool(tool_name)

    def configure_ai_tool(self, tool_name):
        dialog = AIToolConfigDialog(tool_name, self)
        dialog.exec_()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = AIWorkStationHub()
    window.show()
    sys.exit(app.exec_())
