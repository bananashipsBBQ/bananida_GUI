from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                           QMenu, QAction, QComboBox, QCheckBox, QFrame,
                           QHeaderView, QStyle, QStyledItemDelegate, QToolButton, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QColor, QFont, QIcon
import psutil
import frida
import re
import qtawesome as qta
from datetime import datetime
import subprocess

class ProcessInfoDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.column() in [2, 3]:  # CPU and Memory columns
            value = float(index.data().replace('%', '').replace('MB', ''))
            if value > 80:
                option.backgroundBrush = QColor('#f04747')
            elif value > 50:
                option.backgroundBrush = QColor('#faa61a')
        super().paint(painter, option, index)

class ProcessMonitor(QWidget):
    def __init__(self, main_window=None):
        QWidget.__init__(self)
        self.processes = {}
        self.current_device = None
        self.main_window = main_window
        self.setup_ui()
        self.start_monitoring()
        
    def start_monitoring(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_processes)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def stop_monitoring(self):
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Device selection
        device_frame = QFrame()
        device_frame.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        device_layout = QHBoxLayout(device_frame)
        
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        
        refresh_devices_btn = QPushButton(qta.icon('fa5s.sync'), "Refresh Devices")
        refresh_devices_btn.clicked.connect(self.refresh_devices)
        
        device_layout.addWidget(QLabel("Device:"))
        device_layout.addWidget(self.device_combo)
        device_layout.addWidget(refresh_devices_btn)
        
        # Search and Filter Bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Process search with regex toggle
        search_container = QFrame()
        search_layout = QHBoxLayout(search_container)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter processes (supports regex)")
        self.search_input.textChanged.connect(self.apply_filters)
        
        self.regex_check = QCheckBox("Regex")
        self.regex_check.toggled.connect(self.apply_filters)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.regex_check)
        
        # Advanced filters
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['All', 'User', 'System', 'Android Apps', 'High CPU', 'High Memory'])
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        
        filter_layout.addWidget(search_container)
        filter_layout.addWidget(self.filter_combo)
        
        # Process Table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory", "Status", "User", "Started", "Command Line"
        ])
        
        # Context menu
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton(qta.icon('fa5s.sync'), "Refresh")
        self.refresh_btn.clicked.connect(self.refresh_processes)
        
        self.kill_btn = QPushButton(qta.icon('fa5s.stop'), "Kill")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        
        self.inject_btn = QPushButton(qta.icon('fa5s.syringe'), "Open in Injector")
        self.inject_btn.clicked.connect(self.open_in_injector_clicked)
        
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.kill_btn)
        action_layout.addWidget(self.inject_btn)
        action_layout.addStretch()
        
        # Add all components
        layout.addWidget(device_frame)
        layout.addWidget(filter_frame)
        layout.addWidget(self.process_table)
        layout.addLayout(action_layout)
        
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
        if index >= 0:
            self.current_device = self.device_combo.currentData()
            self.refresh_processes()
            
    def show_context_menu(self, position):
        menu = QMenu()
        
        kill_action = QAction("Kill Process", self)
        kill_action.triggered.connect(self.kill_selected_process)
        
        inject_action = QAction("Open in Injector", self)
        inject_action.triggered.connect(self.open_in_injector_clicked)
        
        details_action = QAction("Process Details", self)
        details_action.triggered.connect(self.show_process_details)
        
        menu.addAction(kill_action)
        menu.addAction(inject_action)
        menu.addAction(details_action)
        menu.exec_(self.process_table.mapToGlobal(position))
        
    def open_in_injector_clicked(self):
        """Handle click on 'Open in Injector' button"""
        if not self.main_window:
            return
            
        selected = self.process_table.selectedItems()
        if selected:
            row = selected[0].row()
            pid = int(self.process_table.item(row, 0).text())
            if self.current_device:
                self.main_window.open_in_injector(self.current_device, pid)
            else:
                QMessageBox.warning(self, "Error", "No device selected!")
        
    def refresh_processes(self):
        self.process_table.setRowCount(0)
        if not self.current_device:
            return
        
        try:
            device = frida.get_device(self.current_device)
            
            if device.type == 'local':
                # For local processes, use psutil for more reliable info
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'username', 'create_time', 'cmdline']):
                    try:
                        row = self.process_table.rowCount()
                        self.process_table.insertRow(row)
                        
                        # Get process info
                        pid = proc.pid
                        name = proc.name()
                        cpu = proc.cpu_percent()
                        memory = proc.memory_info().rss / 1024 / 1024  # Convert to MB
                        status = proc.status()
                        user = proc.username()
                        started = datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S')
                        cmdline = ' '.join(proc.cmdline())
                        
                        # Create items
                        items = [
                            QTableWidgetItem(str(pid)),
                            QTableWidgetItem(name),
                            QTableWidgetItem(f"{cpu:.1f}%"),
                            QTableWidgetItem(f"{memory:.1f} MB"),
                            QTableWidgetItem(status),
                            QTableWidgetItem(user),
                            QTableWidgetItem(started),
                            QTableWidgetItem(cmdline)
                        ]
                        
                        # Set alignment
                        items[0].setTextAlignment(Qt.AlignCenter)
                        items[2].setTextAlignment(Qt.AlignCenter)
                        items[3].setTextAlignment(Qt.AlignCenter)
                        items[4].setTextAlignment(Qt.AlignCenter)
                        
                        # Add items to row
                        for col, item in enumerate(items):
                            self.process_table.setItem(row, col, item)
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    
            else:
                # For ADB devices
                try:
                    adb_output = subprocess.check_output(
                        ['adb', '-s', self.current_device, 'shell', 'ps'],
                        text=True
                    ).strip().split('\n')
                    
                    for line in adb_output[1:]:  # Skip header
                        parts = line.split()
                        if len(parts) >= 9:
                            row = self.process_table.rowCount()
                            self.process_table.insertRow(row)
                            
                            pid = parts[1]
                            name = parts[-1]
                            
                            items = [
                                QTableWidgetItem(pid),
                                QTableWidgetItem(name),
                                QTableWidgetItem("N/A"),
                                QTableWidgetItem("N/A"),
                                QTableWidgetItem(parts[7]),
                                QTableWidgetItem(parts[0]),
                                QTableWidgetItem("N/A"),
                                QTableWidgetItem("N/A")
                            ]
                            
                            for col, item in enumerate(items):
                                self.process_table.setItem(row, col, item)
                                
                except subprocess.CalledProcessError as e:
                    print(f"ADB error: {e}")
                    
        except Exception as e:
            print(f"Error refreshing processes: {e}")
            
    def apply_filters(self):
        search_text = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        use_regex = self.regex_check.isChecked()
        
        for row in range(self.process_table.rowCount()):
            show_row = True
            name = self.process_table.item(row, 1).text().lower()
            pid = int(self.process_table.item(row, 0).text())
            
            # Apply text filter
            if search_text:
                if use_regex:
                    try:
                        if not re.search(search_text, name):
                            show_row = False
                    except re.error:
                        show_row = False
                elif search_text not in name:
                    show_row = False
                    
            # Apply type filter
            if filter_type == 'User' and pid < 1000:
                show_row = False
            elif filter_type == 'System' and pid >= 1000:
                show_row = False
            elif filter_type == 'Android Apps' and not name.startswith('com.'):
                show_row = False
            elif filter_type == 'High CPU':
                cpu = float(self.process_table.item(row, 2).text().replace('%', ''))
                if cpu < 50:
                    show_row = False
            elif filter_type == 'High Memory':
                memory = float(self.process_table.item(row, 3).text().replace('MB', ''))
                if memory < 500:
                    show_row = False
                    
            self.process_table.setRowHidden(row, not show_row)
            
    def kill_selected_process(self):
        selected = self.process_table.selectedItems()
        if selected:
            row = selected[0].row()
            pid = int(self.process_table.item(row, 0).text())
            try:
                if self.current_device == 'local':
                    psutil.Process(pid).terminate()
                else:
                    subprocess.run(['adb', '-s', self.current_device, 'shell', 'kill', str(pid)])
                self.refresh_processes()
            except Exception as e:
                print(f"Error killing process: {e}")
                
    def show_process_details(self):
        selected = self.process_table.selectedItems()
        if selected:
            row = selected[0].row()
            details = "\n".join([
                f"{self.process_table.horizontalHeaderItem(col).text()}: "
                f"{self.process_table.item(row, col).text()}"
                for col in range(self.process_table.columnCount())
            ])
            QMessageBox.information(self, "Process Details", details)