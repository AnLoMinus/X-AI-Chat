import sys
import json
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QCheckBox, QTextEdit, QPushButton, QLabel, QScrollArea,
                             QLineEdit, QFileDialog, QMessageBox, QComboBox, QListWidget, QInputDialog,
                             QSplitter, QFrame)
from PyQt5.QtCore import Qt, QLocale
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

class PromptsGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.languages = self.load_languages()
        self.templates = self.load_templates()
        self.current_language = "Hebrew"  # Default language
        self.initUI()

    def load_languages(self):
        try:
            with open('languages.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"Hebrew": {}, "Russian": {}, "English": {}}

    def load_templates(self):
        templates = {}
        templates_dir = 'templates'
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        for filename in os.listdir(templates_dir):
            if filename.endswith('.json'):
                with open(os.path.join(templates_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for i, template in enumerate(data):
                            templates[f"{filename[:-5]}_{i+1}"] = template
                    else:
                        templates[filename[:-5]] = data
        return templates

    def initUI(self):
        self.setWindowTitle('Prompts Generator v1.2')
        self.setGeometry(100, 100, 1400, 800)
        
        # Set the color palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)

        self.setStyleSheet("""
            QWidget {
                background-color: #353535;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial;
                font-size: 14px;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
            QTextEdit, QLineEdit, QComboBox, QListWidget {
                background-color: #252525;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #0D6EFD;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0B5ED7;
            }
            QPushButton:pressed {
                background-color: #094BBA;
            }
            QScrollArea {
                border: none;
            }
            QSplitter::handle {
                background-color: #555;
            }
            QSplitter::handle:hover {
                background-color: #0D6EFD;
            }
            QComboBox {
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 14px;
                height: 14px;
            }
            QListWidget::item:selected {
                background-color: #0D6EFD;
            }
        """)

        self.main_layout = QHBoxLayout()

        # Create a splitter for the main sections
        self.splitter = QSplitter(Qt.Horizontal)

        # Template sets section
        self.template_sets_widget = QFrame()
        self.template_sets_widget.setFrameShape(QFrame.StyledPanel)
        template_sets_layout = QVBoxLayout(self.template_sets_widget)
        self.template_sets_label = QLabel(self.tr("ready_sets"))
        self.template_sets_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        template_sets_layout.addWidget(self.template_sets_label)

        self.template_sets_list = QListWidget()
        self.template_sets_list.addItems(self.templates.keys())
        self.template_sets_list.itemClicked.connect(self.load_template_set)
        template_sets_layout.addWidget(self.template_sets_list)

        self.splitter.addWidget(self.template_sets_widget)

        # Form section
        self.form_widget = QFrame()
        self.form_widget.setFrameShape(QFrame.StyledPanel)
        form_layout = QVBoxLayout(self.form_widget)
        self.form_label = QLabel(self.tr("form_title"))
        self.form_label.setFont(QFont('Segoe UI', 18, QFont.Bold))
        form_layout.addWidget(self.form_label)

        # Language selection
        form_layout.addWidget(QLabel(self.tr("language")))
        self.language_select = QComboBox()
        self.language_select.addItems(self.languages.keys())
        self.language_select.currentTextChanged.connect(self.change_language)
        form_layout.addWidget(self.language_select)

        # Category
        form_layout.addWidget(QLabel("קטגוריה:"))
        self.category_input = QComboBox()
        self.category_input.addItems(["", "כללי", "טכנולוגיה", "בריאות", "חינוך", "בידור", "פיננסים", "נסיעות", "אוכל", "ספורט", "אורח חיים", "מדע", "אמנות"])
        form_layout.addWidget(self.category_input)

        # Tone
        form_layout.addWidget(QLabel("טון:"))
        self.tone_input = QComboBox()
        self.tone_input.addItems(["", "רשמי", "לא רשמי", "ידידותי", "מקצועי", "הומוריסטי", "רציני", "משכנע", "מעורר השראה", "תמציתי", "תיאורי", "נרטיבי", "טכני"])
        form_layout.addWidget(self.tone_input)

        # Length
        form_layout.addWidget(QLabel("אורך:"))
        self.length_input = QComboBox()
        self.length_input.addItems(["", "קצר", "בינוני", "ארוך", "מאוד ארוך", "משפט אחד", "פסקה", "מפורט", "סיכום", "נקודות", "דיאלוג", "מתווה", "מאמר"])
        form_layout.addWidget(self.length_input)

        # Keywords
        form_layout.addWidget(QLabel("מילות מפתח:"))
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("הכנס מילות מפתח (מופרדות בפסיקים)")
        form_layout.addWidget(self.keywords_input)

        # Include
        form_layout.addWidget(QLabel("כלול:"))
        self.include_input = QListWidget()
        self.include_input.setSelectionMode(QListWidget.MultiSelection)
        include_options = ["דוגמאות", "הסברים", "טיפים", "סטטיסטיקות", "ציטוטים", "מקרים לדוגמה", "הפניות", "תמונות", "סרטונים", "קישורים", "רשימות בדיקה", "סיכומים"]
        self.include_input.addItems(include_options)
        form_layout.addWidget(self.include_input)

        # Format
        form_layout.addWidget(QLabel("פורמט פלט:"))
        self.format_input = QComboBox()
        self.format_input.addItems(["", "טקסט פשוט", "Markdown", "HTML", "JSON", "XML", "CSV", "PDF", "DOCX", "PPTX", "LaTeX", "קובץ טקסט", "תמונה"])
        form_layout.addWidget(self.format_input)

        # Target Audience
        form_layout.addWidget(QLabel("קהל יעד:"))
        self.target_audience_input = QLineEdit()
        self.target_audience_input.setPlaceholderText("הכנס קהל יעד")
        form_layout.addWidget(self.target_audience_input)

        # Context
        form_layout.addWidget(QLabel("הקשר:"))
        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText("הכנס הקשר לפקודה")
        form_layout.addWidget(self.context_input)

        self.splitter.addWidget(self.form_widget)

        # Output section
        self.output_widget = QFrame()
        self.output_widget.setFrameShape(QFrame.StyledPanel)
        output_layout = QVBoxLayout(self.output_widget)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        generate_button = QPushButton("🔮 צור בקשה")
        generate_button.clicked.connect(self.generate_prompt)
        buttons_layout.addWidget(generate_button)

        save_template_button = QPushButton("💾 שמור תבנית")
        save_template_button.clicked.connect(self.save_template)
        buttons_layout.addWidget(save_template_button)

        load_template_button = QPushButton("📂 טען תבנית")
        load_template_button.clicked.connect(self.load_custom_template)
        buttons_layout.addWidget(load_template_button)

        export_button = QPushButton("📤 ייצא בקשה")
        export_button.clicked.connect(self.export_prompt)
        buttons_layout.addWidget(export_button)

        output_layout.addLayout(buttons_layout)

        # Output
        output_label = QLabel("📝 בקשה שנוצרה:")
        output_label.setFont(QFont('Arial', 14, QFont.Bold))
        output_layout.addWidget(output_label)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)

        # Additional buttons
        additional_buttons_layout = QHBoxLayout()
        
        copy_button = QPushButton("העתק תוצאה")
        copy_button.clicked.connect(self.copy_result)
        additional_buttons_layout.addWidget(copy_button)

        clear_button = QPushButton("נקה תוצאה")
        clear_button.clicked.connect(self.clear_result)
        additional_buttons_layout.addWidget(clear_button)

        output_layout.addLayout(additional_buttons_layout)

        self.splitter.addWidget(self.output_widget)

        # Add the splitter to the main layout
        self.main_layout.addWidget(self.splitter)

        self.setLayout(self.main_layout)

        # Initial language setup
        self.change_language(self.current_language)

    def change_language(self, language):
        self.current_language = language
        translations = self.languages[language]
        
        # Update all labels and placeholders with the new language
        self.template_sets_label.setText(self.tr("ready_sets"))
        self.form_label.setText(self.tr("form_title"))
        
        # Update other UI elements...

        # Set layout direction based on language
        if language in ["Hebrew", "Arabic"]:
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

    def tr(self, key):
        return self.languages[self.current_language].get(key, key)

    def load_template_set(self, item):
        template_name = item.text()
        if template_name in self.templates:
            template = self.templates[template_name]
            self.load_template_data(template)

    def load_template_data(self, template):
        self.category_input.setCurrentText(template.get("category", ""))
        self.tone_input.setCurrentText(template.get("tone", ""))
        self.length_input.setCurrentText(template.get("length", ""))
        self.keywords_input.setText(template.get("keywords", ""))
        self.format_input.setCurrentText(template.get("format", ""))
        self.target_audience_input.setText(template.get("target_audience", ""))
        self.context_input.setPlainText(template.get("context", ""))
        
        self.include_input.clearSelection()
        for include in template.get("include", []):
            items = self.include_input.findItems(include, Qt.MatchExactly)
            for item in items:
                item.setSelected(True)

    def generate_prompt(self):
        prompt = {
            "קטגוריה": self.category_input.currentText(),
            "טון": self.tone_input.currentText(),
            "אורך": self.length_input.currentText(),
            "מילות מפתח": self.keywords_input.text(),
            "כלול": [item.text() for item in self.include_input.selectedItems()],
            "פורמט פלט": self.format_input.currentText(),
            "קהל יעד": self.target_audience_input.text(),
            "הקשר": self.context_input.toPlainText()
        }

        result = "בקשה שנוצרה:\n\n"
        for key, value in prompt.items():
            if isinstance(value, list):
                result += f"{key}: {', '.join(value)}\n"
            else:
                result += f"{key}: {value}\n"

        self.output_text.setPlainText(result)

    def save_template(self):
        template = {
            "category": self.category_input.currentText(),
            "tone": self.tone_input.currentText(),
            "length": self.length_input.currentText(),
            "keywords": self.keywords_input.text(),
            "include": [item.text() for item in self.include_input.selectedItems()],
            "format": self.format_input.currentText(),
            "target_audience": self.target_audience_input.text(),
            "context": self.context_input.toPlainText()
        }
        
        template_name, ok = QInputDialog.getText(self, 'שמור תבנית', 'הכנס שם לתבנית:')
        if ok and template_name:
            file_name = f'templates/{template_name}.json'
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            self.templates[template_name] = template
            self.template_sets_list.addItem(template_name)
            QMessageBox.information(self, "הצלחה", "✅ התבנית נשמרה בהצלחה!")

    def load_custom_template(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "טען תבנית", "", "קבצי JSON (*.json)")
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as f:
                template = json.load(f)
            self.load_template_data(template)
            QMessageBox.information(self, "הצלחה", "✅ התבנית נטענה בהצלחה!")

    def export_prompt(self):
        prompt = self.output_text.toPlainText()
        file_name, _ = QFileDialog.getSaveFileName(self, "ייצא בקשה", "", "קבצי טקסט (*.txt)")
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(prompt)
            QMessageBox.information(self, "הצלחה", "✅ הבקשה יוצאה בהצלחה!")

    def copy_result(self):
        self.output_text.selectAll()
        self.output_text.copy()
        QMessageBox.information(self, "הצלחה", "✅ התוצאה הועתקה ללוח!")

    def clear_result(self):
        self.output_text.clear()
        QMessageBox.information(self, "הצלחה", "✅ התוצאה נוקתה!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PromptsGenerator()
    ex.show()
    sys.exit(app.exec_())
