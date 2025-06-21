import platform
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal

# Try to import platform-specific notification libraries
try:
    if platform.system() == "Windows":
        from plyer import notification as plyer_notification
        PLYER_AVAILABLE = True
    else:
        from plyer import notification as plyer_notification
        PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    plyer_notification = None

class NotificationManager(QObject):
    """Manages system notifications and toast messages"""
    
    notification_sent = pyqtSignal(str)  # Emitted when notification is sent
    notification_error = pyqtSignal(str)  # Emitted when notification fails
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.app_name = "Red Alert Monitor"
        self.app_icon = None  # Can be set to path of icon file
    
    def is_enabled(self) -> bool:
        """Check if notifications are enabled"""
        return self.config_manager.get("notifications_enabled", True)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable notifications"""
        self.config_manager.set("notifications_enabled", enabled)
    
    def show_alert_notification(self, alert_data: Dict[str, Any]):
        """Show notification for red alert"""
        if not self.is_enabled():
            return
        
        title = alert_data.get("title", "התרעה")
        cities = alert_data.get("cities", [])
        description = alert_data.get("description", "")
        
        # Create notification title
        if cities:
            notification_title = f"🚨 Alert in {', '.join(cities)}"
        else:
            notification_title = f"🚨 {title}"
        
        # Create notification message
        notification_message = title
        if description:
            notification_message += f"\n{description}"
        
        self.show_notification(
            title=notification_title,
            message=notification_message,
            timeout=10
        )
    
    def show_status_notification(self, message: str, timeout: int = 5):
        """Show status notification"""
        if not self.is_enabled():
            return
        
        self.show_notification(
            title=self.app_name,
            message=message,
            timeout=timeout
        )
    
    def show_notification(self, title: str, message: str, timeout: int = 5):
        """Show system notification"""
        try:
            if PLYER_AVAILABLE and plyer_notification:
                plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    app_icon=self.app_icon,
                    timeout=timeout
                )
                self.notification_sent.emit(f"Notification sent: {title}")
            else:
                # Fallback: Print to console if no notification system available
                print(f"NOTIFICATION: {title}")
                print(f"MESSAGE: {message}")
                self.notification_sent.emit(f"Console notification: {title}")
                
        except Exception as e:
            error_msg = f"Notification error: {str(e)}"
            self.notification_error.emit(error_msg)
            print(error_msg)
    
    def test_notification(self):
        """Send a test notification"""
        self.show_notification(
            title="Red Alert Monitor - Test",
            message="This is a test notification to verify the system is working properly.",
            timeout=5
        )
    
    def show_monitoring_started(self):
        """Show notification when monitoring starts"""
        self.show_status_notification("🟡 Red Alert monitoring started")
    
    def show_monitoring_stopped(self):
        """Show notification when monitoring stops"""
        self.show_status_notification("🔴 Red Alert monitoring stopped")
    
    def show_error_notification(self, error_message: str):
        """Show error notification"""
        self.show_notification(
            title="Red Alert Monitor - Error",
            message=error_message,
            timeout=8
        )
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get information about notification capabilities"""
        return {
            "platform": platform.system(),
            "plyer_available": PLYER_AVAILABLE,
            "notifications_enabled": self.is_enabled()
        } 
    

