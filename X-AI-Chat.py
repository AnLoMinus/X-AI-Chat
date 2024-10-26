import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import sys
import subprocess
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtChart import *
import qdarkstyle
import datetime
import getpass
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import speech_recognition as sr
from gtts import gTTS
import pygame
import platform
import pyaudio
from settings_dialog import SettingsDialog
from instructions_dashboard import InstructionsDashboard
from ai_workstation_hub import AIWorkStationHub
from ollama_handler import OllamaThread, get_available_models
from ai_chat_extensions import initialize_extensions

# הגדרת מערכת הלוגים
def setup_logger():
    logger = logging.getLogger('AIChat')
    logger.setLevel(logging.DEBUG)

    # יצירת תיקיית לוגים אם היא לא קיימת
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # הגדרת handler לקובץ ע רוטציה
    file_handler = RotatingFileHandler('logs/aichat.log', maxBytes=1024*1024, backupCount=5)
    file_handler.setLevel(logging.DEBUG)

    # הגדרת handler לקונסול
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # יצית פורמט ללוגים
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # הוספת ה-handlers ללוגר
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

# הגדרת פלטת צבעים הרמונית
COLORS = {
    'background': '#1E1E1E',
    'surface': '#2D2D2D',
    'primary': '#3700B3',
    'secondary': '#03DAC6',
    'on_background': '#E1E1E1',
    'on_surface': '#FFFFFF',
    'on_primary': '#FFFFFF',
    'on_secondary': '#000000',
    'error': '#CF6679',
    'success': '#03DAC6',
    'warning': '#FFAB00',
}

class ChatMessage(QFrame):
    def __init__(self, text, is_user=True, parent=None, model_name=None, tokens=0):
        super().__init__(parent)
        self.text = text
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        header_layout = QHBoxLayout()
        
        # שם המשתמש או המודל
        name_label = QLabel(f"{getpass.getuser()}" if is_user else f"{model_name}")
        name_label.setStyleSheet(f"""
            color: {COLORS['on_surface']};
            font-weight: bold;
            font-size: 14px;
        """)
        header_layout.addWidget(name_label)
        
        # תאריך ושעה
        timestamp = QLabel(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        timestamp.setStyleSheet(f"""
            color: {COLORS['on_surface']};
            font-size: 10px;
        """)
        header_layout.addWidget(timestamp)
        
        header_layout.addStretch(1)
        
        # מספר טוקנים
        tokens_label = QLabel(f"Tokens: {tokens}")
        tokens_label.setStyleSheet(f"""
            color: {COLORS['on_surface']};
            font-size: 10px;
        """)
        header_layout.addWidget(tokens_label)
        
        layout.addLayout(header_layout)
        
        message = QLabel(text)
        message.setWordWrap(True)
        message.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['on_surface']};
            background-color: {COLORS['surface']};
            border-radius: 10px;
            padding: 10px;
        """)
        layout.addWidget(message)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        for icon, tooltip, action in [
            ("🔖", "Bookmark", self.add_bookmark),
            ("⏰", "Set Reminder", self.add_reminder),
            ("🔊", "Speak Message", self.speak_message),
            ("📋", "Copy", self.copy_text)
        ]:
            button = QPushButton(icon)
            button.setToolTip(tooltip)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['on_surface']};
                    border: none;
                    border-radius: 15px;
                    padding: 5px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary']};
                    color: {COLORS['on_primary']};
                }}
            """)
            button.clicked.connect(action)
            button_layout.addWidget(button)
        
        button_layout.addStretch(1)
        layout.addLayout(button_layout)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 15px;
                margin: 5px;
            }}
        """)

    def get_main_window(self):
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, AIChat):
                return parent
            parent = parent.parent()
        return None

    def add_bookmark(self):
        main_window = self.get_main_window()
        if main_window:
            main_window.add_bookmark(self.text)

    def add_reminder(self):
        main_window = self.get_main_window()
        if main_window:
            main_window.add_reminder(self.text)

    def speak_message(self):
        main_window = self.get_main_window()
        if main_window:
            main_window.speak_message(self.text)

    def copy_text(self):
        QApplication.clipboard().setText(self.text)

class Conversation:
    def __init__(self, name):
        self.name = name
        self.messages = []

class AIChat(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chat v0.9.8 🤖")
        self.setGeometry(100, 100, 1200, 800)
        self.conversations = []
        self.current_conversation = -1
        self.font_size = 12
        self.username = getpass.getuser()
        self.current_model = None
        logger.info(f"Initializing AI Chat application for user: {self.username}")
        self.bookmarks = []
        self.reminders = []
        self.preset_instructions = self.load_preset_instructions()
        self.setup_rtl()
        self.ui_scale = 100
        self.current_theme = "Default"
        self.load_plugins()
        self.setup_ui()
        self.setup_toolbar()
        self.setup_connections()
        self.apply_glass_theme()
        self.setup_menu_bar()
        self.setup_status_bar()
        self.setup_footer()
        self.refresh_models()
        self.setup_clock()
        self.setup_workstation_button()
        self.workstation_hub = None
        logger.info("Application initialized successfully")
        self.extensions = initialize_extensions(self)
        self.toolbar = self.addToolBar("Main Toolbar")

    def setup_rtl(self):
        QGuiApplication.setLayoutDirection(Qt.RightToLeft)
        QLocale.setDefault(QLocale(QLocale.Hebrew, QLocale.Israel))

    def setup_ui(self):
        logger.debug("Setting up UI")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sidebar (now on the right side)
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        
        # שדרוג מקטע שם האפליקציה
        app_header = QWidget()
        app_header_layout = QHBoxLayout(app_header)
        app_header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.logo_button = QPushButton("🤖", self)
        self.logo_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 48px;
                background-color: transparent;
                border: none;
                color: {COLORS['on_background']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
        """)
        self.logo_button.clicked.connect(self.open_settings_dashboard)
        app_header_layout.addWidget(self.logo_button)
        
        app_info_layout = QVBoxLayout()
        app_name_label = QLabel("AI Chat", alignment=Qt.AlignLeft)
        app_name_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['on_background']};")
        app_info_layout.addWidget(app_name_label)
        
        version_label = QLabel("v0.9.8", alignment=Qt.AlignLeft)
        version_label.setStyleSheet(f"font-size: 12px; color: {COLORS['on_background']};")
        app_info_layout.addWidget(version_label)
        
        app_header_layout.addLayout(app_info_layout)
        app_header_layout.addStretch(1)
        
        sidebar_layout.addWidget(app_header)
        
        self.conversation_list = QListWidget()
        self.conversation_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {COLORS['surface']};
                border: none;
                border-radius: 5px;
                padding: 5px;
            }}
            QListWidget::item {{
                background-color: {COLORS['background']};
                color: {COLORS['on_background']};
                border-radius: 3px;
                padding: 5px;
                margin: 2px 0;
            }}
            QListWidget::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
        """)
        self.conversation_list.currentRowChanged.connect(self.change_conversation)
        sidebar_layout.addWidget(self.conversation_list)

        new_chat_button = QPushButton("New Chat 💬")
        new_chat_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                color: {COLORS['on_secondary']};
            }}
        """)
        new_chat_button.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(new_chat_button)

        # הוספת כפתורי ייצוא וייבוא לתוך מסגרת רשימת השיחות
        export_import_layout = QHBoxLayout()
        export_button = QPushButton("📤")
        export_button.setToolTip("Export Chats")
        export_button.clicked.connect(self.export_conversations)
        export_import_layout.addWidget(export_button)

        import_button = QPushButton("📥")
        import_button.setToolTip("Import Chats")
        import_button.clicked.connect(self.import_conversations)
        export_import_layout.addWidget(import_button)

        export_import_layout.setContentsMargins(0, 0, 0, 0)
        export_import_widget = QWidget()
        export_import_widget.setLayout(export_import_layout)
        export_import_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border-radius: 5px;
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                font-size: 16px;
                padding: 5px;
                color: {COLORS['on_surface']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
        """)
        sidebar_layout.addWidget(export_import_widget)

        upload_button = QPushButton("Upload File 📎")
        upload_button.clicked.connect(self.upload_file)
        sidebar_layout.addWidget(upload_button)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.returnPressed.connect(self.search_history)
        sidebar_layout.addWidget(self.search_input)

        bookmark_button = QPushButton("Bookmarks and Reminders 🔖")
        bookmark_button.clicked.connect(self.show_bookmarks_and_reminders)
        sidebar_layout.addWidget(bookmark_button)

        stats_button = QPushButton("Statistics 📊")
        stats_button.clicked.connect(self.show_statistics)
        sidebar_layout.addWidget(stats_button)

        # שיפור עיצוב הסרגל הצדדי
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border-radius: 10px;
            }}
            QPushButton {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border: none;
                padding: 10px;
                margin: 5px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
        """)

        # הוספת הסרגל הצדדי לימין של התצוגה הראשית
        main_layout.addWidget(sidebar)

        # Chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        self.chat_stack = QStackedWidget()
        chat_layout.addWidget(self.chat_stack)

        chat_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border-radius: 10px;
            }}
        """)

        # הוספת כפתורים מעל תיבת הקלט
        button_layout = QHBoxLayout()
        
        for icon, tooltip, action in [
            ("📎", "Upload File", self.upload_file),
            ("📊", "Statistics", self.show_statistics),
            ("🔖", "Bookmarks and Reminders", self.show_bookmarks_and_reminders),
            ("🎤", "Voice Input", self.start_voice_input),
            ("📝", "Preset Instructions", self.show_instructions_dashboard)
        ]:
            button = QPushButton(icon)
            button.setToolTip(tooltip)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['surface']};
                    color: {COLORS['on_surface']};
                    border: none;
                    padding: 5px;
                    border-radius: 5px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['primary']};
                    color: {COLORS['on_primary']};
                }}
            """)
            button.clicked.connect(action)
            button_layout.addWidget(button)
        
        chat_layout.addLayout(button_layout)

        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("הקלד את ההודעה שלך כאן... (Shift+Enter להוספת שורה, Enter לשליחה)")
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['primary']};
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                color: {COLORS['on_surface']};
            }}
        """)
        self.input_field.setFixedHeight(60)
        self.input_field.setMinimumHeight(60)
        self.input_field.setMaximumHeight(200)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field)

        send_button = QPushButton("שלח")
        send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                color: {COLORS['on_secondary']};
            }}
        """)
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        chat_layout.addLayout(input_layout)

        # הוספת שורת תפריט מעל תיבת הקלט
        input_menu_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.preset_instructions.keys())
        self.preset_combo.currentTextChanged.connect(self.update_preset_instructions)
        self.preset_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border: 1px solid {COLORS['primary']};
                border-radius: 3px;
                padding: 2px 5px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {COLORS['primary']};
                border-left-style: solid;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
            }}
        """)
        input_menu_layout.addWidget(self.preset_combo)

        self.instruction_combo = QComboBox()
        self.instruction_combo.currentTextChanged.connect(self.insert_instruction)
        self.instruction_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border: 1px solid {COLORS['primary']};
                border-radius: 3px;
                padding: 2px 5px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: {COLORS['primary']};
                border-left-style: solid;
            }}
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
            }}
        """)
        input_menu_layout.addWidget(self.instruction_combo)

        chat_layout.addLayout(input_menu_layout)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(chat_widget)
        splitter.setSizes([1000])
        main_layout.addWidget(splitter)

        self.statusBar().showMessage("Ready")

        self.new_chat()

        logger.debug("UI setup completed")

    def setup_connections(self):
        self.conversation_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.conversation_list.customContextMenuRequested.connect(self.show_context_menu)

    def add_chat_display(self):
        chat_display = QWidget()
        chat_display_layout = QVBoxLayout(chat_display)
        chat_display_layout.setAlignment(Qt.AlignTop)
        chat_display_layout.setSpacing(10)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(chat_display)
        self.chat_stack.addWidget(scroll_area)

    def new_chat(self):
        logger.info("Creating new chat")
        initial_message = "שלום! כיצד אוכל לסייע לך היום? 😊"
        new_conv = Conversation(f"שיחה חדשה {len(self.conversations) + 1} 💬")
        self.conversations.append(new_conv)
        self.add_chat_display()
        item = QListWidgetItem(new_conv.name)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.conversation_list.addItem(item)
        self.conversation_list.setCurrentRow(len(self.conversations) - 1)
        self.add_message_to_chat(initial_message, False)
        logger.info(f"New chat created: {new_conv.name}")

    def generate_chat_title(self, conversation_index, num_suggestions=3):
        conversation = self.conversations[conversation_index]
        
        prompt = f"Based on this conversation, suggest {num_suggestions} short and descriptive titles (max 5 words each):\n\n"
        for msg, is_user in conversation.messages[:5]:  # Use up to the first 5 messages
            prompt += f"{'User' if is_user else 'AI'}: {msg}\n"
        
        selected_model = self.model_selector.currentText()
        titles = self.get_ollama_response(selected_model, prompt).strip().split('\n')
        
        # Limit each title to 5 words and ensure we have the correct number of suggestions
        titles = [' '.join(title.split()[:5]) for title in titles[:num_suggestions]]
        titles = titles + [f"Suggestion {i+1}" for i in range(len(titles), num_suggestions)]
        
        chosen_title = self.choose_title_dialog(titles)
        
        if chosen_title:
            conversation.name = chosen_title
            self.conversation_list.item(conversation_index).setText(chosen_title)

    def change_conversation(self, index):
        if 0 <= index < len(self.conversations):
            self.current_conversation = index
            self.chat_stack.setCurrentIndex(index)

    def get_ollama_models(self):
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            models = result.stdout.strip().split('\n')[1:]  # Skip the header
            return [model.split()[0] for model in models]
        except Exception as e:
            self.statusBar().showMessage(f"Error fetching Ollama models: {e}")
            return ["Default Model"]

    def refresh_models(self):
        current_model = self.model_selector.currentText()
        self.model_selector.clear()
        models = self.get_ollama_models()
        self.model_selector.addItems(models)
        if current_model in models:
            self.model_selector.setCurrentText(current_model)
        else:
            self.update_current_model(self.model_selector.currentText())
        self.statusBar().showMessage("Models refreshed")

    def send_message(self):
        user_message = self.input_field.toPlainText().strip()
        if user_message:
            logger.info(f"Sending user message: {user_message[:50]}...")
            self.add_message_to_chat(user_message, True)
            self.input_field.clear()
            self.input_field.setFixedHeight(60)  # Reset input field height after sending

            self.statusBar().showMessage("Processing...")
            self.progress_bar.setVisible(True)
            
            logger.debug(f"Starting Ollama thread with model: {self.current_model}")
            self.ollama_thread = OllamaThread(self.current_model, f"{self.username}: {user_message}")
            self.ollama_thread.response_received.connect(self.handle_ollama_response)
            self.ollama_thread.error_occurred.connect(self.handle_ollama_error)
            self.ollama_thread.finished.connect(self.ollama_request_finished)
            self.ollama_thread.start()

    def handle_ollama_response(self, response):
        logger.info(f"AI response received: {response[:50]}...")
        tokens = self.calculate_tokens(response)
        self.add_message_to_chat(response, False, tokens)

    def calculate_tokens(self, text):
        # This is a simple token calculation. Replace with a more accurate method if needed.
        return len(text.split())

    def handle_ollama_error(self, error_message):
        logger.error(f"Ollama error: {error_message}")
        self.add_message_to_chat(error_message, False)

    def ollama_request_finished(self):
        logger.debug("Ollama request finished")
        self.statusBar().showMessage("Ready")
        self.progress_bar.setVisible(False)

    def add_message_to_chat(self, message, is_user, tokens=None):
        if self.current_conversation >= 0:
            chat_display = self.chat_stack.widget(self.current_conversation).widget()
            if tokens is None:
                tokens = self.calculate_tokens(message)
            message_widget = ChatMessage(message, is_user, model_name=self.current_model, tokens=tokens)
            message_widget.setStyleSheet(f"""
                ChatMessage {{
                    background-color: {COLORS['surface']};
                    border-radius: 10px;
                    margin: 5px;
                    padding: 10px;
                }}
            """)
            
            chat_display.layout().addWidget(message_widget)
            
            # Scroll to bottom
            QTimer.singleShot(0, lambda: self.scroll_to_bottom(self.current_conversation))

            # Add the message to the conversation history
            self.conversations[self.current_conversation].messages.append((message, is_user, self.current_model, tokens))

    def scroll_to_bottom(self, conversation_index):
        scroll_area = self.chat_stack.widget(conversation_index)
        scroll_bar = scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def get_ollama_response(self, model, prompt):
        try:
            result = subprocess.run(['ollama', 'run', model, prompt], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise Exception(f"Ollama returned non-zero exit status {result.returncode}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            return "Error: Ollama response time exceeded the limit."
        except Exception as e:
            return f"Error getting response from Ollama: {str(e)}"

    def closeEvent(self, event):
        logger.info("Application closing")
        self.refresh_timer.stop()
        super().closeEvent(event)

    def rename_conversation(self, item):
        if item:
            current_name = item.text()
            new_name, ok = QInputDialog.getText(self, "Rename Chat 🏷️", "Enter new chat name:", text=current_name)
            if ok and new_name:
                item.setText(new_name)
                self.conversations[self.conversation_list.row(item)].name = new_name
                logger.info(f"Chat renamed from '{current_name}' to '{new_name}'")

    def choose_title_dialog(self, titles):
        dialog = QDialog(self)
        dialog.setWindowTitle("Choose Chat Title")
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Choose a suggested title or enter your own:")
        layout.addWidget(label)
        
        button_group = QButtonGroup(dialog)
        for i, title in enumerate(titles):
            radio = QRadioButton(title)
            button_group.addButton(radio, i)
            layout.addWidget(radio)
        
        custom_title = QLineEdit()
        custom_title.setPlaceholderText("Or enter your own title here")
        layout.addWidget(custom_title)
        
        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            if custom_title.text():
                return custom_title.text()
            elif button_group.checkedId() != -1:
                return titles[button_group.checkedId()]
        return None

    def apply_glass_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                  stop:0 {COLORS['background']}, stop:1 {COLORS['surface']});
            }}
            QWidget {{
                color: {COLORS['on_background']};
                font-family: Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                color: {COLORS['on_secondary']};
            }}
            QLineEdit, QTextEdit {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['primary']};
                border-radius: 4px;
                padding: 4px;
                color: {COLORS['on_surface']};
            }}
            QLabel {{
                color: {COLORS['on_surface']};
            }}
            QMenuBar {{
                background-color: {COLORS['background']};
                color: {COLORS['on_background']};
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
            QMenu {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border: 1px solid {COLORS['primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
        """)

    def change_font_size(self, size):
        self.font_size = size
        for i in range(self.chat_stack.count()):
            chat_display = self.chat_stack.widget(i).widget()
            for j in range(chat_display.layout().count()):
                item = chat_display.layout().itemAt(j).widget()
                if isinstance(item, ChatMessage):
                    item.setStyleSheet(f"font-size: {size}px;")

    def export_conversations(self):
        logger.info("Exporting conversations")
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Conversations", "", "JSON File (*.json)")
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump([{'name': c.name, 'messages': c.messages} for c in self.conversations], f, ensure_ascii=False, indent=2)
                logger.info(f"Conversations exported successfully to {file_name}")
                QMessageBox.information(self, "Export Successful", "Conversations exported successfully.")
            except Exception as e:
                logger.error(f"Error exporting conversations: {str(e)}")
                QMessageBox.critical(self, "Export Error", f"An error occurred while exporting conversations: {str(e)}")

    def import_conversations(self):
        logger.info("Importing conversations")
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Conversations", "", "JSON File (*.json)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    imported_conversations = json.load(f)
                for conv in imported_conversations:
                    new_conv = Conversation(conv['name'])
                    new_conv.messages = conv['messages']
                    self.conversations.append(new_conv)
                    self.add_chat_display()
                    item = QListWidgetItem(new_conv.name)
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    self.conversation_list.addItem(item)
                self.conversation_list.setCurrentRow(len(self.conversations) - 1)
                logger.info(f"Conversations imported successfully from {file_name}")
                QMessageBox.information(self, "Import Successful", "Conversations imported successfully.")
            except Exception as e:
                logger.error(f"Error importing conversations: {str(e)}")
                QMessageBox.critical(self, "Import Error", f"An error occurred while importing conversations: {str(e)}")

    def show_context_menu(self, position):
        item = self.conversation_list.itemAt(position)
        if item is None:
            return

        context_menu = QMenu(self)
        edit_action = QAction("Edit Title 🏷️", self)
        edit_action.triggered.connect(lambda: self.rename_conversation(item))
        context_menu.addAction(edit_action)

        generate_submenu = QMenu("Generate Suggested Titles 🤔", self)
        for num in [1, 3, 5]:
            action = QAction(f"{num} Titles", self)
            action.triggered.connect(lambda checked, n=num: self.generate_chat_title(self.conversation_list.row(item), n))
            generate_submenu.addAction(action)

        context_menu.addMenu(generate_submenu)

        delete_action = QAction("Delete Chat 🗑️", self)
        delete_action.triggered.connect(lambda: self.delete_conversation(self.conversation_list.row(item)))

    def show_about_dialog(self):
        about_text = """
        AI Chat v0.9.8 🤖

        A smart chat application using Ollama for communication with AI models.

        Features:
        - Preset instructions
        - Voice input and output
        - Bookmarks and reminders
        - Enhanced UI with glass effect

        Developed by:
        - Claude (AI Assistant)
        - AnLoMinus

        Thank you for using our application!
        """
        QMessageBox.about(self, "About AI Chat", about_text)

    def setup_status_bar(self):
        self.statusBar().showMessage("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # אינדיקטור פעילות אינסופי
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

    def setup_footer(self):
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)

        # שעון ותאריך
        self.clock_label = QLabel("", alignment=Qt.AlignLeft)
        self.clock_label.setStyleSheet(f"font-size: 14px; color: {COLORS['on_background']};")
        footer_layout.addWidget(self.clock_label)

        footer_layout.addStretch(1)

        # לוגו במרכז
        logo_label = QLabel("🤖", alignment=Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 24px;")
        footer_layout.addWidget(logo_label)

        footer_layout.addStretch(1)

        # Ollama Model selector
        model_layout = QHBoxLayout()
        model_label = QLabel("Ollama Model:")
        model_layout.addWidget(model_label)
        
        self.model_selector = QComboBox()
        self.model_selector.addItems(get_available_models())
        self.model_selector.currentTextChanged.connect(self.update_current_model)
        model_layout.addWidget(self.model_selector)

        refresh_button = QPushButton("🔄")
        refresh_button.setToolTip("Refresh Models")
        refresh_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['secondary']};
                color: {COLORS['on_secondary']};
            }}
        """)
        refresh_button.clicked.connect(self.refresh_models)
        model_layout.addWidget(refresh_button)

        footer_layout.addLayout(model_layout)

        self.statusBar().addPermanentWidget(footer)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_models)
        self.refresh_timer.start(300000)  # רענון כל 5 דקות

        footer.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border-top: 1px solid {COLORS['primary']};
            }}
        """)

    def update_current_model(self, model_name):
        self.current_model = model_name
        logger.info(f"Current model updated to: {self.current_model}")

    def setup_clock(self):
        self.update_clock()
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)  # עדכון כל שנייה

    def update_clock(self):
        current_time = datetime.datetime.now()
        time_str = current_time.strftime("%H:%M:%S")
        date_str = current_time.strftime("%Y-%m-%d")
        self.clock_label.setText(f"{date_str} {time_str}")

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Choose File to Upload")
        if file_path:
            file_name = os.path.basename(file_path)
            with open(file_path, 'rb') as file:
                file_content = file.read()
            self.add_message_to_chat(f"File uploaded: {file_name}", True)
            # כאן תוכל להוסיף לוגיקה לשליחת הובץ ל-AI או לטיפול בו

    def search_history(self):
        search_term = self.search_input.text()
        results = []
        for conv in self.conversations:
            for msg, is_user, model, tokens in conv.messages:
                if search_term.lower() in msg.lower():
                    results.append((conv.name, msg))
        
        # הצג את תוצאות החיפוש בחלון נפרד
        dialog = QDialog(self)
        dialog.setWindowTitle("Search Results")
        layout = QVBoxLayout(dialog)
        result_list = QListWidget()
        for conv_name, msg in results:
            result_list.addItem(f"{conv_name}: {msg[:50]}...")
        layout.addWidget(result_list)
        dialog.exec_()

    def show_bookmarks_and_reminders(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bookmarks and Reminders")
        layout = QVBoxLayout(dialog)
        
        tabs = QTabWidget()
        bookmarks_tab = QWidget()
        reminders_tab = QWidget()
        
        # סימניות
        bookmarks_layout = QVBoxLayout(bookmarks_tab)
        bookmarks_list = QListWidget()
        for bookmark in self.bookmarks:
            bookmarks_list.addItem(bookmark)
        bookmarks_layout.addWidget(bookmarks_list)
        
        # תזכורות
        reminders_layout = QVBoxLayout(reminders_tab)
        reminders_list = QListWidget()
        for reminder in self.reminders:
            reminders_list.addItem(f"{reminder['text']} - {reminder['time'].toString()}")
        reminders_layout.addWidget(reminders_list)
        
        tabs.addTab(bookmarks_tab, "Bookmarks")
        tabs.addTab(reminders_tab, "Reminders")
        layout.addWidget(tabs)
        
        dialog.exec_()

    def show_statistics(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Statistics")
        layout = QVBoxLayout(dialog)
        
        # יצירת גרף עוגה לשימוש במודלים
        pie_chart = QChart()
        series = QPieSeries()
        model_usage = {}
        for conv in self.conversations:
            for _, _, model, _ in conv.messages:
                model_usage[model] = model_usage.get(model, 0) + 1
        for model, count in model_usage.items():
            series.append(model, count)
        pie_chart.addSeries(series)
        pie_chart.setTitle("Model Usage")
        chart_view = QChartView(pie_chart)
        layout.addWidget(chart_view)
        
        # יצירת גרף עמודות למספר ההודעות בכל שיחה
        bar_chart = QChart()
        bar_series = QBarSeries()
        for conv in self.conversations:
            bar_set = QBarSet(conv.name)
            bar_set.append(len(conv.messages))
            bar_series.append(bar_set)
        bar_chart.addSeries(bar_series)
        bar_chart.setTitle("Number of Messages in Each Chat")
        bar_chart_view = QChartView(bar_chart)
        layout.addWidget(bar_chart_view)
        
        dialog.exec_()

    def add_bookmark(self, message):
        self.bookmarks.append(message)
        QMessageBox.information(self, "Bookmark Added", "The message has been added to bookmarks")
        logger.info("Bookmark added")

    def add_reminder(self, message):
        time, ok = QInputDialog.getText(self, "Add Reminder", "Enter reminder time (YYYY-MM-DD HH:MM):")
        if ok:
            try:
                reminder_time = QDateTime.fromString(time, "yyyy-MM-dd HH:mm")
                self.reminders.append({"text": message, "time": reminder_time})
                QMessageBox.information(self, "Reminder Added", f"Reminder set for {time}")
                logger.info(f"Reminder added for {time}")
            except:
                QMessageBox.warning(self, "Error", "Invalid time format")
                logger.warning("Failed to add reminder due to invalid time format")

    def eventFilter(self, source, event):
        if source is self.input_field and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return:
                if event.modifiers() & Qt.ShiftModifier:
                    # Shift+Enter: הוספת שורה חדשה והגדלת התיבה
                    cursor = self.input_field.textCursor()
                    cursor.insertText('\n')
                    self.adjust_input_field_height()
                    return True
                else:
                    # Enter ללא Shift: שליחת ההודעה
                    self.send_message()
                    return True
        return super().eventFilter(source, event)

    def adjust_input_field_height(self):
        document_height = self.input_field.document().size().height()
        new_height = min(max(60, document_height + 20), 200)  # מגביל את הגובה בין 60 ל-200 פיקסלים
        self.input_field.setFixedHeight(int(new_height))

    def load_preset_instructions(self):
        try:
            file_path = os.path.join(os.path.dirname(__file__), 'preset_instructions.json')
            with open(file_path, 'r', encoding='utf-8') as f:
                instructions = json.load(f)
            return instructions
        except FileNotFoundError:
            logger.warning("preset_instructions.json not found. Creating an empty file.")
            empty_instructions = {}
            self.save_preset_instructions(empty_instructions)
            return empty_instructions

    def save_preset_instructions(self, instructions=None):
        if instructions is None:
            instructions = self.preset_instructions
        file_path = os.path.join(os.path.dirname(__file__), 'preset_instructions.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(instructions, f, ensure_ascii=False, indent=2)

    def update_preset_instructions(self, category):
        self.instruction_combo.clear()
        if category in self.preset_instructions:
            self.instruction_combo.addItems(self.preset_instructions[category]['instructions'])

    def insert_instruction(self, instruction):
        if instruction:
            current_text = self.input_field.toPlainText()
            if current_text and not current_text.endswith('\n'):
                self.input_field.append('\n')
            self.input_field.append(instruction)

    def detect_system_and_setup_microphone(self):
        system = platform.system()
        logger.info(f"Detected operating system: {system}")

        if system == "Windows":
            return self.setup_windows_microphone()
        elif system == "Darwin":  # macOS
            return self.setup_macos_microphone()
        elif system == "Linux":
            return self.setup_linux_microphone()
        else:
            logger.warning(f"Unsupported operating system: {system}")
            return None

    def setup_windows_microphone(self):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:
                logger.info(f"Found input device: {dev['name']}")
                return dev['index']
        logger.warning("No suitable microphone found on Windows")
        return None

    def setup_macos_microphone(self):
        try:
            # ניסיון ראשון: שימוש -PyAudio לזיהוי משירי קלט
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            for i in range(0, num_devices):
                if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    device_name = p.get_device_info_by_host_api_device_index(0, i).get('name')
                    logger.info(f"Found input device: {device_name}")
                    return i
            
            # ניסיון שני: שימוש ב-speech_recognition לקבלת רשימת מכשירים
            mic_list = sr.Microphone.list_microphone_names()
            if mic_list:
                logger.info(f"Available microphones: {mic_list}")
                return mic_list.index(mic_list[0])  # בחירת המיקרופון הראשון ברשימה
            
            # ניסיון שלישי: שימוש במיקרופון ברירת המחדל
            logger.info("Using default microphone")
            return None
        
        except Exception as e:
            logger.error(f"Error setting up macOS microphone: {str(e)}")
            return None

    def setup_linux_microphone(self):
        # On Linux, we might need to check ALSA or PulseAudio
        # This is a simplified version, you might need to expand it
        return None

    def start_voice_input(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.statusBar().showMessage("Adjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=1)
                self.statusBar().showMessage("Listening... Speak now.")
                audio = r.listen(source, timeout=10, phrase_time_limit=10)
                self.statusBar().showMessage("Processing speech...")

            text = r.recognize_google(audio, language='en-US')
            self.input_field.append(text)
            self.statusBar().showMessage("Speech recognized")
            logger.info(f"Speech recognized: {text}")
        except sr.WaitTimeoutError:
            self.statusBar().showMessage("No speech detected")
            QMessageBox.warning(self, "Error", "No speech detected. Please try again.")
            logger.warning("No speech detected during voice input")
        except sr.UnknownValueError:
            self.statusBar().showMessage("Could not understand audio")
            QMessageBox.warning(self, "Error", "Could not understand audio. Please try again.")
            logger.warning("Speech recognition failed: Could not understand audio")
        except sr.RequestError as e:
            self.statusBar().showMessage(f"Could not request results; {e}")
            QMessageBox.warning(self, "Error", f"Failed to process speech: {str(e)}")
            logger.error(f"Speech recognition request failed: {str(e)}")
        except Exception as e:
            self.statusBar().showMessage(f"An error occurred: {e}")
            QMessageBox.warning(self, "Error", f"An unexpected error occurred: {str(e)}")
            logger.error(f"Unexpected error during speech recognition: {str(e)}")

    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File 📁")
        new_chat_action = QAction("New Chat 💬", self)
        new_chat_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_chat_action)

        export_action = QAction("Export Chats 📤", self)
        export_action.triggered.connect(self.export_conversations)
        file_menu.addAction(export_action)

        import_action = QAction("Import Chats 📥", self)
        import_action.triggered.connect(self.import_conversations)
        file_menu.addAction(import_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("Edit ✏️")
        rename_action = QAction("Rename Chat 🏷️", self)
        rename_action.triggered.connect(lambda: self.rename_conversation(self.conversation_list.currentItem()))
        edit_menu.addAction(rename_action)

        delete_action = QAction("Delete Chat 🗑️", self)
        delete_action.triggered.connect(lambda: self.delete_conversation(self.conversation_list.currentRow()))
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menu_bar.addMenu("View 👁️")
        increase_font_action = QAction("Increase Font 🔍+", self)
        increase_font_action.triggered.connect(lambda: self.change_font_size(self.font_size + 1))
        view_menu.addAction(increase_font_action)

        decrease_font_action = QAction("Decrease Font 🔍-", self)
        decrease_font_action.triggered.connect(lambda: self.change_font_size(self.font_size - 1))
        view_menu.addAction(decrease_font_action)

        # Help menu
        help_menu = menu_bar.addMenu("Help ❓")
        about_action = QAction("About 🧠", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        menu_bar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {COLORS['background']};
                color: {COLORS['on_background']};
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
            QMenu {{
                background-color: {COLORS['surface']};
                color: {COLORS['on_surface']};
                border: 1px solid {COLORS['primary']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
            }}
        """)

    def change_ui_scale(self, scale):
        self.ui_scale = scale
        self.setStyleSheet(f"font-size: {int(9 * scale / 100)}pt;")
        # Adjust other UI elements as needed

    def change_theme(self, theme):
        self.current_theme = theme
        if theme == "Dark":
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        elif theme == "Light":
            self.setStyleSheet("")
        # Add more theme options as needed

    def load_plugins(self):
        self.plugins = []
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        if not os.path.exists(plugin_dir):
            logger.warning("Plugins directory not found. Creating an empty one.")
            os.makedirs(plugin_dir)
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py"):
                plugin_name = filename[:-3]
                try:
                    plugin = __import__(f"plugins.{plugin_name}", fromlist=["Plugin"])
                    self.plugins.append(plugin.Plugin(self))
                except ImportError as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")

    def open_settings_dashboard(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec_()

    def show_instructions_dashboard(self):
        dashboard = InstructionsDashboard(self)
        dashboard.exec_()

    def speak_message(self, message):
        try:
            tts = gTTS(text=message, lang='en')
            tts.save("temp_speech.mp3")
            pygame.mixer.init()
            pygame.mixer.music.load("temp_speech.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            os.remove("temp_speech.mp3")
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to generate speech: {str(e)}")

    def setup_toolbar(self):
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(32, 32))

    def setup_workstation_button(self):
        workstation_button = QPushButton("🏢", self)
        workstation_button.setToolTip("Open AI WorkStation Hub")
        workstation_button.setStyleSheet(f"""
            QPushButton {{
                font-size: 24px;
                background-color: transparent;
                border: none;
                padding: 5px;
                color: {COLORS['on_background']};
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: {COLORS['on_primary']};
                border-radius: 15px;
            }}
        """)
        workstation_button.clicked.connect(self.toggle_workstation_hub)
        
        self.toolbar.addWidget(workstation_button)

    def toggle_workstation_hub(self):
        if self.workstation_hub is None or not self.workstation_hub.isVisible():
            self.open_workstation_hub()
        else:
            self.workstation_hub.close()

    def open_workstation_hub(self):
        if self.workstation_hub is None:
            self.workstation_hub = AIWorkStationHub(self)
        
        # מיקום הוורקסטיישן מימין לחלון הראשי
        main_geo = self.geometry()
        self.workstation_hub.setGeometry(
            main_geo.right(),
            main_geo.top(),
            300,  # רוחב התחלתי
            main_geo.height()
        )
        
        self.workstation_hub.show()

    def delete_conversation(self, index):
        if 0 <= index < len(self.conversations):
            del self.conversations[index]
            self.conversation_list.takeItem(index)
            self.chat_stack.removeWidget(self.chat_stack.widget(index))
            if len(self.conversations) == 0:
                self.new_chat()
            elif index == self.current_conversation:
                self.change_conversation(len(self.conversations) - 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AIChat()
    window.show()
    sys.exit(app.exec_())
