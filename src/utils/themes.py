from PyQt5.QtWidgets import QStyleFactory
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

# Discord-inspired color scheme
DISCORD_COLORS = {
    'background': '#36393f',
    'secondary_bg': '#2f3136',
    'tertiary_bg': '#202225',
    'text': '#dcddde',
    'secondary_text': '#96989d',
    'accent': '#ec695c',
    'accent_hover': '#4752c4',
    'red': '#ed4245',
    'green': '#3ba55c'
}

STYLE_SHEET = """
QMainWindow, QWidget {
    background-color: """ + DISCORD_COLORS['background'] + """;
    color: """ + DISCORD_COLORS['text'] + """;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QTabWidget::pane {
    border: none;
    background-color: """ + DISCORD_COLORS['background'] + """;
}

QTabWidget::tab-bar {
    alignment: left;
}

QTabBar::tab {
    background-color: """ + DISCORD_COLORS['tertiary_bg'] + """;
    color: """ + DISCORD_COLORS['secondary_text'] + """;
    padding: 8px 16px;
    border: none;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: """ + DISCORD_COLORS['background'] + """;
    color: """ + DISCORD_COLORS['text'] + """;
}

QTabBar::tab:hover:!selected {
    background-color: """ + DISCORD_COLORS['secondary_bg'] + """;
}

QPushButton {
    background-color: """ + DISCORD_COLORS['accent'] + """;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: """ + DISCORD_COLORS['accent_hover'] + """;
}

QPushButton:pressed {
    background-color: """ + DISCORD_COLORS['accent'] + """;
}

QComboBox {
    background-color: """ + DISCORD_COLORS['tertiary_bg'] + """;
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    color: """ + DISCORD_COLORS['text'] + """;
    min-width: 150px;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid """ + DISCORD_COLORS['text'] + """;
    margin-right: 8px;
}

QTextEdit {
    background-color: """ + DISCORD_COLORS['tertiary_bg'] + """;
    border: none;
    border-radius: 4px;
    padding: 8px;
    color: """ + DISCORD_COLORS['text'] + """;
    font-family: 'Consolas', 'Courier New', monospace;
}

QLabel {
    color: """ + DISCORD_COLORS['text'] + """;
    font-weight: bold;
}

QScrollBar:vertical {
    border: none;
    background-color: """ + DISCORD_COLORS['tertiary_bg'] + """;
    width: 14px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: """ + DISCORD_COLORS['secondary_bg'] + """;
    min-height: 30px;
    border-radius: 7px;
}

QScrollBar::handle:vertical:hover {
    background-color: """ + DISCORD_COLORS['accent'] + """;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    border: none;
    background: none;
    color: none;
}

QListWidget {
    background-color: """ + DISCORD_COLORS['tertiary_bg'] + """;
    border: none;
    border-radius: 4px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 4px;
}

QListWidget::item:hover {
    background-color: """ + DISCORD_COLORS['secondary_bg'] + """;
}

QListWidget::item:selected {
    background-color: """ + DISCORD_COLORS['accent'] + """;
    color: white;
}
"""

def set_application_style(app):
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Set the custom style sheet
    app.setStyleSheet(STYLE_SHEET)
    
    # Set up dark palette for system dialogs
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(DISCORD_COLORS['background']))
    dark_palette.setColor(QPalette.WindowText, QColor(DISCORD_COLORS['text']))
    dark_palette.setColor(QPalette.Base, QColor(DISCORD_COLORS['tertiary_bg']))
    dark_palette.setColor(QPalette.AlternateBase, QColor(DISCORD_COLORS['secondary_bg']))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(DISCORD_COLORS['text']))
    dark_palette.setColor(QPalette.ToolTipText, QColor(DISCORD_COLORS['text']))
    dark_palette.setColor(QPalette.Text, QColor(DISCORD_COLORS['text']))
    dark_palette.setColor(QPalette.Button, QColor(DISCORD_COLORS['accent']))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(DISCORD_COLORS['accent']))
    dark_palette.setColor(QPalette.Highlight, QColor(DISCORD_COLORS['accent']))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    
    app.setPalette(dark_palette) 