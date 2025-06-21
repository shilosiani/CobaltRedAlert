import sys
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

# Import our custom modules
from config import ConfigManager
from alert_engine import AlertEngine, AlertHistory
from tts_manager import TTSManager
from sound_manager import SoundManager
from notifications import NotificationManager
from tray_manager import TrayManager
from main_window import MainWindow

class RedAlertApp(QObject):
    """Main application class that coordinates all components"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Initialize core components
        self.alert_engine = AlertEngine(self.config_manager)
        self.alert_history = AlertHistory()
        self.tts_manager = TTSManager(self.config_manager)
        self.sound_manager = SoundManager(self.config_manager)
        self.notification_manager = NotificationManager(self.config_manager)
        
        # Initialize GUI components
        self.main_window = MainWindow(self.config_manager)
        self.tray_manager = TrayManager(self.config_manager)
        
        # Connect signals
        self.connect_signals()
        
        # Show tray icon
        if self.tray_manager.is_available():
            self.tray_manager.show_tray()
        
        # Show main window
        self.main_window.show()
        
        print("🚨 Red Alert Desktop App initialized successfully!")
    
    def connect_signals(self):
        """Connect signals between components"""
        
        # Alert engine signals
        self.alert_engine.alert_detected.connect(self.on_alert_detected)
        self.alert_engine.status_changed.connect(self.on_status_changed)
        self.alert_engine.error_occurred.connect(self.on_error_occurred)
        
        # Main window signals
        self.main_window.monitoring_toggled.connect(self.toggle_monitoring)
        self.main_window.test_sound_requested.connect(self.test_sound)
        self.main_window.test_notification_requested.connect(self.test_notification)
        self.main_window.settings_changed.connect(self.on_settings_changed)
        
        # TTS Manager signals
        self.tts_manager.tts_ready.connect(self.on_tts_ready)
        self.tts_manager.tts_error.connect(self.on_tts_error)
        
        # Sound Manager signals
        self.sound_manager.playback_finished.connect(self.on_playback_finished)
        self.sound_manager.playback_error.connect(self.on_playback_error)
        
        # Tray Manager signals
        if self.tray_manager.is_available():
            self.tray_manager.show_window_requested.connect(self.show_window)
            self.tray_manager.quit_requested.connect(self.quit_application)
            self.tray_manager.toggle_monitoring_requested.connect(self.toggle_monitoring_from_tray)
        
        # Notification Manager signals
        self.notification_manager.notification_sent.connect(self.on_notification_sent)
        self.notification_manager.notification_error.connect(self.on_notification_error)
    
    def on_alert_detected(self, alert_data):
        """Handle new alert detection"""
        print(f"🚨 Alert detected: {alert_data}")
        
        # Add to history
        self.alert_history.add_alert(alert_data)
        self.main_window.add_alert_to_history(alert_data)
        
        # Update tray icon
        if self.tray_manager.is_available():
            self.tray_manager.update_alert_status(True)
            self.tray_manager.show_alert_message(
                alert_data.get("title", "Alert"),
                alert_data.get("cities", [])
            )
        
        # Show notification
        self.notification_manager.show_alert_notification(alert_data)
        
        # Generate TTS
        if self.tts_manager.is_enabled():
            title = alert_data.get("title", "")
            description = alert_data.get("description", "")
            texts = self.tts_manager.create_alert_texts(title, description)
            self.tts_manager.generate_tts(texts, use_random_voice=True)
        
        # Play alert sound
        if self.sound_manager.is_sound_enabled():
            self.sound_manager.play_alert_sound()
        
        # Schedule status reset
        QTimer.singleShot(10000, self.reset_alert_status)  # Reset after 10 seconds
    
    def reset_alert_status(self):
        """Reset alert status after some time"""
        if self.tray_manager.is_available():
            self.tray_manager.update_alert_status(False)
    
    def on_status_changed(self, status):
        """Handle status changes from alert engine"""
        self.main_window.update_status(status)
        print(f"Status: {status}")
    
    def on_error_occurred(self, error_message):
        """Handle errors from alert engine"""
        print(f"Error: {error_message}")
        self.notification_manager.show_error_notification(error_message)
    
    def toggle_monitoring(self, start_monitoring=None):
        """Toggle monitoring state"""
        if start_monitoring is None:
            # Toggle current state
            if self.alert_engine.is_monitoring:
                self.alert_engine.stop_monitoring()
            else:
                self.alert_engine.start_monitoring()
        else:
            # Set specific state
            if start_monitoring:
                self.alert_engine.start_monitoring()
            else:
                self.alert_engine.stop_monitoring()
        
        # Update tray icon
        if self.tray_manager.is_available():
            self.tray_manager.update_monitoring_status(self.alert_engine.is_monitoring)
        
        # Show notification
        if self.alert_engine.is_monitoring:
            self.notification_manager.show_monitoring_started()
        else:
            self.notification_manager.show_monitoring_stopped()
    
    def toggle_monitoring_from_tray(self):
        """Toggle monitoring from tray menu"""
        self.toggle_monitoring()
        # Also update main window button state
        self.main_window.is_monitoring = self.alert_engine.is_monitoring
        if self.alert_engine.is_monitoring:
            self.main_window.start_stop_btn.setText("Stop Monitoring")
            self.main_window.start_stop_btn.setStyleSheet("background-color: #f44336;")
        else:
            self.main_window.start_stop_btn.setText("Start Monitoring")
            self.main_window.start_stop_btn.setStyleSheet("background-color: #4caf50;")
    
    def test_sound(self):
        """Test sound system"""
        print("Testing sound system...")
        self.sound_manager.test_alert_sound()
    
    def test_notification(self):
        """Test notification system"""
        print("Testing notification system...")
        self.notification_manager.test_notification()
    
    def on_settings_changed(self, setting_name, value):
        """Handle settings changes from main window"""
        print(f"Setting changed: {setting_name} = {value}")
        
        # Update alert engine if needed
        if setting_name == "check_interval":
            self.alert_engine.update_check_interval(value)
    
    def on_tts_ready(self, audio_files, temp_dir):
        """Handle TTS audio files ready"""
        print(f"TTS ready: {len(audio_files)} files")
        self.sound_manager.play_tts_files(audio_files)
        # Clean up temp files after a delay
        QTimer.singleShot(30000, lambda: self.tts_manager.cleanup_temp_files(temp_dir))
    
    def on_tts_error(self, error_message):
        """Handle TTS errors"""
        print(f"TTS Error: {error_message}")
    
    def on_playback_finished(self):
        """Handle playback finished"""
        print("Playback finished")
    
    def on_playback_error(self, error_message):
        """Handle playback errors"""
        print(f"Playback Error: {error_message}")
    
    def on_notification_sent(self, message):
        """Handle notification sent"""
        print(f"Notification sent: {message}")
    
    def on_notification_error(self, error_message):
        """Handle notification errors"""
        print(f"Notification Error: {error_message}")
    
    def show_window(self):
        """Show main window"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    def quit_application(self):
        """Quit the application"""
        print("Quitting application...")
        
        # Stop monitoring
        if self.alert_engine.is_monitoring:
            self.alert_engine.stop_monitoring()
        
        # Clean up resources
        self.sound_manager.cleanup()
        
        if self.tray_manager.is_available():
            self.tray_manager.cleanup()
        
        # Save window state
        self.main_window.save_window_state()
        
        # Quit application
        QApplication.quit()

def main():
    """Main entry point"""
    print("🚨 Starting Red Alert Desktop Application...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Red Alert Monitor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Red Alert Monitor")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.ico"))
    
    # Check for system tray availability
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "System Tray",
            "System tray is not available on this system."
        )
    
    # Set font for Hebrew text support
    app.setFont(QFont("Arial", 10))
    
    # Apply global qt-material theme if available
    try:
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='light_blue.xml')
        print("✅ Applied qt-material theme")
    except ImportError:
        print("⚠️ qt-material not available, using fallback styling")
    
    try:
        # Create and run the application
        red_alert_app = RedAlertApp()
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Error starting application: {e}")
        QMessageBox.critical(
            None,
            "Error",
            f"Failed to start application:\n{str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main() 