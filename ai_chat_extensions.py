import sys
import os
import json
import logging
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
import psutil
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
import tempfile

logger = logging.getLogger('AIChat')

class AIChatExtensions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.setup_extensions()

    def setup_extensions(self):
        self.setup_advanced_ui()
        self.setup_advanced_features()
        self.setup_plugins()

    def setup_advanced_ui(self):
        self.main_window.setWindowTitle("AI Chat v1.0.0 🚀")
        self.setup_advanced_toolbar()
        self.setup_advanced_status_bar()
        self.setup_advanced_menu_bar()

    def setup_advanced_toolbar(self):
        self.main_window.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2C3E50;
                border: none;
                spacing: 10px;
            }
            QToolButton {
                background-color: #34495E;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #4E6D8C;
            }
        """)
        
        # הוספת כפתורים מתקדמים לסרגל הכלים
        actions = [
            ("🔍", "Advanced Search", self.advanced_search),
            ("📊", "Analytics Dashboard", self.show_analytics_dashboard),
            ("🔧", "Advanced Settings", self.show_advanced_settings),
            ("🔌", "Plugin Manager", self.show_plugin_manager)
        ]
        
        for icon, tooltip, func in actions:
            action = QAction(self.main_window)
            action.setText(icon)  # שימוש ב-setText במקום להעביר את האייקון כפרמטר
            action.setToolTip(tooltip)
            action.triggered.connect(func)
            self.main_window.toolbar.addAction(action)

    def setup_advanced_status_bar(self):
        # הוספת מידע נוסף לשורת המצב
        self.cpu_usage_label = QLabel()
        self.memory_usage_label = QLabel()
        self.main_window.statusBar().addPermanentWidget(self.cpu_usage_label)
        self.main_window.statusBar().addPermanentWidget(self.memory_usage_label)
        
        # עדכון מידע על שימוש במשאבים
        self.resource_timer = QTimer(self.main_window)
        self.resource_timer.timeout.connect(self.update_resource_usage)
        self.resource_timer.start(5000)  # עדכון כל 5 שניות

    def setup_advanced_menu_bar(self):
        # הוספת תפריטים מתקדמים
        advanced_menu = self.main_window.menuBar().addMenu("Advanced 🔬")
        
        actions = [
            ("Advanced Search 🔍", self.advanced_search),
            ("Analytics Dashboard 📊", self.show_analytics_dashboard),
            ("Plugin Manager 🔌", self.show_plugin_manager),
            ("Export Chat as PDF 📄", self.export_chat_as_pdf),
            ("Batch Process Chats 🔄", self.batch_process_chats)
        ]
        
        for name, func in actions:
            action = QAction(name, self.main_window)
            action.triggered.connect(func)
            advanced_menu.addAction(action)

    def setup_advanced_features(self):
        # הוספת תכונות מתקדמות
        self.setup_voice_commands()
        self.setup_auto_summarization()
        self.setup_advanced_search()

    def setup_plugins(self):
        self.plugin_manager = PluginManager(self.main_window)
        self.plugin_manager.load_plugins()

    def advanced_search(self):
        search_dialog = AdvancedSearchDialog(self.main_window)
        if search_dialog.exec_():
            search_params = search_dialog.get_search_params()
            results = self.perform_advanced_search(search_params)
            self.show_search_results(results)

    def show_analytics_dashboard(self):
        # יצירת לוח בקרה לניתוח נתונים
        dashboard = AnalyticsDashboard(self.main_window)
        dashboard.show()

    def show_advanced_settings(self):
        # הצגת הגדרות מתקדמות
        settings_dialog = AdvancedSettingsDialog(self.main_window)
        settings_dialog.exec_()

    def show_plugin_manager(self):
        # הצגת מנהל התוספים
        self.plugin_manager.show_manager_dialog()

    def update_resource_usage(self):
        # עדכון מידע על שימוש במשאבים
        cpu_usage = self.get_cpu_usage()
        memory_usage = self.get_memory_usage()
        self.cpu_usage_label.setText(f"CPU: {cpu_usage}%")
        self.memory_usage_label.setText(f"Memory: {memory_usage}%")

    def setup_voice_commands(self):
        # הגדרת פקודות קוליות
        self.voice_command_recognizer = VoiceCommandRecognizer(self.main_window)
        self.main_window.voice_command_action = QAction("🎤", self.main_window)
        self.main_window.voice_command_action.setToolTip("Voice Commands")
        self.main_window.voice_command_action.triggered.connect(self.voice_command_recognizer.start_listening)
        self.main_window.toolbar.addAction(self.main_window.voice_command_action)

    def setup_auto_summarization(self):
        # הגדרת סיכום אוטומטי של שיחות
        self.auto_summarizer = AutoSummarizer(self.main_window)
        self.main_window.auto_summarize_action = QAction("📝", self.main_window)
        self.main_window.auto_summarize_action.setToolTip("Auto Summarize")
        self.main_window.auto_summarize_action.triggered.connect(self.auto_summarizer.summarize_current_chat)
        self.main_window.toolbar.addAction(self.main_window.auto_summarize_action)

    def setup_advanced_search(self):
        # הגדרת חיפוש מתקדם
        self.advanced_searcher = AdvancedSearcher(self.main_window)
        self.main_window.advanced_search_action = QAction("🔍", self.main_window)
        self.main_window.advanced_search_action.setToolTip("Advanced Search")
        self.main_window.advanced_search_action.triggered.connect(self.advanced_searcher.show_search_dialog)
        self.main_window.toolbar.addAction(self.main_window.advanced_search_action)

    def export_chat_as_pdf(self):
        # ייצוא השיחה הנוכחית כקובץ PDF
        exporter = PDFExporter(self.main_window)
        exporter.export_current_chat()

    def batch_process_chats(self):
        # עיבוד אצווה של שיחות
        processor = BatchProcessor(self.main_window)
        processor.process_chats()

    def get_cpu_usage(self):
        return psutil.cpu_percent()

    def get_memory_usage(self):
        return psutil.virtual_memory().percent

    def perform_advanced_search(self, search_params):
        results = []
        keyword = search_params['keyword'].lower()
        search_date = QDate.fromString(search_params['date'], "yyyy-MM-dd")
        
        for conv in self.main_window.conversations:
            for msg, is_user, model, tokens in conv.messages:  # עדכון ל-4 ערכים
                msg_date = QDateTime.fromString(msg[4], "yyyy-MM-dd HH:mm:ss").date()  # שימוש ב-msg[4] לתאריך
                if keyword in msg.lower() and msg_date >= search_date:
                    results.append((conv.name, msg, msg[4]))  # שימוש ב-msg[4] לתאריך
        
        return results

    def show_search_results(self, results):
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("תוצאות חיפוש")
        layout = QVBoxLayout(dialog)
        
        result_list = QListWidget()
        for conv_name, msg, timestamp in results:
            item = QListWidgetItem(f"{conv_name} - {timestamp}: {msg[:50]}...")
            result_list.addItem(item)
        
        layout.addWidget(result_list)
        
        close_button = QPushButton("סגור")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec_()

class AdvancedSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("חיפוש מתקדם")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("הכנס מילות מפתח לחיפוש")
        layout.addWidget(self.keyword_input)
        
        self.date_range = QDateEdit()
        self.date_range.setCalendarPopup(True)
        layout.addWidget(self.date_range)
        
        self.search_button = QPushButton("חפש")
        self.search_button.clicked.connect(self.accept)
        layout.addWidget(self.search_button)

    def get_search_params(self):
        return {
            "keyword": self.keyword_input.text(),
            "date": self.date_range.date().toString("yyyy-MM-dd")
        }

class PluginManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.plugins = []

    def load_plugins(self):
        # טעינת תוספים
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py"):
                plugin_name = filename[:-3]
                try:
                    plugin = __import__(f"plugins.{plugin_name}", fromlist=["Plugin"])
                    self.plugins.append(plugin.Plugin(self.main_window))
                except ImportError as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")

    def show_manager_dialog(self):
        # הצגת חלון ניהול התוספים
        dialog = PluginManagerDialog(self.main_window, self.plugins)
        dialog.exec_()

class VoiceCommandRecognizer:
    def __init__(self, main_window):
        self.main_window = main_window

    def start_listening(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.main_window.statusBar().showMessage("Adjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=1)
                self.main_window.statusBar().showMessage("Listening... Speak now.")
                audio = r.listen(source, timeout=10, phrase_time_limit=10)
                self.main_window.statusBar().showMessage("Processing speech...")

            text = r.recognize_google(audio, language='en-US')
            self.main_window.input_field.append(text)
            self.main_window.statusBar().showMessage("Speech recognized")
            logger.info(f"Speech recognized: {text}")
        except sr.WaitTimeoutError:
            self.main_window.statusBar().showMessage("No speech detected")
            QMessageBox.warning(self.main_window, "Error", "No speech detected. Please try again.")
            logger.warning("No speech detected during voice input")
        except sr.UnknownValueError:
            self.main_window.statusBar().showMessage("Could not understand audio")
            QMessageBox.warning(self.main_window, "Error", "Could not understand audio. Please try again.")
            logger.warning("Speech recognition failed: Could not understand audio")
        except sr.RequestError as e:
            self.main_window.statusBar().showMessage(f"Could not request results; {e}")
            QMessageBox.warning(self.main_window, "Error", f"Failed to process speech: {str(e)}")
            logger.error(f"Speech recognition request failed: {str(e)}")
        except Exception as e:
            self.main_window.statusBar().showMessage(f"An error occurred: {e}")
            QMessageBox.warning(self.main_window, "Error", f"An unexpected error occurred: {str(e)}")
            logger.error(f"Unexpected error during speech recognition: {str(e)}")

class AutoSummarizer:
    def __init__(self, main_window):
        self.main_window = main_window

    def summarize_current_chat(self):
        # סיכום השיחה הנוכחית
        pass

class AdvancedSearcher:
    def __init__(self, main_window):
        self.main_window = main_window

    def show_search_dialog(self):
        # הצגת חלון חיפוש מתקדם
        pass

class PDFExporter:
    def __init__(self, main_window):
        self.main_window = main_window

    def export_current_chat(self):
        if not self.main_window.conversations:
            QMessageBox.warning(self.main_window, "שגיאה", "אין שיחה להמרה ל-PDF")
            return
        
        current_conv = self.main_window.conversations[self.main_window.current_conversation]
        
        html_content = f"<h1>{current_conv.name}</h1>"
        for msg, is_user, model, tokens, timestamp in current_conv.messages:
            sender = "משתמש" if is_user else model
            html_content += f"<p><strong>{sender} ({timestamp}):</strong> {msg}</p>"
        
        # יצירת קובץ HTML זמני
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        # יצירת מסמך PDF
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(f"{current_conv.name}.pdf")
        
        web_view = QWebEngineView()
        web_view.load(QUrl.fromLocalFile(temp_file_path))
        
        def handle_print():
            web_view.page().print(printer, lambda success: None)
            os.unlink(temp_file_path)  # מחיקת הקובץ הזמני
        
        web_view.loadFinished.connect(handle_print)

class BatchProcessor:
    def __init__(self, main_window):
        self.main_window = main_window

    def process_chats(self):
        options = ["ייצוא לPDF", "ניתוח רגשות", "זיהוי נושאים"]
        choice, ok = QInputDialog.getItem(self.main_window, "עיבוד אצווה", 
                                          "בחר פעולה לביצוע על כל השיחות:", options, 0, False)
        if ok and choice:
            if choice == "ייצוא לPDF":
                self.export_all_to_pdf()
            elif choice == "ניתוח רגשות":
                self.analyze_sentiments()
            elif choice == "זיהוי נושאים":
                self.identify_topics()

    def export_all_to_pdf(self):
        exporter = PDFExporter(self.main_window)
        for conv in self.main_window.conversations:
            # כאן נצטרך להתאים את הלוגיקה של הייצוא לPDF כך שתעבוד על שיחה ספציפית
            pass

    def analyze_sentiments(self):
        # כאן יש להוסיף קוד לניתוח רגשות של כל השיחות
        pass

    def identify_topics(self):
        # כאן יש להוסיף קוד לזיהוי נושאים בכל השיחות
        pass

class AnalyticsDashboard(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("לוח בקרה אנליטי")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # גרף עוגה לשימוש במודלים
        pie_chart = self.create_model_usage_chart()
        layout.addWidget(pie_chart)
        
        # גרף עמודות למספר ההודעות בכל שיחה
        bar_chart = self.create_message_count_chart()
        layout.addWidget(bar_chart)
        
        close_button = QPushButton("סגור")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def create_model_usage_chart(self):
        series = QPieSeries()
        model_usage = {}
        for conv in self.main_window.conversations:
            for _, _, model, _ in conv.messages:  # עדכון ל-4 ערכים
                model_usage[model] = model_usage.get(model, 0) + 1
        
        for model, count in model_usage.items():
            series.append(model, count)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("שימוש במודלים")
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view

    def create_message_count_chart(self):
        set0 = QBarSet("מספר הודעות")
        categories = []
        
        for conv in self.main_window.conversations:
            set0.append(len(conv.messages))
            categories.append(conv.name)
        
        series = QBarSeries()
        series.append(set0)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("מספר הודעות בכל שיחה")
        
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        return chart_view

class AdvancedSettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("הגדרות מתקדמות")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # הגדרות נוספות כאן
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ברירת מחדל", "כהה", "בהיר"])
        layout.addWidget(QLabel("ערכת נושא:"))
        layout.addWidget(self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.main_window.font_size)
        layout.addWidget(QLabel("גודל גופן:"))
        layout.addWidget(self.font_size_spin)
        
        save_button = QPushButton("שמור")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

    def save_settings(self):
        # שמירת ההגדרות
        theme = self.theme_combo.currentText()
        font_size = self.font_size_spin.value()
        
        # עדכון ההגדרות במחלקה הראשית
        self.main_window.change_theme(theme)
        self.main_window.change_font_size(font_size)
        
        self.accept()

class PluginManagerDialog(QDialog):
    def __init__(self, main_window, plugins):
        super().__init__(main_window)
        self.setWindowTitle("מנהל תוספים")
        self.plugins = plugins
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        plugin_list = QListWidget()
        for plugin in self.plugins:
            plugin_list.addItem(plugin.__class__.__name__)
        layout.addWidget(plugin_list)
        
        close_button = QPushButton("סגור")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

def initialize_extensions(main_window):
    return AIChatExtensions(main_window)
