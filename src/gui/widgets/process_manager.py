from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
                           QMenu, QAction, QComboBox, QCheckBox, QFrame,
                           QTableWidgetSelectionRange, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont
import qtawesome as qta
import re
import psutil

class ProcessManager(QWidget):
    process_selected = pyqtSignal(int)  # pid
    
    def __init__(self):
        super().__init__()
        self.processes = {}
        self.filters = {
            'name': '',
            'pid': '',
            'cpu': 0,
            'memory': 0,
            'show_system': False
        }
        self.setup_ui()
        self.start_monitoring()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        
        # Search with regex support
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
        self.filter_combo.addItems(['All', 'User', 'System', 'Android Apps'])
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        
        # Resource thresholds
        self.cpu_threshold = QSpinBox()
        self.cpu_threshold.setSuffix("% CPU")
        self.cpu_threshold.valueChanged.connect(self.apply_filters)
        
        self.memory_threshold = QSpinBox()
        self.memory_threshold.setSuffix("MB")
        self.memory_threshold.setMaximum(32000)
        self.memory_threshold.valueChanged.connect(self.apply_filters)
        
        filter_layout.addWidget(search_container)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(self.cpu_threshold)
        filter_layout.addWidget(self.memory_threshold)
        
        # Process table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(6)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "CPU %", "Memory", "Status", "Path"
        ])
        
        # Style the table
        self.process_table.setStyleSheet("""
            QTableWidget {
                background-color: #36393f;
                border: none;
                border-radius: 8px;
                gridline-color: #2f3136;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #2f3136;
            }
            QTableWidget::item:selected {
                background-color: #7289da;
            }
        """)
        
        # Set column widths
        header = self.process_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # PID
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # CPU
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Memory
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Path
        
        self.process_table.setColumnWidth(0, 70)  # PID
        self.process_table.setColumnWidth(2, 80)  # CPU
        self.process_table.setColumnWidth(3, 100)  # Memory
        self.process_table.setColumnWidth(4, 100)  # Status
        
        # Context menu
        self.process_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.process_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Quick action buttons
        action_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton(qta.icon('fa5s.sync'), "Refresh")
        self.refresh_btn.clicked.connect(self.refresh_processes)
        
        self.kill_btn = QPushButton(qta.icon('fa5s.stop'), "Kill")
        self.kill_btn.clicked.connect(self.kill_selected_process)
        
        self.inject_btn = QPushButton(qta.icon('fa5s.syringe'), "Inject")
        self.inject_btn.clicked.connect(self.inject_into_selected)
        
        action_layout.addWidget(self.refresh_btn)
        action_layout.addWidget(self.kill_btn)
        action_layout.addWidget(self.inject_btn)
        action_layout.addStretch()
        
        # Status bar
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        status_layout = QHBoxLayout(status_bar)
        
        self.process_count = QLabel("0 processes")
        self.cpu_usage = QLabel("CPU: 0%")
        self.memory_usage = QLabel("Memory: 0 MB")
        
        status_layout.addWidget(self.process_count)
        status_layout.addStretch()
        status_layout.addWidget(self.cpu_usage)
        status_layout.addWidget(self.memory_usage)
        
        # Add all components
        layout.addWidget(filter_frame)
        layout.addWidget(self.process_table)
        layout.addLayout(action_layout)
        layout.addWidget(status_bar)
        
    def start_monitoring(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_processes)
        self.update_timer.start(2000)  # Update every 2 seconds
        
    def refresh_processes(self):
        self.processes.clear()
        total_cpu = 0
        total_memory = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'exe']):
            try:
                info = proc.info
                memory_mb = info['memory_info'].rss / 1024 / 1024
                self.processes[info['pid']] = {
                    'name': info['name'],
                    'cpu': info['cpu_percent'],
                    'memory': memory_mb,
                    'status': info['status'],
                    'path': info['exe'] or ''
                }
                total_cpu += info['cpu_percent']
                total_memory += memory_mb
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        self.update_table()
        self.update_stats(total_cpu, total_memory)
        
    def update_table(self):
        self.process_table.setSortingEnabled(False)
        self.process_table.setRowCount(0)
        
        filtered_processes = self.filter_processes()
        
        for pid, info in filtered_processes.items():
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)
            
            # PID
            pid_item = QTableWidgetItem(str(pid))
            pid_item.setTextAlignment(Qt.AlignCenter)
            
            # Name
            name_item = QTableWidgetItem(info['name'])
            
            # CPU
            cpu_item = QTableWidgetItem(f"{info['cpu']:.1f}%")
            cpu_item.setTextAlignment(Qt.AlignCenter)
            
            # Memory
            memory_item = QTableWidgetItem(f"{info['memory']:.1f} MB")
            memory_item.setTextAlignment(Qt.AlignCenter)
            
            # Status
            status_item = QTableWidgetItem(info['status'])
            status_item.setTextAlignment(Qt.AlignCenter)
            
            # Path
            path_item = QTableWidgetItem(info['path'])
            
            # Set items
            self.process_table.setItem(row, 0, pid_item)
            self.process_table.setItem(row, 1, name_item)
            self.process_table.setItem(row, 2, cpu_item)
            self.process_table.setItem(row, 3, memory_item)
            self.process_table.setItem(row, 4, status_item)
            self.process_table.setItem(row, 5, path_item)
            
            # Color coding based on resource usage
            if info['cpu'] > 50:
                self.color_row(row, QColor(240, 71, 71, 50))  # Red
            elif info['memory'] > 1000:
                self.color_row(row, QColor(250, 166, 26, 50))  # Orange
                
        self.process_table.setSortingEnabled(True)
        
    def filter_processes(self):
        filtered = {}
        search_text = self.search_input.text().lower()
        
        for pid, info in self.processes.items():
            # Apply regex/text filter
            if self.regex_check.isChecked():
                try:
                    if not re.search(search_text, info['name'].lower()):
                        continue
                except re.error:
                    continue
            elif search_text and search_text not in info['name'].lower():
                continue
                
            # Apply type filter
            if self.filter_combo.currentText() == 'User' and pid < 1000:
                continue
            elif self.filter_combo.currentText() == 'System' and pid >= 1000:
                continue
            elif self.filter_combo.currentText() == 'Android Apps' and not info['name'].startswith('com.'):
                continue
                
            # Apply resource thresholds
            if info['cpu'] < self.cpu_threshold.value():
                continue
            if info['memory'] < self.memory_threshold.value():
                continue
                
            filtered[pid] = info
            
        return filtered
        
    def color_row(self, row, color):
        for col in range(self.process_table.columnCount()):
            item = self.process_table.item(row, col)
            item.setBackground(color)
            
    def update_stats(self, total_cpu, total_memory):
        self.process_count.setText(f"{len(self.processes)} processes")
        self.cpu_usage.setText(f"CPU: {total_cpu:.1f}%")
        self.memory_usage.setText(f"Memory: {total_memory:.0f} MB")
        
    def show_context_menu(self, position):
        menu = QMenu()
        
        kill_action = QAction("Kill Process", self)
        kill_action.triggered.connect(self.kill_selected_process)
        
        inject_action = QAction("Inject Script", self)
        inject_action.triggered.connect(self.inject_into_selected)
        
        menu.addAction(kill_action)
        menu.addAction(inject_action)
        menu.exec_(self.process_table.mapToGlobal(position))
        
    def kill_selected_process(self):
        selected = self.process_table.selectedItems()
        if selected:
            pid = int(self.process_table.item(selected[0].row(), 0).text())
            try:
                psutil.Process(pid).terminate()
                self.refresh_processes()
            except psutil.NoSuchProcess:
                pass
                
    def inject_into_selected(self):
        selected = self.process_table.selectedItems()
        if selected:
            pid = int(self.process_table.item(selected[0].row(), 0).text())
            self.process_selected.emit(pid) 