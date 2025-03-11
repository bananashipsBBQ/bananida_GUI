from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import psutil
import frida
import weakref

class ProcessMonitor(QObject):
    process_started = pyqtSignal(str, int)  # name, pid
    process_ended = pyqtSignal(str, int)    # name, pid
    memory_updated = pyqtSignal(str, float) # pid, memory_usage
    
    def __init__(self, refresh_rate=1000):
        super().__init__()
        self.refresh_rate = refresh_rate
        self.monitored_processes = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_processes)
        self._stopped = False
        
    def start_monitoring(self):
        self._stopped = False
        self.timer.start(self.refresh_rate)
        
    def stop_monitoring(self):
        self._stopped = True
        self.timer.stop()
        self.monitored_processes.clear()  # Clear the dictionary
        
    def check_processes(self):
        if self._stopped:
            return
            
        current_processes = {}
        
        try:
            device = frida.get_local_device()
            # Use iterator instead of list comprehension
            for process in device.enumerate_processes():
                if self._stopped:
                    return
                    
                current_processes[process.pid] = process.name
                
                # New process
                if process.pid not in self.monitored_processes:
                    self.process_started.emit(process.name, process.pid)
                
                # Update memory usage
                try:
                    p = psutil.Process(process.pid)
                    memory_mb = p.memory_info().rss / 1024 / 1024
                    self.memory_updated.emit(str(process.pid), memory_mb)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            # Check for ended processes - use iterator
            for pid in list(self.monitored_processes.keys()):
                if pid not in current_processes:
                    name = self.monitored_processes[pid]
                    self.process_ended.emit(name, pid)
                    
            self.monitored_processes = current_processes
            
        except Exception as e:
            print(f"Error monitoring processes: {str(e)}")
            
    def __del__(self):
        self.stop_monitoring()