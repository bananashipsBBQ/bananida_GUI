from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QComboBox, QPushButton, QLabel)
import frida
import subprocess

class ProcessPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_device_id = None
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.process_combo = QComboBox()
        self.refresh_button = QPushButton("Refresh Processes")
        
        layout.addWidget(QLabel("Select Process:"))
        layout.addWidget(self.process_combo)
        layout.addWidget(self.refresh_button)
        
        self.refresh_button.clicked.connect(self.refresh_processes)
        
    def update_device(self, device_id):
        self.current_device_id = device_id
        self.refresh_processes()
        
    def refresh_processes(self):
        if not self.current_device_id:
            return
            
        self.process_combo.clear()
        try:
            device = frida.get_device(self.current_device_id)
            if device.type == 'local':
                processes = device.enumerate_processes()
                for process in processes:
                    self.process_combo.addItem(
                        f"{process.name} (PID: {process.pid})", 
                        process.pid
                    )
            else:
                # For ADB devices
                output = subprocess.check_output(
                    ['adb', '-s', self.current_device_id, 'shell', 'ps'],
                    text=True
                ).strip().split('\n')
                
                for line in output[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 9:
                        pid = parts[1]
                        process_name = parts[-1]
                        self.process_combo.addItem(
                            f"{process_name} (PID: {pid})", 
                            pid
                        )
        except Exception as e:
            print(f"Error refreshing processes: {str(e)}") 