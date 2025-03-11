from datetime import datetime
import json
import os
from collections import deque
import weakref

class HistoryManager:
    def __init__(self):
        self.history_file = os.path.join(os.path.expanduser('~'), '.frida_gui', 'history.json')
        self._history = deque(maxlen=1000)  # Limit history size
        self.load_history()
        
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    # Load directly into deque with max size
                    data = json.load(f)
                    self._history.extend(data[-1000:])  # Only keep last 1000 entries
        except Exception as e:
            print(f"Error loading history: {e}")
            
    def save_history(self):
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w') as f:
                # Convert deque to list for JSON serialization
                json.dump(list(self._history), f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def add_entry(self, action_type, details):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': action_type,
            'details': details
        }
        self._history.appendleft(entry)  # Use deque's appendleft
        
        # Periodically save to prevent memory buildup
        if len(self._history) % 10 == 0:  # Save every 10 entries
            self.save_history()
            
    def clear_history(self):
        self._history.clear()
        self.save_history()
        
    @property
    def history(self):
        return list(self._history)  # Return a copy to prevent memory leaks
        
    def __del__(self):
        self.save_history()