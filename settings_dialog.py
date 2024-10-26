from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Settings Dashboard")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # UI Scale
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("UI Scale:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["100%", "125%", "150%", "200%"])
        self.scale_combo.setCurrentText(f"{self.parent.ui_scale}%")
        self.scale_combo.currentTextChanged.connect(self.change_scale)
        scale_layout.addWidget(self.scale_combo)
        layout.addLayout(scale_layout)

        # Theme
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark", "Light"])
        self.theme_combo.setCurrentText(self.parent.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Plugin settings
        for plugin in self.parent.plugins:
            plugin_widget = plugin.get_settings_widget()
            if plugin_widget:
                layout.addWidget(plugin_widget)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def change_scale(self, scale):
        self.parent.change_ui_scale(int(scale[:-1]))

    def change_theme(self, theme):
        self.parent.change_theme(theme)
