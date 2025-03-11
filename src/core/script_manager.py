from PyQt5.QtCore import QObject, pyqtSignal
from pygments import highlight
from pygments.lexers import JavascriptLexer
from pygments.formatters import HtmlFormatter
from cryptography.fernet import Fernet
import json
import os

class ScriptManager(QObject):
    script_loaded = pyqtSignal(str, str)  # name, content
    script_saved = pyqtSignal(str)  # name
    
    def __init__(self):
        super().__init__()
        self.scripts_dir = os.path.join(os.path.expanduser('~'), '.frida_gui', 'scripts')
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self._ensure_dirs()
        
    def _ensure_dirs(self):
        os.makedirs(self.scripts_dir, exist_ok=True)
        
    def save_script(self, name, content, encrypt=False):
        """Save script with optional encryption"""
        script_path = os.path.join(self.scripts_dir, f"{name}.js")
        metadata_path = f"{script_path}.meta"
        
        if encrypt:
            content = self.cipher_suite.encrypt(content.encode()).decode()
            
        with open(script_path, 'w') as f:
            f.write(content)
            
        metadata = {
            'name': name,
            'encrypted': encrypt,
            'tags': [],
            'description': '',
            'version': '1.0'
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
            
        self.script_saved.emit(name)
        
    def load_script(self, name):
        """Load script and handle decryption if needed"""
        script_path = os.path.join(self.scripts_dir, f"{name}.js")
        metadata_path = f"{script_path}.meta"
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            with open(script_path, 'r') as f:
                content = f.read()
                
            if metadata.get('encrypted', False):
                content = self.cipher_suite.decrypt(content.encode()).decode()
                
            self.script_loaded.emit(name, content)
            return content
        except Exception as e:
            print(f"Error loading script: {str(e)}")
            return None
            
    def get_highlighted_script(self, content):
        """Return HTML-formatted highlighted script"""
        return highlight(
            content,
            JavascriptLexer(),
            HtmlFormatter(style='monokai')
        ) 