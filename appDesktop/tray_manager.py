import sys
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal

class TrayManager(QObject):
    """Manages system tray icon and menu"""
    
    # Signals for tray actions
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    toggle_monitoring_requested = pyqtSignal()
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.tray_icon = None
        self.tray_menu = None
        self.is_monitoring = False
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available on this system")
            return
        
        self.setup_tray()
    
    def setup_tray(self):
        """Set up system tray icon and menu"""
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        
        # Set default icon (you can replace this with a proper icon file)
        self.update_tray_icon("🔴")  # Red circle for stopped state
        
        # Create tray menu
        self.tray_menu = QMenu()
        
        # Add menu actions
        self.show_action = QAction("Show Window", self.tray_menu)
        self.show_action.triggered.connect(self.show_window_requested.emit)
        self.tray_menu.addAction(self.show_action)
        
        self.tray_menu.addSeparator()
        
        self.toggle_action = QAction("Start Monitoring", self.tray_menu)
        self.toggle_action.triggered.connect(self.toggle_monitoring_requested.emit)
        self.tray_menu.addAction(self.toggle_action)
        
        self.tray_menu.addSeparator()
        
        self.quit_action = QAction("Exit", self.tray_menu)
        self.quit_action.triggered.connect(self.quit_requested.emit)
        self.tray_menu.addAction(self.quit_action)
        
        # Set menu to tray icon
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Connect double-click to show window
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        # Set tooltip
        self.tray_icon.setToolTip("Red Alert Monitor")
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()
    
    def show_tray(self):
        """Show the tray icon"""
        if self.tray_icon:
            self.tray_icon.show()
    
    def hide_tray(self):
        """Hide the tray icon"""
        if self.tray_icon:
            self.tray_icon.hide()
    
    def update_monitoring_status(self, is_monitoring: bool):
        """Update tray icon based on monitoring status"""
        self.is_monitoring = is_monitoring
        
        if is_monitoring:
            self.update_tray_icon("🟡")  # Yellow circle for monitoring
            self.toggle_action.setText("Stop Monitoring")
            self.tray_icon.setToolTip("Red Alert Monitor - Monitoring Active")
        else:
            self.update_tray_icon("🔴")  # Red circle for stopped
            self.toggle_action.setText("Start Monitoring")
            self.tray_icon.setToolTip("Red Alert Monitor - Monitoring Stopped")
    
    def update_alert_status(self, has_alert: bool):
        """Update tray icon when alert is detected"""
        if has_alert:
            self.update_tray_icon("🚨")  # Alert icon
            self.tray_icon.setToolTip("Red Alert Monitor - ALERT ACTIVE!")
        elif self.is_monitoring:
            self.update_tray_icon("🟢")  # Green circle for active monitoring
            self.tray_icon.setToolTip("Red Alert Monitor - Monitoring Active")
    
    def update_tray_icon(self, emoji: str):
        """Update tray icon with emoji (fallback method)"""
        if not self.tray_icon:
            return
        
        try:
            # For now, we'll use a simple approach with text
            # In a production app, you'd want to use proper icon files
            # This is a simplified version that works across platforms
            
            # Create a simple icon from text (this is a basic implementation)
            # You should replace this with proper icon files (.ico, .png)
            icon = QIcon()  # Empty icon for now
            self.tray_icon.setIcon(icon)
            
        except Exception as e:
            print(f"Error setting tray icon: {e}")
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.MessageIcon.Information, timeout: int = 5000):
        """Show tray notification message"""
        if self.tray_icon and self.tray_icon.supportsMessages():
            self.tray_icon.showMessage(title, message, icon, timeout)
    
    def show_alert_message(self, title: str, cities: list):
        """Show alert message in tray"""
        message = f"Alert in: {', '.join(cities)}"
        self.show_message(
            title=f"🚨 {title}",
            message=message,
            icon=QSystemTrayIcon.MessageIcon.Critical,
            timeout=10000
        )
    
    def show_status_message(self, message: str):
        """Show status message in tray"""
        self.show_message(
            title="Red Alert Monitor",
            message=message,
            icon=QSystemTrayIcon.MessageIcon.Information,
            timeout=3000
        )
    
    def is_available(self) -> bool:
        """Check if system tray is available"""
        return QSystemTrayIcon.isSystemTrayAvailable() and self.tray_icon is not None
    
    def cleanup(self):
        """Clean up tray resources"""
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None 