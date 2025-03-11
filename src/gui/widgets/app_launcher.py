from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLineEdit, QComboBox, QLabel, QTableWidget, 
                           QTableWidgetItem, QMenu, QAction, QCheckBox,
                           QFileDialog, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt
import subprocess
import json
import os
import qtawesome as qta
import sys

class AppLauncher(QWidget):
    app_launched = pyqtSignal(str, int)  # package_name, pid
    script_selected = pyqtSignal(str)  # script content
    
    def __init__(self):
        super().__init__()
        self.favorites_file = os.path.join(os.path.expanduser('~'), '.frida_gui', 'favorites.json')
        self.scripts_dir = os.path.join(os.path.expanduser('~'), '.frida_gui', 'scripts')
        self.load_favorites()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Quick Launch Section
        quick_launch_group = QGroupBox("Quick Launch")
        quick_launch_layout = QVBoxLayout()
        
        # Package input
        package_layout = QHBoxLayout()
        self.package_input = QLineEdit()
        self.package_input.setPlaceholderText("Enter package name or path...")
        self.launch_button = QPushButton("Launch")
        self.launch_button.setIcon(qta.icon('fa5s.play'))
        self.launch_button.clicked.connect(self.launch_app)
        package_layout.addWidget(self.package_input)
        package_layout.addWidget(self.launch_button)
        
        # Script Selection
        script_layout = QHBoxLayout()
        self.script_input = QLineEdit()
        self.script_input.setPlaceholderText("Select Frida script file...")
        self.script_input.setReadOnly(True)
        
        self.browse_script_btn = QPushButton("Browse")
        self.browse_script_btn.setIcon(qta.icon('fa5s.folder-open'))
        self.browse_script_btn.clicked.connect(self.browse_script)
        
        self.edit_script_btn = QPushButton("Edit")
        self.edit_script_btn.setIcon(qta.icon('fa5s.edit'))
        self.edit_script_btn.clicked.connect(self.edit_script)
        self.edit_script_btn.setEnabled(False)
        
        script_layout.addWidget(self.script_input)
        script_layout.addWidget(self.browse_script_btn)
        script_layout.addWidget(self.edit_script_btn)
        
        # Launch Options
        options_layout = QHBoxLayout()
        self.debug_check = QCheckBox("Debug Mode")
        self.wait_check = QCheckBox("Wait for Debugger")
        self.inject_check = QCheckBox("Auto-Inject Script")
        self.inject_check.toggled.connect(self.toggle_script_selection)
        
        options_layout.addWidget(self.debug_check)
        options_layout.addWidget(self.wait_check)
        options_layout.addWidget(self.inject_check)
        
        quick_launch_layout.addLayout(package_layout)
        quick_launch_layout.addLayout(script_layout)
        quick_launch_layout.addLayout(options_layout)
        quick_launch_group.setLayout(quick_launch_layout)
        
        # Favorites Section
        favorites_group = QGroupBox("Favorites")
        favorites_layout = QVBoxLayout()
        
        self.favorites_table = QTableWidget(0, 4)  # Added column for script
        self.favorites_table.setHorizontalHeaderLabels(["Name", "Package", "Script", "Actions"])
        self.favorites_table.horizontalHeader().setStretchLastSection(True)
        self.favorites_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favorites_table.customContextMenuRequested.connect(self.show_context_menu)
        
        favorites_layout.addWidget(self.favorites_table)
        favorites_group.setLayout(favorites_layout)
        
        # Recent Apps Section
        recent_group = QGroupBox("Recent Apps")
        recent_layout = QHBoxLayout()
        self.recent_combo = QComboBox()
        self.recent_combo.setPlaceholderText("Recent Apps")
        recent_launch_btn = QPushButton("Launch Recent")
        recent_launch_btn.clicked.connect(self.launch_recent)
        
        recent_layout.addWidget(self.recent_combo)
        recent_layout.addWidget(recent_launch_btn)
        recent_group.setLayout(recent_layout)
        
        # Add all sections to main layout
        layout.addWidget(quick_launch_group)
        layout.addWidget(favorites_group)
        layout.addWidget(recent_group)
        
        # Populate favorites
        self.update_favorites_table()
        
    def browse_script(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Frida Script",
            self.scripts_dir,
            "JavaScript Files (*.js);;All Files (*.*)"
        )
        
        if file_name:
            self.script_input.setText(file_name)
            self.edit_script_btn.setEnabled(True)
            
            # Read script content
            try:
                with open(file_name, 'r') as f:
                    script_content = f.read()
                self.script_selected.emit(script_content)
            except Exception as e:
                print(f"Error reading script: {str(e)}")
                
    def edit_script(self):
        script_path = self.script_input.text()
        if script_path and os.path.exists(script_path):
            # You can implement your own script editor or use system default
            if sys.platform == 'win32':
                os.startfile(script_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', script_path])
            else:
                subprocess.run(['xdg-open', script_path])
                
    def toggle_script_selection(self, enabled):
        self.script_input.setEnabled(enabled)
        self.browse_script_btn.setEnabled(enabled)
        self.edit_script_btn.setEnabled(enabled and bool(self.script_input.text()))
        
    def add_to_favorites(self, name, package, script_path=None):
        self.favorites[name] = {
            'package': package,
            'script': script_path
        }
        self.save_favorites()
        self.update_favorites_table()
        
    def update_favorites_table(self):
        self.favorites_table.setRowCount(0)
        for name, data in self.favorites.items():
            row = self.favorites_table.rowCount()
            self.favorites_table.insertRow(row)
            
            name_item = QTableWidgetItem(name)
            package_item = QTableWidgetItem(data['package'])
            script_item = QTableWidgetItem(data.get('script', ''))
            
            launch_btn = QPushButton("Launch")
            launch_btn.clicked.connect(
                lambda checked, p=data['package'], s=data.get('script'): 
                self.launch_favorite(p, s)
            )
            
            self.favorites_table.setItem(row, 0, name_item)
            self.favorites_table.setItem(row, 1, package_item)
            self.favorites_table.setItem(row, 2, script_item)
            self.favorites_table.setCellWidget(row, 3, launch_btn)
            
    def launch_favorite(self, package, script_path=None):
        if script_path:
            try:
                with open(script_path, 'r') as f:
                    script_content = f.read()
                self.script_selected.emit(script_content)
            except Exception as e:
                print(f"Error reading script: {str(e)}")
        self.launch_app(package)
        
    def show_context_menu(self, position):
        menu = QMenu()
        remove_action = QAction("Remove from Favorites", self)
        remove_action.triggered.connect(self.remove_selected_favorite)
        
        edit_script_action = QAction("Edit Script", self)
        edit_script_action.triggered.connect(self.edit_selected_script)
        
        menu.addAction(remove_action)
        menu.addAction(edit_script_action)
        menu.exec_(self.favorites_table.mapToGlobal(position))
        
    def edit_selected_script(self):
        current_row = self.favorites_table.currentRow()
        if current_row >= 0:
            script_path = self.favorites_table.item(current_row, 2).text()
            if script_path:
                if sys.platform == 'win32':
                    os.startfile(script_path)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', script_path])
                else:
                    subprocess.run(['xdg-open', script_path])
                
    def launch_app(self, package_name=None):
        if not package_name:
            package_name = self.package_input.text()
            
        try:
            cmd = ['adb', 'shell', 'am', 'start']
            
            if self.debug_check.isChecked():
                cmd.extend(['-D'])
                
            if self.wait_check.isChecked():
                cmd.extend(['-W'])
                
            cmd.extend(['-n', f'{package_name}/{package_name}.MainActivity'])
            
            process = subprocess.Popen(cmd, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
            
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.add_to_recent(package_name)
                # Get PID of launched app
                pid_cmd = ['adb', 'shell', 'pidof', package_name]
                pid = subprocess.check_output(pid_cmd).decode().strip()
                if pid:
                    self.app_launched.emit(package_name, int(pid))
            else:
                raise Exception(stderr.decode())
                
        except Exception as e:
            print(f"Error launching app: {str(e)}")
            
    def add_to_favorites(self, name, package):
        self.favorites[name] = package
        self.save_favorites()
        self.update_favorites_table()
        
    def remove_from_favorites(self, name):
        if name in self.favorites:
            del self.favorites[name]
            self.save_favorites()
            self.update_favorites_table()
            
    def load_favorites(self):
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r') as f:
                    self.favorites = json.load(f)
            else:
                self.favorites = {}
        except:
            self.favorites = {}
            
    def save_favorites(self):
        os.makedirs(os.path.dirname(self.favorites_file), exist_ok=True)
        with open(self.favorites_file, 'w') as f:
            json.dump(self.favorites, f)
            
    def update_favorites_table(self):
        self.favorites_table.setRowCount(0)
        for name, package in self.favorites.items():
            row = self.favorites_table.rowCount()
            self.favorites_table.insertRow(row)
            
            name_item = QTableWidgetItem(name)
            package_item = QTableWidgetItem(package)
            
            launch_btn = QPushButton("Launch")
            launch_btn.clicked.connect(lambda checked, p=package: self.launch_app(p))
            
            self.favorites_table.setItem(row, 0, name_item)
            self.favorites_table.setItem(row, 1, package_item)
            self.favorites_table.setCellWidget(row, 2, launch_btn)
            
    def show_context_menu(self, position):
        menu = QMenu()
        remove_action = QAction("Remove from Favorites", self)
        remove_action.triggered.connect(lambda: self.remove_selected_favorite())
        menu.addAction(remove_action)
        menu.exec_(self.favorites_table.mapToGlobal(position))
        
    def remove_selected_favorite(self):
        current_row = self.favorites_table.currentRow()
        if current_row >= 0:
            name = self.favorites_table.item(current_row, 0).text()
            self.remove_from_favorites(name)
            
    def add_to_recent(self, package_name):
        current_text = self.recent_combo.currentText()
        if current_text != package_name:
            self.recent_combo.insertItem(0, package_name)
            if self.recent_combo.count() > 10:
                self.recent_combo.removeItem(10)
                
    def launch_recent(self):
        package_name = self.recent_combo.currentText()
        if package_name:
            self.launch_app(package_name) 