from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLineEdit, QPushButton, QListWidget, 
                           QTextBrowser, QSplitter, QComboBox,
                           QLabel, QProgressBar, QMessageBox, QGroupBox, QDialog, QTabWidget, QMenu, QFrame, QTableWidget, QHeaderView, QFileDialog, QScrollArea, QGridLayout, QTextEdit)
from PyQt5.QtCore import pyqtSignal, Qt, QThread, QUrl
from PyQt5.QtGui import QFont, QDesktopServices, QIcon
import aiohttp
import asyncio
import qtawesome as qta
import json
import os
from bs4 import BeautifulSoup
from core.script_templates import SCRIPT_TEMPLATES
from core.script_history import ScriptHistory
import time
import requests
import threading
import re

class CodeFetcher(QThread):
    code_fetched = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            response = requests.get(self.url)
            if response.status_code != 200:
                self.error_occurred.emit(f"HTTP Error: {response.status_code}")
                return
                
            # Find the script content in the Vue.js data
            script_match = re.search(r'projectSource: "(.*?)",', response.text, re.DOTALL)
            if script_match:
                # Unescape the JavaScript string
                code = script_match.group(1).encode().decode('unicode_escape')
                self.code_fetched.emit(code)
            else:
                # Try alternative method - look for the editor content
                soup = BeautifulSoup(response.text, 'html.parser')
                editor_div = soup.find('div', {'id': 'editor'})
                if editor_div and editor_div.string:
                    self.code_fetched.emit(editor_div.string)
                else:
                    self.error_occurred.emit("Could not find script content")
                
        except Exception as e:
            self.error_occurred.emit(f"Error fetching script: {str(e)}")

class CodeShareBrowser(QWidget):
    script_selected = pyqtSignal(str)  # For injector
    open_in_injector = pyqtSignal(str)  # New signal for opening in injector
    favorites_updated = pyqtSignal()    # New signal for favorites updates
    
    def __init__(self):
        super().__init__()
        self.scripts_cache = {}
        self.api_url = "https://konsumer.js.org/frida-codeshare/codeshare.json"
        self.favorites = []  # Initialize as empty list
        self.load_favorites()
        self.setup_ui()
        
    def load_favorites(self):
        """Load favorites from file"""
        try:
            favorites_file = os.path.join(os.path.expanduser('~'), '.frida_gui', 'favorites.json')
            if os.path.exists(favorites_file):
                with open(favorites_file, 'r') as f:
                    data = json.load(f)
                    # Make sure we get a list, even if loading from a dict
                    if isinstance(data, dict):
                        self.favorites = data.get('favorites', [])
                    else:
                        self.favorites = data if isinstance(data, list) else []
            else:
                self.favorites = []
        except Exception as e:
            print(f"Error loading favorites: {e}")
            self.favorites = []
        
    def save_favorites(self):
        """Save favorites to file"""
        try:
            favorites_file = os.path.join(os.path.expanduser('~'), '.frida_gui', 'favorites.json')
            os.makedirs(os.path.dirname(favorites_file), exist_ok=True)
            with open(favorites_file, 'w') as f:
                # Save as a simple list
                json.dump(self.favorites, f)
        except Exception as e:
            print(f"Error saving favorites: {e}")
            
    def is_favorite(self, script_id):
        """Check if script is favorited"""
        return script_id in self.favorites
        
    def toggle_favorite(self, script_info):
        """Toggle favorite status of script"""
        script_id = script_info['id']
        if script_id in self.favorites:
            self.favorites.remove(script_id)
        else:
            self.favorites.append(script_id)
        self.save_favorites()
        self.refresh_favorites()
        self.favorites_updated.emit()  # Emit signal when favorites change
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.browse_tab = QWidget()
        self.favorites_tab = QWidget()
        
        self.setup_browse_tab()
        self.setup_favorites_tab()
        
        # Add tabs
        self.tab_widget.addTab(self.browse_tab, "Browse")
        self.tab_widget.addTab(self.favorites_tab, "★ Favorites")
        
        layout.addWidget(self.tab_widget)
        
        self.refresh_scripts()
        
    def setup_browse_tab(self):
        """Setup the browse tab (existing functionality)"""
        layout = QVBoxLayout(self.browse_tab)
        
        # Move existing toolbar and grid here
        toolbar = QHBoxLayout()
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("⌕ Search scripts...")
        self.search_input.textChanged.connect(self.filter_scripts)
        
        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.addItems(['All', 'Android', 'iOS', 'Windows', 'Linux', 'macOS'])
        self.category_combo.currentTextChanged.connect(self.filter_scripts)
        
        # Sort options
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['★ Most Popular', '👁 Most Viewed', '⏲ Latest'])
        self.sort_combo.currentTextChanged.connect(self.refresh_scripts)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.category_combo)
        toolbar.addWidget(self.sort_combo)
        
        # Grid layout for scripts
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidget(self.grid_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #36393f;
            }
        """)
        
        # Add all components
        layout.addLayout(toolbar)
        layout.addWidget(scroll)
        
    def setup_favorites_tab(self):
        """Setup the favorites tab"""
        layout = QVBoxLayout(self.favorites_tab)
        
        # Create grid for favorite scripts
        self.favorites_grid = QWidget()
        self.favorites_grid_layout = QGridLayout(self.favorites_grid)
        self.favorites_grid_layout.setSpacing(10)
        
        # Scroll area for favorites
        scroll = QScrollArea()
        scroll.setWidget(self.favorites_grid)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #36393f;
            }
        """)
        
        # Add to layout
        layout.addWidget(scroll)
        
        # Initial population of favorites
        self.refresh_favorites()
        
    def refresh_favorites(self):
        """Refresh the favorites grid"""
        # Clear existing favorites grid
        for i in reversed(range(self.favorites_grid_layout.count())): 
            widget = self.favorites_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            
        # Get favorite scripts
        try:
            # Get all scripts
            response = requests.get(self.api_url)
            all_scripts = response.json()
            
            # Filter to only favorited scripts
            favorite_scripts = [s for s in all_scripts if s['id'] in self.favorites]
            
            if favorite_scripts:
                # Add scripts to grid
                for idx, script_info in enumerate(favorite_scripts):
                    row = idx // 3
                    col = idx % 3
                    card = self.create_script_card(script_info)
                    self.favorites_grid_layout.addWidget(card, row, col)
            else:
                # Show message if no favorites
                msg = QLabel("No favorite scripts yet.\nBrowse scripts and click the ★ to add favorites!")
                msg.setAlignment(Qt.AlignCenter)
                msg.setStyleSheet("""
                    color: #b9bbbe;
                    font-size: 14px;
                    padding: 20px;
                """)
                self.favorites_grid_layout.addWidget(msg, 0, 0, 1, 3)
                
        except Exception as e:
            print(f"Error refreshing favorites: {e}")
            error_msg = QLabel(f"Error loading favorites: {str(e)}")
            error_msg.setStyleSheet("color: #ff4444;")
            self.favorites_grid_layout.addWidget(error_msg, 0, 0, 1, 3)

    def fetch_scripts(self):
        """Fetch scripts from API"""
        try:
            response = requests.get(self.api_url)
            scripts = response.json()
            
            # Sort scripts
            sort_option = self.sort_combo.currentText()
            if sort_option == 'Most Popular':
                scripts.sort(key=lambda x: x.get('likes', 0), reverse=True)
            elif sort_option == 'Most Viewed':
                scripts.sort(key=lambda x: x.get('seen', 0), reverse=True)
            
            return scripts
        except Exception as e:
            print(f"Error fetching scripts: {e}")
            return []
            
    def create_script_card(self, script_info):
        """Create a card widget for a script"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2f3136;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #40444b;
            }
            QLabel {
                color: white;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Title
        title = QLabel(script_info['title'])
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        title.setWordWrap(True)
        
        # Author
        author = QLabel(f"by {script_info['author']}")
        author.setStyleSheet("color: #b9bbbe;")
        
        # Stats
        stats = QHBoxLayout()
        stars = QLabel(f"★ {script_info.get('likes', 0)}")
        views = QLabel(f"👁 {script_info.get('seen', 0)}")
        stats.addWidget(stars)
        stats.addWidget(views)
        
        # Description
        desc = QLabel(script_info.get('description', '')[:100] + '...')
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #b9bbbe;")
        
        # Action buttons
        buttons = QHBoxLayout()
        
        view_btn = QPushButton("View")
        view_btn.clicked.connect(lambda: self.fetch_script_code(script_info))
        
        fav_btn = QPushButton()
        if self.is_favorite(script_info['id']):
            fav_btn.setIcon(QIcon())
            fav_btn.setText("★")
        else:
            fav_btn.setIcon(QIcon())
            fav_btn.setText("☆")
            fav_btn.setStyleSheet("color: #b9bbbe;")
        fav_btn.clicked.connect(lambda: self.toggle_favorite_ui(script_info, fav_btn))
        
        buttons.addWidget(view_btn)
        buttons.addWidget(fav_btn)
        buttons.addStretch()
        
        layout.addWidget(title)
        layout.addWidget(author)
        layout.addLayout(stats)
        layout.addWidget(desc)
        layout.addLayout(buttons)
        
        return card
        
    def fetch_script_code(self, script_info):
        """Fetch and show script code"""
        # Remove author name from ID if it's included
        script_id = script_info['id'].replace(f"{script_info['author']}/", "")
        url = f"https://codeshare.frida.re/@{script_info['author']}/{script_id}"
        print(f"Fetching script from: {url}")  # Debug print
        
        # Create preview dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Frida CodeShare - {script_info['title']}")
        dialog.resize(1000, 800)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2f3136;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #7289da;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #677bc4;
            }
            QTextEdit {
                background-color: #36393f;
                color: #dcddde;
                border: none;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(script_info['title'])
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        author = QLabel(f"by {script_info['author']}")
        author.setStyleSheet("color: #b9bbbe;")
        header.addWidget(title)
        header.addWidget(author)
        header.addStretch()
        
        # Stats
        stats = QHBoxLayout()
        likes = QLabel(f"★ {script_info.get('likes', 0)}")
        views = QLabel(f"👁 {script_info.get('seen', 0)}")
        stats.addWidget(likes)
        stats.addWidget(views)
        stats.addStretch()
        
        # Description
        desc = QLabel(script_info.get('description', ''))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #b9bbbe; padding: 10px;")
        
        # Code preview
        code_view = QTextEdit()
        code_view.setReadOnly(True)
        code_view.setFont(QFont('Consolas', 11))
        code_view.setLineWrapMode(QTextEdit.NoWrap)
        code_view.setText("Loading script...")
        
        # Usage instructions
        usage = QLabel(f"Try this code out by running:\n$ frida --codeshare {script_info['author']}/{script_info['id']} -f YOUR_BINARY")
        usage.setStyleSheet("""
            background-color: #202225;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Consolas', monospace;
        """)
        
        # Action buttons
        buttons = QHBoxLayout()
        
        copy_btn = QPushButton(qta.icon('fa5s.copy'), "⎘ Copy Code")
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(code_view.toPlainText()))
        
        inject_btn = QPushButton(qta.icon('fa5s.syringe'), "⚡ Open in Injector")
        inject_btn.clicked.connect(lambda: self.open_in_injector_page(code_view.toPlainText(), dialog))
        
        download_btn = QPushButton(qta.icon('fa5s.download'), "⤓ Download")
        download_btn.clicked.connect(lambda: self.download_script(script_info['title'], code_view.toPlainText()))
        
        open_btn = QPushButton(qta.icon('fa5s.external-link-alt'), "⧉ Open in Browser")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        
        buttons.addWidget(copy_btn)
        buttons.addWidget(inject_btn)
        buttons.addWidget(download_btn)
        buttons.addWidget(open_btn)
        buttons.addStretch()
        
        # Add all components
        layout.addLayout(header)
        layout.addLayout(stats)
        layout.addWidget(desc)
        layout.addWidget(usage)
        layout.addWidget(code_view)
        layout.addLayout(buttons)
        
        dialog.show()
        
        # Create and start the code fetcher thread
        self.code_fetcher = CodeFetcher(url)
        self.code_fetcher.code_fetched.connect(code_view.setText)
        self.code_fetcher.error_occurred.connect(lambda err: code_view.setText(f"Error loading script: {err}"))
        self.code_fetcher.start()

    def refresh_scripts(self):
        """Refresh scripts from API"""
        # Clear existing grid
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        # Fetch and sort scripts
        scripts = self.fetch_scripts()
        
        # Add all scripts to grid
        for idx, script_info in enumerate(scripts):
            row = idx // 3
            col = idx % 3
            card = self.create_script_card(script_info)
            self.grid_layout.addWidget(card, row, col)
            
        # Refresh favorites tab
        self.refresh_favorites()

    def add_script(self, script_info):
        """Add a script card to the grid"""
        # Calculate grid position
        count = self.grid_layout.count()
        row = count // 3
        col = count % 3
        
        # Create and add card
        card = self.create_script_card(script_info)
        self.grid_layout.addWidget(card, row, col)
        
        # Cache the script
        self.scripts_cache[script_info['id']] = script_info

    def filter_scripts(self):
        """Filter visible scripts based on search and category"""
        search_text = self.search_input.text().lower()
        category = self.category_combo.currentText()
        
        # Show/hide cards based on filters
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                title = widget.findChild(QLabel).text().lower()
                desc = widget.findChildren(QLabel)[-2].text().lower()  # Description label
                
                show = True
                if search_text and search_text not in title and search_text not in desc:
                    show = False
                if category != 'All' and category not in desc:
                    show = False
                    
                widget.setVisible(show)

    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "✓ Success", "⎘ Copied to clipboard!")

    def download_script(self, title, code):
        """Download script to file"""
        filename = f"{title.lower().replace(' ', '_')}.js"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "⤓ Save Script", filename, "JavaScript Files (*.js)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(code)
                QMessageBox.information(self, "✓ Success", "⤓ Script downloaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "✗ Error", f"Failed to save script: {str(e)}")

    def toggle_favorite_ui(self, script_info, button):
        """Toggle favorite status and update UI"""
        self.toggle_favorite(script_info)
        if self.is_favorite(script_info['id']):
            button.setIcon(QIcon())
            button.setText("★")
        else:
            button.setIcon(QIcon())
            button.setText("☆")
            button.setStyleSheet("color: #b9bbbe;")
            
        # Refresh favorites tab when status changes
        self.refresh_favorites()

    def open_in_injector_page(self, code, dialog=None):
        """Open the script in the injector page"""
        self.open_in_injector.emit(code)  # Emit signal to main window
        if dialog:
            dialog.close()  # Close the preview dialog