from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class OutputPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("Output will appear here...")
        
        layout.addWidget(self.output_area)
        
    def append_output(self, text):
        self.output_area.append(text)
        
    def clear_output(self):
        self.output_area.clear() 