import json
import hashlib
import time
import logging
from typing import List, Dict, Any, Callable, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from rocket_api_bridge import RocketAPIBridge

class AlertEngine(QObject):
    """Enhanced alert monitoring engine using Rocket Alert Live API"""
    
    # Qt signals for GUI communication
    alert_detected = pyqtSignal(dict)  # Emitted when new alert is detected
    status_changed = pyqtSignal(str)   # Emitted when status changes
    error_occurred = pyqtSignal(str)   # Emitted when error occurs
    api_connected = pyqtSignal(bool)   # Emitted when API connection status changes
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize the Rocket Alert API bridge
        self.api_bridge = RocketAPIBridge(config_manager)
        
        # Connect API bridge signals
        self.api_bridge.new_alerts.connect(self.process_new_alerts)
        self.api_bridge.api_error.connect(self.on_api_error)
        self.api_bridge.connection_status_changed.connect(self.on_connection_status_changed)
        
        # Alert tracking
        self.last_alert_hash = None
        self.processed_alert_ids = set()
        self.is_monitoring = False
        
        # Stats tracking
        self.total_alerts_today = 0
        self.connection_status = False
        
        # Periodic stats update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(30000)  # Update stats every 30 seconds
        
        self.logger.info("🚀 Enhanced Alert Engine initialized with Rocket Alert API")
    
    def start_monitoring(self):
        """Start alert monitoring using the new API"""
        if not self.is_monitoring:
            self.is_monitoring = True
            
            if self.api_bridge.start_monitoring():
                self.status_changed.emit("🟡 מפעיל מערכת ניטור...")
                self.logger.info("✅ Alert monitoring started successfully")
            else:
                self.is_monitoring = False
                self.status_changed.emit("❌ שגיאה בהפעלת מערכת הניטור")
                self.error_occurred.emit("Failed to start monitoring - Node.js not available or API error")
    
    def stop_monitoring(self):
        """Stop alert monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.api_bridge.stop_monitoring()
            self.status_changed.emit("🔴 מערכת ניטור מופסקת")
            self.logger.info("🛑 Alert monitoring stopped")
    
    def update_check_interval(self, seconds: int):
        """Update the check interval (for compatibility)"""
        # The new API bridge handles intervals internally
        self.logger.info(f"Check interval setting updated to {seconds}s (handled by API bridge)")
    
    def process_new_alerts(self, alerts: List[Dict]):
        """Process new alerts from the API bridge"""
        if not alerts:
            return
        
        # Get monitored cities
        monitored_cities = set(self.config_manager.get_monitored_cities())
        if not monitored_cities:
            self.logger.warning("No cities are being monitored")
            return
        
        relevant_alerts = []
        
        for alert in alerts:
            # Skip if already processed
            alert_id = alert.get('id', '')
            if alert_id in self.processed_alert_ids:
                continue
            
            # Check if alert is for monitored cities
            alert_cities = alert.get('cities', [])
            
            # Check both Hebrew and English names
            relevant_cities = []
            for city in alert_cities:
                if city in monitored_cities:
                    relevant_cities.append(city)
                    continue
                
                # Also check if any monitored city is contained in this alert city
                for monitored_city in monitored_cities:
                    if (monitored_city.lower() in city.lower() or 
                        city.lower() in monitored_city.lower()):
                        relevant_cities.append(city)
                        break
            
            if relevant_cities:
                # Enhance alert data
                enhanced_alert = {
                    'id': alert_id,
                    'title': alert.get('title', 'התרעת צבע אדום'),
                    'description': alert.get('description', ''),
                    'cities': relevant_cities,
                    'all_cities': alert_cities,
                    'timestamp': alert.get('timestamp', time.time()),
                    'alertType': alert.get('alertType', 1),
                    'duration': alert.get('duration', '90 שניות'),
                    'priority': self.calculate_alert_priority(relevant_cities),
                    'raw_data': alert.get('raw_data', {})
                }
                
                relevant_alerts.append(enhanced_alert)
                self.processed_alert_ids.add(alert_id)
        
        # Process relevant alerts
        if relevant_alerts:
            # Sort by priority (high priority first)
            relevant_alerts.sort(key=lambda x: x.get('priority', 1), reverse=True)
            
            for alert in relevant_alerts:
                self.logger.info(f"🚨 Processing alert for: {', '.join(alert['cities'])}")
                self.status_changed.emit(f"🚨 התרעה: {', '.join(alert['cities'])}")
                self.alert_detected.emit(alert)
                
                # Add small delay between alerts to prevent overwhelming
                time.sleep(0.5)
            
            # Update stats
            self.total_alerts_today += len(relevant_alerts)
        
        # Clean up old processed IDs (keep only last 100)
        if len(self.processed_alert_ids) > 100:
            ids_list = list(self.processed_alert_ids)
            self.processed_alert_ids = set(ids_list[-50:])  # Keep last 50
    
    def calculate_alert_priority(self, cities: List[str]) -> int:
        """Calculate alert priority based on monitored cities priorities"""
        max_priority = 1
        
        for city in cities:
            city_priority = self.config_manager.get(f"city_priority_{city}", 1)
            max_priority = max(max_priority, city_priority)
        
        return max_priority
    
    def on_api_error(self, error_message: str):
        """Handle API errors"""
        self.logger.error(f"API Error: {error_message}")
        self.error_occurred.emit(f"שגיאת API: {error_message}")
        self.status_changed.emit("⚠️ שגיאה בחיבור ל-API")
    
    def on_connection_status_changed(self, connected: bool):
        """Handle connection status changes"""
        self.connection_status = connected
        self.api_connected.emit(connected)
        
        if connected:
            self.status_changed.emit("🟢 מחובר ל-API")
            self.logger.info("✅ Connected to Rocket Alert API")
        else:
            self.status_changed.emit("🔴 מנותק מ-API")
            self.logger.warning("❌ Disconnected from Rocket Alert API")
    
    def update_stats(self):
        """Update statistics from the API"""
        if self.connection_status and self.is_monitoring:
            # Request updated statistics
            self.api_bridge.get_daily_stats()
            self.api_bridge.get_most_targeted_locations(10)
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Get current API statistics"""
        return {
            'connected': self.connection_status,
            'monitoring': self.is_monitoring,
            'total_alerts_today': self.total_alerts_today,
            'processed_alerts': len(self.processed_alert_ids)
        }
    
    def force_check(self):
        """Force immediate check for alerts"""
        if self.connection_status:
            self.api_bridge.get_most_recent_alert()
            self.status_changed.emit("🔄 בודק התראות...")
            self.logger.info("🔄 Force checking for alerts")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_monitoring()
        self.api_bridge.cleanup()
        self.stats_timer.stop()

class AlertHistory:
    """Enhanced alert history management with better filtering and persistence"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        
        # Load existing history if available
        self.load_history()
    
    def add_alert(self, alert_data: Dict[str, Any]):
        """Add alert to history with enhanced data"""
        import datetime
        
        # Enhance alert data with additional metadata
        enhanced_alert = {
            **alert_data,
            'added_timestamp': datetime.datetime.now().isoformat(),
            'day_of_year': datetime.datetime.now().strftime('%Y-%j'),
            'hour': datetime.datetime.now().hour
        }
        
        self.history.insert(0, enhanced_alert)  # Add to beginning
        
        # Maintain max history size
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
        
        # Save to file periodically
        if len(self.history) % 10 == 0:  # Save every 10 alerts
            self.save_history()
        
        self.logger.info(f"📝 Alert added to history: {alert_data.get('cities', ['Unknown'])}")
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.history[:count]
    
    def get_alerts_by_city(self, city: str, count: int = 50) -> List[Dict[str, Any]]:
        """Get alerts for a specific city"""
        city_alerts = []
        for alert in self.history:
            if city in alert.get('cities', []) or city in alert.get('all_cities', []):
                city_alerts.append(alert)
                if len(city_alerts) >= count:
                    break
        return city_alerts
    
    def get_daily_stats(self, days: int = 7) -> Dict[str, int]:
        """Get daily alert statistics"""
        import datetime
        
        stats = {}
        today = datetime.datetime.now()
        
        for i in range(days):
            date = today - datetime.timedelta(days=i)
            day_key = date.strftime('%Y-%j')
            stats[date.strftime('%Y-%m-%d')] = 0
            
            for alert in self.history:
                if alert.get('day_of_year') == day_key:
                    stats[date.strftime('%Y-%m-%d')] += 1
        
        return stats
    
    def clear_history(self):
        """Clear alert history"""
        self.history.clear()
        self.save_history()
        self.logger.info("🗑️ Alert history cleared")
    
    def get_history_count(self) -> int:
        """Get total number of alerts in history"""
        return len(self.history)
    
    def save_history(self):
        """Save history to file"""
        try:
            import os
            history_file = os.path.join(os.path.dirname(__file__), 'alert_history.json')
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history[:100], f, ensure_ascii=False, indent=2)  # Save last 100 alerts
            
        except Exception as e:
            self.logger.error(f"Error saving history: {e}")
    
    def load_history(self):
        """Load history from file"""
        try:
            import os
            history_file = os.path.join(os.path.dirname(__file__), 'alert_history.json')
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                self.logger.info(f"📂 Loaded {len(self.history)} alerts from history")
            
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            self.history = [] 