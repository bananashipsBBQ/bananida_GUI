from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtCore import Qt, QTimer
import json

class DataVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.api_calls = []
        self.setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("API Calls Over Time")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        self.series = QLineSeries()
        self.chart.addSeries(self.series)
        
        chart_view = QChartView(self.chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        layout.addWidget(chart_view)
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_chart)
        self.timer.start(1000)  # Update every second
        
    def add_api_call(self, call_data):
        self.api_calls.append({
            'timestamp': time.time(),
            'data': call_data
        })
        
    def update_chart(self):
        # Update chart with new data
        self.series.clear()
        for i, call in enumerate(self.api_calls[-50:]):  # Show last 50 calls
            self.series.append(i, len(call['data'])) 