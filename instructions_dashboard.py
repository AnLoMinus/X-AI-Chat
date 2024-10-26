from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QInputDialog

class InstructionsDashboard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Instructions Dashboard")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.instructions_list = QListWidget()
        layout.addWidget(self.instructions_list)
        
        add_button = QPushButton("Add Instruction")
        add_button.clicked.connect(self.add_instruction)
        layout.addWidget(add_button)
        
        self.load_instructions()

    def load_instructions(self):
        for category, data in self.parent.preset_instructions.items():
            for instruction in data['instructions']:
                self.instructions_list.addItem(f"{category}: {instruction}")

    def add_instruction(self):
        category, ok = QInputDialog.getText(self, "Add Instruction", "Enter category:")
        if ok and category:
            instruction, ok = QInputDialog.getText(self, "Add Instruction", "Enter instruction:")
            if ok and instruction:
                if category not in self.parent.preset_instructions:
                    self.parent.preset_instructions[category] = {'instructions': []}
                self.parent.preset_instructions[category]['instructions'].append(instruction)
                self.parent.save_preset_instructions()
                self.instructions_list.addItem(f"{category}: {instruction}")
