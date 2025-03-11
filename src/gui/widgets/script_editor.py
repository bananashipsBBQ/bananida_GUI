from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class ScriptEditorPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Enter your Frida script here...")
        
        # Set default script template
        self.editor.setPlainText('''Java.perform(function() {
    console.log("Script loaded!");
});''')
        
        layout.addWidget(self.editor)
        
    def get_script(self):
        return self.editor.toPlainText()
        
    def set_script(self, script):
        self.editor.setPlainText(script) 