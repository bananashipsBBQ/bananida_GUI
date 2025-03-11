from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QProgressBar, QFrame, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
import qtawesome as qta
import os

class InjectionPanel(QWidget):
    injection_started = pyqtSignal(str, int)  # script, pid
    injection_completed = pyqtSignal(bool, str)  # success, message
    injection_stopped = pyqtSignal()  # Signal to stop injection
    
    def __init__(self):
        super().__init__()
        self.current_pid = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status panel
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        
        self.status_icon = QLabel()
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#99aab5').pixmap(16, 16))
        self.status_label = QLabel("No process selected")
        self.status_label.setStyleSheet("color: #99aab5;")
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton(qta.icon('fa5s.folder-open'), "Load Script")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #7289da;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #677bc4;
            }
        """)
        self.load_btn.clicked.connect(self.load_script_file)
        
        # Attach button (for running processes)
        self.attach_btn = QPushButton(qta.icon('fa5s.link'), "Attach")
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #43b581;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3ca374;
            }
            QPushButton:disabled {
                background-color: #2f3136;
                color: #72767d;
            }
        """)
        self.attach_btn.clicked.connect(lambda: self.start_injection(mode="attach"))
        self.attach_btn.setEnabled(False)
        
        # Launch button (for spawning new process)
        self.launch_btn = QPushButton(qta.icon('fa5s.play'), "Launch")
        self.launch_btn.setStyleSheet(self.attach_btn.styleSheet())
        self.launch_btn.clicked.connect(lambda: self.start_injection(mode="launch"))
        self.launch_btn.setEnabled(False)
        
        self.stop_btn = QPushButton(qta.icon('fa5s.stop'), "Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f04747;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d84040;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_injection)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.attach_btn)
        button_layout.addWidget(self.launch_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2f3136;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #7289da;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        
        # Add all components
        layout.addWidget(status_frame)
        layout.addLayout(button_layout)
        layout.addWidget(self.progress_bar)
        
    def set_process(self, device_id, pid):
        """Called when a process is selected"""
        try:
            # Ensure pid is an integer
            if not isinstance(pid, int):
                print(f"Warning: PID is not an integer: {pid} ({type(pid)})")
                pid = int(pid)
                
            if pid <= 0:
                raise ValueError(f"Invalid PID value: {pid}")
                
            self.current_pid = pid
            self.status_label.setText(f"Selected PID: {self.current_pid}")
            self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#43b581').pixmap(16, 16))
            self.attach_btn.setEnabled(True)
            self.launch_btn.setEnabled(True)
            
        except (ValueError, TypeError) as e:
            print(f"Error setting process: {e}")
            self.status_label.setText("Invalid PID")
            self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#f04747').pixmap(16, 16))
            self.attach_btn.setEnabled(False)
            self.launch_btn.setEnabled(False)
        
    def load_script_file(self):
        """Load script from file"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Frida Script",
            "",
            "JavaScript Files (*.js);;All Files (*.*)"
        )
        
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    script_content = f.read()
                self.script_editor.set_script(script_content)
                self.status_label.setText(f"Loaded script: {os.path.basename(file_name)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load script: {str(e)}")
        
    def start_injection(self, mode="attach"):
        """Start the injection process"""
        if not self.current_pid or not isinstance(self.current_pid, int) or self.current_pid <= 0:
            QMessageBox.warning(self, "Error", "Invalid PID!")
            return
            
        script_content = self.script_editor.get_script()
        if not script_content:
            QMessageBox.warning(self, "Error", "No script to inject!")
            return
            
        # Debug output
        print(f"Starting injection - PID: {self.current_pid} ({type(self.current_pid)}), Mode: {mode}")
        
        # Update UI
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#faa61a').pixmap(16, 16))
        self.status_label.setText(f"{'Attaching to' if mode == 'attach' else 'Launching'} process...")
        self.attach_btn.setEnabled(False)
        self.launch_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)
        
        try:
            self.injection_started.emit(script_content, self.current_pid)
        except Exception as e:
            self.injection_failed(str(e))
        
    def injection_succeeded(self):
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#43b581').pixmap(16, 16))
        self.status_label.setText("Injection successful!")
        self.reset_ui()
        QMessageBox.information(self, "Success", "Script injected successfully!")
        
    def injection_failed(self, error):
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#f04747').pixmap(16, 16))
        self.status_label.setText("Injection failed!")
        self.reset_ui()
        QMessageBox.critical(self, "Error", f"Injection failed: {error}")
        
    def reset_ui(self):
        self.attach_btn.setEnabled(True)
        self.launch_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.hide() 
        
    def stop_injection(self):
        """Stop the current injection"""
        self.injection_stopped.emit()
        self.reset_ui()
        self.status_label.setText("Injection stopped")
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#faa61a').pixmap(16, 16))
        