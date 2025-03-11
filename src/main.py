import sys
import os
from pathlib import Path

def setup_qt_environment():
    """Setup Qt environment variables and paths"""
    try:
        # Get the PyQt5 location
        import PyQt5
        pyqt_path = Path(PyQt5.__file__).parent
        
        # Set environment variables
        os.environ['QT_DEBUG_PLUGINS'] = '1'
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(pyqt_path / 'Qt5' / 'plugins')
        
        # Print debug info
        print(f"PyQt5 path: {pyqt_path}")
        print(f"Plugin path: {os.environ['QT_QPA_PLATFORM_PLUGIN_PATH']}")
        
        # Verify plugin exists
        cocoa_path = pyqt_path / 'Qt5' / 'plugins' / 'platforms' / 'libqcocoa.dylib'
        if cocoa_path.exists():
            print(f"Found cocoa plugin at: {cocoa_path}")
        else:
            print(f"Warning: Could not find cocoa plugin at: {cocoa_path}")
            
            # Try alternate locations
            alt_paths = [
                pyqt_path / 'Qt' / 'plugins' / 'platforms' / 'libqcocoa.dylib',
                Path('/opt/anaconda3/plugins/platforms/libqcocoa.dylib'),
                Path('/opt/anaconda3/lib/python3.11/site-packages/PyQt5/Qt/plugins/platforms/libqcocoa.dylib')
            ]
            
            for path in alt_paths:
                if path.exists():
                    print(f"Found cocoa plugin in alternate location: {path}")
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(path.parent.parent)
                    break
            
    except Exception as e:
        print(f"Error setting up Qt environment: {e}")

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Setup Qt environment before importing PyQt
setup_qt_environment()

from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.main_window import FridaInjectorMainWindow
from utils.themes import set_application_style

def main():
    try:
        # Create application
        app = QApplication(sys.argv)
        set_application_style(app)
        
        window = FridaInjectorMainWindow()
        window.show()
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {e}")
        QMessageBox.critical(None, "Error", f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 