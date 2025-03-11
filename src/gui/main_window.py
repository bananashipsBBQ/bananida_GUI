from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QStackedWidget, QLabel, QScrollArea, 
                            QGridLayout, QLineEdit, QTextEdit, QFrame, QDialog, QFileDialog,
                            QCheckBox, QSpinBox, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap  # 添加 QPixmap 用于加载插图
import qtawesome as qta
from .widgets.device_panel import DevicePanel
from .widgets.process_panel import ProcessPanel
from .widgets.script_editor import ScriptEditorPanel
from .widgets.output_panel import OutputPanel
from .widgets.codeshare_browser import CodeShareBrowser
from .widgets.app_launcher import AppLauncher
from .widgets.process_monitor import ProcessMonitor
from .widgets.injection_panel import InjectionPanel
from .widgets.device_selector import DeviceSelector
from .widgets.history_page import HistoryPage
from core.history_manager import HistoryManager
import frida
import subprocess
import os
import json
import requests

class FridaInjectorMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("bananaship's | Frida Script Manager")
        self.setMinimumSize(1200, 700)
        self.history_manager = HistoryManager()
        self.favorites = []
        self.load_favorites()
        self.setup_ui()
        self.codeshare_browser.favorites_updated.connect(self.refresh_favorites)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        sidebar = self.create_sidebar()
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        layout.setStretch(0, 1)
        layout.setStretch(1, 5)

        self.init_pages()

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            QWidget#sidebar {
                background-color: #2f3136;
                border-right: 1px solid #202225;
                min-width: 150px;
                max-width: 150px;
            }
            QPushButton {
                text-align: left;
                padding: 4px 6px;
                border: none;
                border-radius: 3px;
                margin: 1px 2px;
                min-height: 28px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #36393f;
            }
            QPushButton:checked {
                background-color: #404249;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 2, 0, 2)

        self.nav_buttons = {}
        nav_items = [
            ("home", "Home", "fa5s.home"),
            ("inject", "Script Injection", "fa5s.syringe"),
            ("codeshare", "CodeShare", "fa5s.cloud-download-alt"),
            ("favorites", "Favorites", "fa5s.star"),
            ("history", "History", "fa5s.history"),
            ("monitor", "Process Monitor", "fa5s.desktop"),
            ("settings", "Settings", "fa5s.cog")
        ]

        for id_, text, icon in nav_items:
            btn = QPushButton(qta.icon(icon, color='#b9bbbe'), f" {text}")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, x=id_: self.switch_page(x))
            btn.setIconSize(QSize(12, 12))
            self.nav_buttons[id_] = btn
            layout.addWidget(btn)

        layout.addStretch()

        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(4, 2, 4, 2)
        self.status_icon = QLabel()
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#43b581').pixmap(6, 6))
        self.status_text = QLabel("Ready")
        self.status_text.setStyleSheet("color: #b9bbbe; font-size: 11px;")
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_text)
        layout.addLayout(status_layout)

        return sidebar

    def init_pages(self):
        self.pages = {
            'home': self.create_home_page(),
            'inject': self.create_injection_page(),
            'codeshare': self.create_codeshare_page(),
            'favorites': self.create_favorites_page(),
            'history': self.create_history_page(),
            'monitor': self.create_monitor_page(),
            'settings': self.create_settings_page()
        }
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.switch_page('home')

    def switch_page(self, page_id):
        for btn in self.nav_buttons.values():
            btn.setChecked(False)
        self.nav_buttons[page_id].setChecked(True)
        self.stack.setCurrentWidget(self.pages[page_id])

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        # 欢迎头部
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(4)

        title = QLabel("欢迎使用bananida_GUIfrida_注入工具")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        subtitle = QLabel("A powerful GUI tool for Frida script management and injection")
        subtitle.setStyleSheet("font-size: 14px; color: #b9bbbe;")
        author = QLabel("improved by bananaship")
        author.setStyleSheet("font-size: 12px; color: #7289da;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(author)

        # 插图区域（替换原 Quick Actions）
        illustration_frame = QFrame()
        illustration_frame.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        illustration_layout = QVBoxLayout(illustration_frame)
        illustration_layout.setContentsMargins(0, 0, 0, 0)

        # 添加插图（假设有一张图片文件，例如 'illustration.png'）
        illustration = QLabel()
        #pixmap = QPixmap('D://FridaGUI-feature-improved-gui//src//utils//beijing.jpg')  # 请替换为实际图片路径
        relative_path = os.path.join('src/utils', 'beijing.jpg')
        absolute_path = os.path.abspath(relative_path)
        print(f"Loading image from: {absolute_path}")
        pixmap = QPixmap(relative_path)
        if pixmap.isNull():
            print(f"Failed to load image: {relative_path}")
            #pixmap = QPixmap('../utils/beijing.jpg')
        if not pixmap.isNull():
            illustration.setPixmap(pixmap.scaled(1000, 600, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            illustration.setText("插图加载失败，请检查图片路径")
            illustration.setStyleSheet("color: #b9bbbe; font-size: 14px;")
        illustration.setAlignment(Qt.AlignCenter)
        illustration_layout.addWidget(illustration)

        layout.addWidget(header)
        layout.addWidget(illustration_frame)
        layout.addStretch()

        return page

    def create_injection_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(5)

        self.device_selector = DeviceSelector()
        self.script_editor = ScriptEditorPanel()
        self.injection_panel = InjectionPanel()
        self.injection_panel.script_editor = self.script_editor
        self.output_panel = OutputPanel()

        layout.addWidget(self.device_selector, stretch=1)
        layout.addWidget(self.script_editor, stretch=3)
        layout.addWidget(self.injection_panel, stretch=1)
        layout.addWidget(self.output_panel, stretch=2)

        self.device_selector.process_selected.connect(
            lambda device_id, pid: self.injection_panel.set_process(device_id, pid)
        )
        self.injection_panel.injection_started.connect(self.inject_script)
        self.injection_panel.injection_stopped.connect(self.stop_injection)

        return page

    def create_codeshare_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.codeshare_browser = CodeShareBrowser()
        self.codeshare_browser.open_in_injector.connect(self.open_script_in_injector)
        layout.addWidget(self.codeshare_browser)

        return page

    def create_favorites_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(5)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        search_input = QLineEdit()
        search_input.setPlaceholderText("⌕ Search favorites...")
        search_input.setMaximumHeight(25)
        search_input.textChanged.connect(self.filter_favorites)
        upload_btn = QPushButton(qta.icon('fa5s.file-upload'), "Upload")
        upload_btn.setMaximumHeight(25)
        upload_btn.clicked.connect(self.upload_script)

        toolbar.addWidget(search_input)
        toolbar.addWidget(upload_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #36393f; }")

        self.favorites_grid = QWidget()
        self.favorites_grid_layout = QGridLayout(self.favorites_grid)
        self.favorites_grid_layout.setSpacing(5)
        scroll.setWidget(self.favorites_grid)

        layout.addLayout(toolbar)
        layout.addWidget(scroll)

        self.refresh_favorites()

        return page

    def filter_favorites(self, text):
        search_text = text.lower()
        for i in range(self.favorites_grid_layout.count()):
            widget = self.favorites_grid_layout.itemAt(i).widget()
            if widget:
                title = widget.findChild(QLabel).text().lower()
                desc = widget.findChildren(QLabel)[-2].text().lower()
                widget.setVisible(search_text in title or search_text in desc)

    def upload_script(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload Script", "", "JavaScript Files (*.js);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    script_content = f.read()
                script_name = os.path.basename(file_path)
                script_info = {
                    'id': f"custom/{script_name}",
                    'title': script_name,
                    'author': 'Custom Script',
                    'description': 'Uploaded custom script',
                    'likes': 0,
                    'seen': 0,
                    'content': script_content
                }
                self.add_to_favorites(script_info)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload script: {str(e)}")

    def add_to_favorites(self, script_info):
        if not any(s['id'] == script_info['id'] for s in self.favorites):
            self.favorites.append(script_info)
            self.save_favorites()
        card = self.create_favorite_card(script_info)
        count = self.favorites_grid_layout.count()
        row = count // 3
        col = count % 3
        self.favorites_grid_layout.addWidget(card, row, col)

    def create_favorite_card(self, script_info):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 6px;
                padding: 6px;
            }
            QFrame:hover {
                background-color: #40444b;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(3)

        title = QLabel(script_info['title'])
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        author = QLabel(f"by {script_info['author']}")
        author.setStyleSheet("color: #b9bbbe; font-size: 11px;")
        desc = QLabel(script_info.get('description', '')[:80] + '...')
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #b9bbbe; font-size: 11px;")

        buttons = QHBoxLayout()
        buttons.setSpacing(4)
        view_btn = QPushButton("View")
        view_btn.setMaximumHeight(20)
        view_btn.clicked.connect(lambda: self.view_favorite(script_info))
        inject_btn = QPushButton("⚡")
        inject_btn.setMaximumHeight(20)
        inject_btn.clicked.connect(lambda: self.open_script_in_injector(script_info.get('content', '')))
        remove_btn = QPushButton("✕")
        remove_btn.setMaximumHeight(20)
        remove_btn.clicked.connect(lambda: self.remove_from_favorites(script_info, card))

        buttons.addWidget(view_btn)
        buttons.addWidget(inject_btn)
        buttons.addWidget(remove_btn)
        buttons.addStretch()

        layout.addWidget(title)
        layout.addWidget(author)
        layout.addWidget(desc)
        layout.addLayout(buttons)

        return card

    def view_favorite(self, script_info):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"View Script - {script_info['title']}")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(5)

        content = QTextEdit()
        content.setReadOnly(True)
        content.setFont(QFont('Consolas', 10))
        content.setText(script_info.get('content', 'Script content not available'))

        buttons = QHBoxLayout()
        buttons.setSpacing(4)
        copy_btn = QPushButton("Copy")
        copy_btn.setMaximumHeight(20)
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(content.toPlainText()))
        inject_btn = QPushButton("⚡ Inject")
        inject_btn.setMaximumHeight(20)
        inject_btn.clicked.connect(lambda: self.open_script_in_injector(content.toPlainText()))

        buttons.addWidget(copy_btn)
        buttons.addWidget(inject_btn)
        buttons.addStretch()

        layout.addWidget(content)
        layout.addLayout(buttons)
        dialog.exec_()

    def remove_from_favorites(self, script_info, card):
        reply = QMessageBox.question(
            self, "Remove Favorite", f"Remove {script_info['title']} from favorites?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            card.setParent(None)
            if script_info['id'].startswith('custom/'):
                self.favorites = [s for s in self.favorites if s['id'] != script_info['id']]
                self.save_favorites()
            elif hasattr(self.codeshare_browser, 'favorites'):
                self.codeshare_browser.favorites.remove(script_info['id'])
                self.codeshare_browser.save_favorites()
            self.refresh_favorites()

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "✓ Success", "📋 Copied to clipboard!")

    def create_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.history_page = HistoryPage(self.history_manager)
        self.history_page.script_selected.connect(self.open_script_in_injector)
        layout.addWidget(self.history_page)

        return page

    def create_monitor_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)

        self.process_monitor = ProcessMonitor(main_window=self)
        layout.addWidget(self.process_monitor)

        return page

    def create_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(5)

        settings_categories = [
            ("General", [
                ("Auto-inject on launch", "checkbox"),
                ("Save script history", "checkbox"),
                ("Dark theme", "checkbox")
            ]),
            ("Script Editor", [
                ("Font size", "spinbox"),
                ("Show line numbers", "checkbox"),
                ("Auto-completion", "checkbox")
            ]),
            ("Monitoring", [
                ("Update interval", "spinbox"),
                ("Show memory usage", "checkbox"),
                ("Log to file", "checkbox")
            ])
        ]

        for category, settings in settings_categories:
            group = QFrame()
            group.setStyleSheet("QFrame { background-color: #2f3136; border-radius: 4px; padding: 5px; }")
            group_layout = QVBoxLayout()
            group_layout.setSpacing(3)

            for setting_name, setting_type in settings:
                setting_layout = QHBoxLayout()
                setting_layout.setSpacing(4)
                label = QLabel(setting_name)
                label.setStyleSheet("font-size: 12px; color: #b9bbbe;")
                setting_layout.addWidget(label)

                if setting_type == "checkbox":
                    widget = QCheckBox()
                    widget.setMaximumHeight(20)
                elif setting_type == "spinbox":
                    widget = QSpinBox()
                    widget.setMaximumHeight(20)

                setting_layout.addWidget(widget)
                group_layout.addLayout(setting_layout)

            group.setLayout(group_layout)
            layout.addWidget(group)

        layout.addStretch()
        return page

    def on_process_started(self, name, pid):
        self.status_text.setText(f"Process started: {name} ({pid})")
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#43b581').pixmap(6, 6))

    def on_process_ended(self, name, pid):
        self.status_text.setText(f"Process ended: {name} ({pid})")
        self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#f04747').pixmap(6, 6))

    def on_memory_updated(self, pid, memory_mb):
        pass

    def inject_script(self, script_content, pid):
        try:
            if not script_content:
                QMessageBox.warning(self, "Error", "No script to inject!")
                return

            self.status_text.setText(f"Injecting into PID: {pid}")
            self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#faa61a').pixmap(6, 6))

            device_id = self.device_selector.current_device
            process_info = self.device_selector.get_selected_process_info()

            if not process_info:
                raise Exception("No process selected")

            device = frida.get_device(device_id)

            if device.type == 'usb':
                if not AndroidHelper.is_frida_running(device_id):
                    self.output_panel.append_output("[*] Starting frida-server on device...")
                    if not AndroidHelper.start_frida_server(device_id):
                        raise Exception("Failed to start frida-server")
                    self.output_panel.append_output("[+] frida-server started")
                    device = frida.get_device(device_id)

            try:
                session = device.attach(pid)
                self.output_panel.append_output(f"[+] Successfully attached to PID: {pid}")
            except frida.ProcessNotFoundError:
                try:
                    if device.type == 'local':
                        import psutil
                        process = psutil.Process(pid)
                        executable = process.exe()
                        pid = device.spawn([executable])
                        self.output_panel.append_output(f"[+] Spawned process with PID: {pid}")
                    else:
                        if device.type == 'usb':
                            package_name = process_info['name']
                            pid = device.spawn([package_name])
                            self.output_panel.append_output(f"[+] Spawned Android app: {package_name}")
                        else:
                            pid = device.spawn([process_info['name']])
                    session = device.attach(pid)
                    device.resume(pid)
                except Exception as e:
                    raise Exception(f"Failed to spawn process: {str(e)}")

            script = session.create_script(script_content)

            def on_message(message, data):
                if message['type'] == 'send':
                    self.output_panel.append_output(f"[*] {message['payload']}")
                elif message['type'] == 'error':
                    self.output_panel.append_output(f"[!] {message['description']}")

            script.on('message', on_message)
            script.load()

            self.status_text.setText(f"Injected PID: {pid}")
            self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#43b581').pixmap(6, 6))

            self.current_session = session
            self.current_script = script
            self.output_panel.append_output("[+] Script loaded successfully")

            self.history_manager.add_entry('script_injection', {
                'script': script_content,
                'pid': pid,
                'device': device_id,
                'status': 'success'
            })

        except Exception as e:
            error_msg = f"Injection failed: {str(e)}"
            self.output_panel.append_output(f"[-] {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            self.history_manager.add_entry('script_injection', {
                'script': script_content,
                'pid': pid,
                'device': device_id,
                'status': 'failed',
                'error': str(e)
            })
        finally:
            if hasattr(self, 'injection_panel'):
                self.injection_panel.reset_ui()

    def stop_injection(self):
        try:
            if hasattr(self, 'current_script') and self.current_script:
                self.current_script.unload()
            if hasattr(self, 'current_session') and self.current_session:
                self.current_session.detach()
            self.current_script = None
            self.current_session = None
            self.output_panel.append_output("[*] Script injection stopped")
            self.status_text.setText("Ready")
            self.status_icon.setPixmap(qta.icon('fa5s.circle', color='#43b581').pixmap(6, 6))
        except Exception as e:
            error_msg = f"Error stopping injection: {str(e)}"
            self.output_panel.append_output(f"[-] {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

    def on_process_selected(self, device_id, pid):
        self.current_device = device_id
        self.current_pid = pid
        self.status_text.setText(f"Selected PID: {pid} on device: {device_id}")

    def open_in_injector(self, device_id, pid):
        self.switch_page('inject')
        self.device_selector.select_device(device_id)
        self.device_selector.select_process(pid)

    def open_script_in_injector(self, code):
        self.switch_page('inject')
        self.script_editor.set_script(code)

    def load_favorites(self):
        try:
            favorites_file = os.path.join(os.path.expanduser('~'), '.frida_gui', 'favorites.json')
            if os.path.exists(favorites_file):
                with open(favorites_file, 'r') as f:
                    data = json.load(f)
                    self.favorites = data.get('scripts', [])
        except Exception as e:
            print(f"Error loading favorites: {e}")
            self.favorites = []

    def save_favorites(self):
        try:
            favorites_file = os.path.join(os.path.expanduser('~'), '.frida_gui', 'favorites.json')
            os.makedirs(os.path.dirname(favorites_file), exist_ok=True)
            with open(favorites_file, 'w') as f:
                json.dump({'scripts': self.favorites}, f)
        except Exception as e:
            print(f"Error saving favorites: {e}")

    def refresh_favorites(self):
        for i in reversed(range(self.favorites_grid_layout.count())):
            widget = self.favorites_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            all_favorites = []
            if hasattr(self.codeshare_browser, 'favorites'):
                response = requests.get(self.codeshare_browser.api_url)
                codeshare_scripts = response.json()
                for script in codeshare_scripts:
                    if script['id'] in self.codeshare_browser.favorites:
                        all_favorites.append(script)
            all_favorites.extend([s for s in self.favorites if s['id'].startswith('custom/')])

            if all_favorites:
                for idx, script_info in enumerate(all_favorites):
                    row = idx // 3
                    col = idx % 3
                    card = self.create_favorite_card(script_info)
                    self.favorites_grid_layout.addWidget(card, row, col)
            else:
                msg = QLabel("No favorite scripts yet.\nBrowse scripts and click ★ to add!")
                msg.setAlignment(Qt.AlignCenter)
                msg.setStyleSheet("color: #b9bbbe; font-size: 12px; padding: 10px;")
                self.favorites_grid_layout.addWidget(msg, 0, 0, 1, 3)
        except Exception as e:
            error_msg = QLabel(f"Error loading favorites: {str(e)}")
            error_msg.setStyleSheet("color: #ff4444; font-size: 12px;")
            self.favorites_grid_layout.addWidget(error_msg, 0, 0, 1, 3)

    def cleanup(self):
        if hasattr(self, 'process_monitor'):
            self.process_monitor.stop_monitoring()
        if hasattr(self, 'history_manager'):
            self.history_manager.save_history()
        if hasattr(self, 'device_selector'):
            self.device_selector.cleanup()
        self.stop_injection()
        self.current_script = None
        self.current_session = None

    def closeEvent(self, event):
        self.cleanup()
        event.accept()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = FridaInjectorMainWindow()
    window.show()
    sys.exit(app.exec_())