from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                           QMenu, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
import qtawesome as qta
from datetime import datetime

class HistoryPage(QWidget):
    script_selected = pyqtSignal(str)  # For opening scripts in injector
    
    def __init__(self, history_manager):
        super().__init__()
        self.history_manager = history_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header with title and clear button
        header_layout = QHBoxLayout()
        title = QLabel("Action History")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        
        clear_btn = QPushButton(qta.icon('fa5s.trash'), "Clear History")
        clear_btn.clicked.connect(self.clear_history)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(clear_btn)
        
        # History table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "Action", "Details", "Actions"])
        
        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #36393f;
                border: none;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #2f3136;
            }
            QHeaderView::section {
                background-color: #2f3136;
                padding: 8px;
                border: none;
                color: white;
                font-weight: bold;
            }
        """)
        
        # Set column stretching
        table_header = self.table.horizontalHeader()
        table_header.setSectionResizeMode(0, QHeaderView.Fixed)    # Time
        table_header.setSectionResizeMode(1, QHeaderView.Fixed)    # Action
        table_header.setSectionResizeMode(2, QHeaderView.Stretch)  # Details
        table_header.setSectionResizeMode(3, QHeaderView.Fixed)    # Actions
        
        self.table.setColumnWidth(0, 180)  # Time
        self.table.setColumnWidth(1, 120)  # Action
        self.table.setColumnWidth(3, 100)  # Actions
        
        # Context menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Add components to layout
        layout.addLayout(header_layout)
        layout.addWidget(self.table)
        
        self.refresh_history()
        
    def refresh_history(self):
        self.table.setRowCount(0)
        
        for entry in self.history_manager.history:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Time
            time_item = QTableWidgetItem(
                datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            )
            
            # Action
            action_item = QTableWidgetItem(entry['type'])
            
            # Details
            details = entry['details']
            if isinstance(details, dict):
                details_text = "\n".join(f"{k}: {v}" for k, v in details.items())
            else:
                details_text = str(details)
            details_item = QTableWidgetItem(details_text)
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            if 'script' in entry['details']:
                inject_btn = QPushButton(qta.icon('fa5s.syringe'), "")
                inject_btn.clicked.connect(
                    lambda x, s=entry['details']['script']: self.script_selected.emit(s)
                )
                action_layout.addWidget(inject_btn)
                
            action_layout.addStretch()
            
            # Add items to row
            self.table.setItem(row, 0, time_item)
            self.table.setItem(row, 1, action_item)
            self.table.setItem(row, 2, details_item)
            self.table.setCellWidget(row, 3, action_widget)
            
    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.clear_history()
            self.refresh_history()
            
    def show_context_menu(self, position):
        menu = QMenu()
        
        copy_action = menu.addAction("Copy Details")
        copy_action.triggered.connect(
            lambda: self.copy_details(self.table.currentRow())
        )
        
        menu.exec_(self.table.viewport().mapToGlobal(position))
        
    def copy_details(self, row):
        if row >= 0:
            details_item = self.table.item(row, 2)
            if details_item:
                clipboard = QApplication.clipboard()
                clipboard.setText(details_item.text()) 