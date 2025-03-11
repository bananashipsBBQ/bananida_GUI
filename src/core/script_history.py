import json
import os
from datetime import datetime

class ScriptHistory:
    def __init__(self):
        self.base_dir = os.path.join(os.path.expanduser('~'), '.frida_gui')
        self.history_file = os.path.join(self.base_dir, 'script_history.json')
        self.favorites_file = os.path.join(self.base_dir, 'favorites.json')
        self.ensure_dirs()
        self.load_history()
        
    def ensure_dirs(self):
        os.makedirs(self.base_dir, exist_ok=True)
        
    def load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            else:
                self.history = {
                    'local': [],
                    'codeshare': [],
                    'favorites': []
                }
        except Exception as e:
            print(f"Error loading history: {e}")
            self.history = {'local': [], 'codeshare': [], 'favorites': []}
            
    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
            
    def add_to_history(self, script_type, script_info):
        """Add script to history with timestamp"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'info': script_info
        }
        
        # Keep only last 50 entries
        self.history[script_type] = ([entry] + 
                                   [x for x in self.history[script_type] 
                                    if x['info'].get('id') != script_info.get('id')])[:50]
        self.save_history()
        
    def add_to_favorites(self, script_info):
        """Add script to favorites"""
        if script_info not in self.history['favorites']:
            self.history['favorites'].append(script_info)
            self.save_history()
            
    def remove_from_favorites(self, script_id):
        """Remove script from favorites"""
        self.history['favorites'] = [
            x for x in self.history['favorites'] 
            if x.get('id') != script_id
        ]
        self.save_history()
        
    def get_recent_scripts(self, script_type, limit=10):
        """Get recent scripts of specified type"""
        return self.history[script_type][:limit]
        
    def get_favorites(self):
        """Get all favorite scripts"""
        return self.history['favorites']
        
    def is_favorite(self, script_id):
        """Check if script is in favorites"""
        return any(x.get('id') == script_id 
                  for x in self.history['favorites']) 