from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QComboBox, QPushButton, QLabel)
from PyQt5.QtCore import pyqtSignal
import frida

class DevicePanel(QWidget):
    device_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Device selection combo box
        self.device_combo = QComboBox()
        self.scan_button = QPushButton("Scan Devices")
        
        layout.addWidget(QLabel("Select Device:"))
        layout.addWidget(self.device_combo)
        layout.addWidget(self.scan_button)
        
        # Connect signals
        self.scan_button.clicked.connect(self.scan_devices)
        self.device_combo.currentIndexChanged.connect(self._on_device_selected)
        
        # Initial scan
        self.scan_devices()
        
    def scan_devices(self):
        try:
            self.device_combo.clear()
            devices = frida.enumerate_devices()
            for device in devices:
                if device.type in ['usb', 'remote']:
                    self.device_combo.addItem(f"{device.name} (ADB - {device.type})", device.id)
                elif device.type == 'local':
                    self.device_combo.addItem(f"{device.name} (Local)", device.id)
        except Exception as e:
            print(f"Error scanning devices: {str(e)}")
            
    def _on_device_selected(self):
        device_id = self.device_combo.currentData()
        if device_id:
            self.device_selected.emit(device_id) 