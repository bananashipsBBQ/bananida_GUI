from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                           QPushButton, QLabel, QFrame, QLineEdit, QMessageBox,
                           QApplication)
from PyQt5.QtCore import pyqtSignal, QSize
import frida
import subprocess
import qtawesome as qta
import psutil
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.android_helper import AndroidHelper

class DeviceSelector(QWidget):
    process_selected = pyqtSignal(str, int)  # device_id, pid
    
    def __init__(self):
        super().__init__()
        self.current_device = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main frame
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
            QComboBox {
                background-color: #36393f;
                border: none;
                border-radius: 4px;
                padding: 8px;
                color: white;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox::down-arrow {
                image: url(down-arrow.png);
            }
        """)
        
        frame_layout = QVBoxLayout(frame)
        
        # Device selection
        device_layout = QHBoxLayout()
        
        self.device_combo = QComboBox()
        self.device_combo.setPlaceholderText("Select Device...")
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        
        refresh_btn = QPushButton(qta.icon('fa5s.sync'), "")
        refresh_btn.setToolTip("Refresh Devices")
        refresh_btn.clicked.connect(self.refresh_devices)
        
        device_layout.addWidget(QLabel("Device:"))
        device_layout.addWidget(self.device_combo, 1)
        device_layout.addWidget(refresh_btn)
        
        # Process selection
        process_layout = QHBoxLayout()
        
        # Add filter input
        self.process_filter = QLineEdit()
        self.process_filter.setPlaceholderText("Filter processes...")
        self.process_filter.textChanged.connect(self.filter_processes)
        
        self.process_combo = QComboBox()
        self.process_combo.setPlaceholderText("Select Process...")
        self.process_combo.currentIndexChanged.connect(self.on_process_changed)
        self.process_combo.setMaxVisibleItems(20)  # Show more items in dropdown
        self.process_combo.setStyleSheet("""
            QComboBox QListView {
                min-width: 300px;
            }
        """)
        
        # Add refresh button
        refresh_btn = QPushButton(qta.icon('fa5s.sync'), "")
        refresh_btn.setToolTip("Refresh Processes")
        refresh_btn.clicked.connect(self.refresh_processes)
        
        process_layout.addWidget(QLabel("Process:"))
        process_layout.addWidget(self.process_filter)
        process_layout.addWidget(self.process_combo, 1)
        process_layout.addWidget(refresh_btn)
        
        # Add layouts to frame
        frame_layout.addLayout(device_layout)
        frame_layout.addLayout(process_layout)
        
        # Add frame to main layout
        layout.addWidget(frame)
        
        # Initial device scan
        self.refresh_devices()
        
    def refresh_devices(self):
        self.device_combo.clear()
        try:
            devices = frida.enumerate_devices()
            for device in devices:
                if device.type == 'usb':
                    self.device_combo.addItem(f"📱 {device.name} (USB)", device.id)
                elif device.type == 'remote':
                    self.device_combo.addItem(f"🌐 {device.name} (Remote)", device.id)
                elif device.type == 'local':
                    self.device_combo.addItem(f"💻 {device.name} (Local)", device.id)
        except Exception as e:
            print(f"Error enumerating devices: {e}")
            
    def on_device_changed(self, index):
        if index < 0:
            return
            
        device_id = self.device_combo.currentData()
        self.current_device = device_id
        self.refresh_processes()
        
    def refresh_processes(self):
        self.process_combo.clear()
        if not self.current_device:
            return
        
        try:
            device = frida.get_device(self.current_device)
            
            if device.type == 'usb':
                # Show loading message
                self.process_combo.addItem("Checking device status...")
                QApplication.processEvents()
                
                # Check frida-server for Android devices
                if not AndroidHelper.is_device_connected(self.current_device):
                    raise Exception(f"Device {self.current_device} not connected")
                    
                if not AndroidHelper.is_frida_running(self.current_device):
                    # Show installing message
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setText("Installing Frida Server")
                    msg.setInformativeText("Please wait while Frida server is being installed on the device...")
                    msg.setWindowTitle("Installing Frida")
                    msg.show()
                    QApplication.processEvents()
                    
                    success = AndroidHelper.start_frida_server(self.current_device)
                    msg.close()
                    
                    if not success:
                        error_msg = QMessageBox()
                        error_msg.setIcon(QMessageBox.Critical)
                        error_msg.setText("Frida Installation Failed")
                        error_msg.setInformativeText("Failed to install and start Frida server on the device. Please check your device connection and try again.")
                        error_msg.setWindowTitle("Installation Error")
                        error_msg.exec_()
                        return
                    
                    # Show success message
                    success_msg = QMessageBox()
                    success_msg.setIcon(QMessageBox.Information)
                    success_msg.setText("Frida Server Installed")
                    success_msg.setInformativeText("Frida server has been successfully installed and started on the device.")
                    success_msg.setWindowTitle("Installation Complete")
                    success_msg.exec_()
                
                # Clear loading message and get processes
                self.process_combo.clear()
                
                try:
                    # Get Android processes using frida-ps
                    processes = device.enumerate_processes()
                    for process in processes:
                        if process.pid > 0:
                            name = process.name
                            pid = process.pid
                            # Only add user apps (filter out system processes)
                            if '.' in name:  # Simple check for app package names
                                self.process_combo.addItem(
                                    f"{name} (PID: {pid})",
                                    pid
                                )
                except Exception as e:
                    print(f"Error getting processes: {str(e)}")
                    raise Exception("Failed to get process list from device")
                    
            elif device.type == 'local':
                # Handle local device processes
                processes = device.enumerate_processes()
                for process in processes:
                    if process.pid > 0:
                        self.process_combo.addItem(
                            f"{process.name} (PID: {process.pid})",
                            process.pid
                        )
                    
        except Exception as e:
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("Error")
            error_msg.setInformativeText(f"Failed to refresh processes: {str(e)}")
            error_msg.setWindowTitle("Process List Error")
            error_msg.exec_()
            
            self.process_combo.clear()
            self.process_combo.addItem("Error loading processes")
        
    def filter_processes(self, text):
        """Filter processes in combo box"""
        text = text.lower()
        self.process_combo.clear()
        
        try:
            device = frida.get_device(self.current_device)
            
            if device.type == 'local':
                processes = device.enumerate_processes()
                for process in processes:
                    try:
                        if process.pid > 0 and process.name and text in process.name.lower():
                            pid = int(process.pid)
                            name = str(process.name)
                            self.process_combo.addItem(
                                f"{name} (PID: {pid})",
                                pid
                            )
                    except (ValueError, AttributeError) as e:
                        continue
            else:
                # For Android devices
                processes = device.enumerate_processes()
                for process in processes:
                    if process.pid > 0 and text in process.name.lower():
                        if '.' in process.name:  # Only show Android apps
                            self.process_combo.addItem(
                                f"{process.name} (PID: {process.pid})",
                                process.pid
                            )
                    
        except Exception as e:
            print(f"Error filtering processes: {e}")
            
    def on_process_changed(self, index):
        if index < 0:
            return
        
        try:
            device_id = self.device_combo.currentData()
            pid = self.process_combo.currentData()
            
            # Debug output
            print(f"Process changed - device_id: {device_id}, pid: {pid} ({type(pid)})")
            
            # Only emit if we have valid data
            if device_id and isinstance(pid, int) and pid > 0:
                self.process_selected.emit(device_id, pid)
            else:
                print(f"Skipping invalid process selection - device_id: {device_id}, pid: {pid}")
                
        except Exception as e:
            print(f"Error in process selection: {e}")

    def get_selected_process_info(self):
        """Get info about selected process"""
        try:
            index = self.process_combo.currentIndex()
            if index >= 0:
                device_id = self.device_combo.currentData()
                pid = self.process_combo.currentData()
                name = self.process_combo.currentText().split('(')[0].strip()
                
                # Debug output
                print(f"Selected process - PID: {pid} ({type(pid)}), Name: {name}")
                
                if device_id and pid:
                    return {
                        'device_id': device_id,
                        'pid': pid,
                        'name': name
                    }
            return None
        except Exception as e:
            print(f"Error getting process info: {e}")
            return None

    def select_device(self, device_id):
        """Select a device by its ID"""
        index = self.device_combo.findData(device_id)
        if index >= 0:
            self.device_combo.setCurrentIndex(index)

    def select_process(self, pid):
        """Select a process by its PID"""
        for i in range(self.process_combo.count()):
            if str(pid) in self.process_combo.itemText(i):
                self.process_combo.setCurrentIndex(i)
                break

    def cleanup(self):
        """Clean up resources"""
        self.process_combo.clear()
        self.device_combo.clear()
        self.current_device = None