import json
import hashlib
import time
from typing import List, Dict, Any, Callable, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from python_red_alert.main import RedAlert

class AlertEngine(QObject):
    """Core alert monitoring engine with Qt signals for GUI integration"""
    
    # Qt signals for GUI communication
    alert_detected = pyqtSignal(dict)  # Emitted when new alert is detected
    status_changed = pyqtSignal(str)   # Emitted when status changes
    error_occurred = pyqtSignal(str)   # Emitted when error occurs
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.red_alert = RedAlert()
        self.last_alert_hash = None
        self.is_monitoring = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alerts)
        
    def start_monitoring(self):
        """Start alert monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            interval = self.config_manager.get("check_interval", 3) * 1000  # Convert to milliseconds
            self.timer.start(interval)
            self.status_changed.emit("🟡 Monitoring active...")
            print("Alert monitoring started")
    
    def stop_monitoring(self):
        """Stop alert monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.timer.stop()
            self.status_changed.emit("🔴 Monitoring stopped")
            print("Alert monitoring stopped")
    
    def update_check_interval(self, seconds: int):
        """Update the check interval"""
        if self.is_monitoring:
            self.timer.setInterval(seconds * 1000)
    
    def check_alerts(self):
        """Check for new alerts"""
        try:
            # Get alerts using the python-red-alert library
            alerts = self.red_alert.get_red_alerts()
            
            if not alerts:
                self.status_changed.emit("🟢 No alerts currently")
                return
            
            # Create hash from the alerts data to check for changes
            alert_text = json.dumps(alerts, sort_keys=True, ensure_ascii=False)
            alert_hash = hashlib.md5(alert_text.encode()).hexdigest()
            
            if alert_hash == self.last_alert_hash:
                return
            
            # Check if any alert is for our monitored areas
            monitored_cities = set(self.config_manager.get_monitored_cities())
            relevant_alerts = []
            
            for alert in alerts:
                areas = alert.get("cities", [])
                for area in areas:
                    if area in monitored_cities:
                        relevant_alerts.append(alert)
                        break
            
            if relevant_alerts:
                # Process the first relevant alert
                alert = relevant_alerts[0]
                title = alert.get("title", "התרעה")
                desc = alert.get("desc", "")
                areas = alert.get("cities", [])
                relevant_areas = [area for area in areas if area in monitored_cities]
                
                alert_data = {
                    "title": title,
                    "description": desc,
                    "cities": relevant_areas,
                    "all_cities": areas,
                    "timestamp": time.time(),
                    "raw_alert": alert
                }
                
                self.last_alert_hash = alert_hash
                self.status_changed.emit(f"🚨 ALERT in {', '.join(relevant_areas)}")
                self.alert_detected.emit(alert_data)
                
                print(f"🚨 ALERT: {title}")
                print(f"📝 Description: {desc}")
                print(f"📍 Areas: {', '.join(relevant_areas)}")
                
        except Exception as e:
            error_msg = f"Error checking alerts: {e}"
            self.error_occurred.emit(error_msg)
            print(error_msg)

class AlertHistory:
    """Manages alert history and logging"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
    
    def add_alert(self, alert_data: Dict[str, Any]):
        """Add alert to history"""
        self.history.insert(0, alert_data)  # Add to beginning
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]  # Keep only max_history items
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.history[:count]
    
    def clear_history(self):
        """Clear alert history"""
        self.history.clear()
    
    def get_history_count(self) -> int:
        """Get total number of alerts in history"""
        return len(self.history) 