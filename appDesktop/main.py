import sys
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('red_alert_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class RedAlertApp(QObject):
    """Main application class that coordinates all components with enhanced Rocket Alert API"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.config_manager = ConfigManager()
        
        # Initialize enhanced alert engine with new API
        self.alert_engine = AlertEngine(self.config_manager)
        self.alert_history = AlertHistory()
        
        # Initialize audio/notification managers
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
        
        # Show main window (unless configured to start minimized)
        if not self.config_manager.get("start_minimized", False):
            self.main_window.show()
        
        # Auto-start monitoring if configured
        if self.config_manager.get("auto_start_monitoring", False):
            QTimer.singleShot(2000, self.auto_start_monitoring)  # Start after 2 seconds
        
        self.logger.info("🚨 Enhanced Red Alert Desktop App initialized successfully!")
        print("🚨 Enhanced Red Alert Desktop App with Rocket Alert API is ready!")
    
    def auto_start_monitoring(self):
        """Auto-start monitoring if configured"""
        try:
            self.toggle_monitoring(True)
            self.logger.info("🚀 Auto-started monitoring")
        except Exception as e:
            self.logger.error(f"Error auto-starting monitoring: {e}")
    
    def connect_signals(self):
        """Connect signals between components"""
        
        # Enhanced alert engine signals
        self.alert_engine.alert_detected.connect(self.on_alert_detected)
        self.alert_engine.status_changed.connect(self.on_status_changed)
        self.alert_engine.error_occurred.connect(self.on_error_occurred)
        self.alert_engine.api_connected.connect(self.on_api_connection_changed)
        
        # Main window signals
        self.main_window.monitoring_toggled.connect(self.toggle_monitoring)
        self.main_window.test_sound_requested.connect(self.test_sound)
        self.main_window.test_notification_requested.connect(self.test_notification)
        self.main_window.test_tts_requested.connect(self.test_tts)
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
        """Handle new alert detection with enhanced processing"""
        cities = alert_data.get("cities", [])
        priority = alert_data.get("priority", 1)
        
        self.logger.info(f"🚨 Alert detected: {cities} (Priority: {priority})")
        print(f"🚨 ALERT DETECTED: {', '.join(cities)} (Priority: {priority})")
        
        # Add to history
        self.alert_history.add_alert(alert_data)
        self.main_window.add_alert_to_history(alert_data)
        
        # Update tray icon with priority indication
        if self.tray_manager.is_available():
            self.tray_manager.update_alert_status(True)
            self.tray_manager.show_alert_message(
                alert_data.get("title", "Alert"),
                cities,
                priority
            )
        
        # Show notification with priority
        self.notification_manager.show_alert_notification(alert_data)
        
        # Generate TTS with priority-based voice selection
        if self.tts_manager.is_enabled():
            title = alert_data.get("title", "")
            description = alert_data.get("description", "")
            cities_text = ", ".join(cities)
            
            # Create enhanced TTS message
            if priority >= 3:
                tts_text = f"התרעה דחופה! צבע אדום באזורים: {cities_text}"
            else:
                tts_text = f"התרעת צבע אדום באזורים: {cities_text}"
            
            texts = self.tts_manager.create_alert_texts(title, tts_text)
            self.tts_manager.generate_tts(texts, use_random_voice=priority < 3)
        
        # Play alert sound with priority-based repetition
        if self.sound_manager.is_sound_enabled():
            repeat_count = min(priority, 3)  # Higher priority = more repetitions
            self.sound_manager.play_alert_sound(repeat_count)
        
        # Schedule status reset based on priority
        reset_delay = 15000 if priority >= 3 else 10000  # High priority alerts show longer
        QTimer.singleShot(reset_delay, self.reset_alert_status)
        
        # Update main window status with enhanced info
        self.main_window.status_widget.update_alert_count(
            self.alert_history.get_history_count()
        )
    
    def reset_alert_status(self):
        """Reset alert status after some time"""
        if self.tray_manager.is_available():
            self.tray_manager.update_alert_status(False)
    
    def on_status_changed(self, status):
        """Handle status changes from alert engine"""
        self.main_window.update_status(status)
        self.logger.info(f"Status: {status}")
        
        # Update tray tooltip with current status
        if self.tray_manager.is_available():
            self.tray_manager.update_tooltip(status)
    
    def on_api_connection_changed(self, connected: bool):
        """Handle API connection status changes"""
        if connected:
            self.logger.info("✅ API Connection established")
            print("✅ Connected to Rocket Alert API")
            if self.tray_manager.is_available():
                self.tray_manager.show_message("API Connected", "Successfully connected to Rocket Alert API")
        else:
            self.logger.warning("❌ API Connection lost")
            print("❌ Disconnected from Rocket Alert API")
            if self.tray_manager.is_available():
                self.tray_manager.show_message("API Disconnected", "Lost connection to Rocket Alert API")
        
        # Update main window connection status
        if hasattr(self.main_window, 'status_widget'):
            self.main_window.status_widget.update_connection_status(connected)
    
    def on_error_occurred(self, error_message):
        """Handle errors from alert engine"""
        self.logger.error(f"Alert Engine Error: {error_message}")
        print(f"❌ Error: {error_message}")
        
        # Show user-friendly error notification
        if "Node.js" in error_message:
            user_message = "Node.js לא מותקן או לא נמצא בנתיב המערכת"
        elif "API" in error_message:
            user_message = "שגיאה בחיבור לשרת ההתראות"
        else:
            user_message = error_message
        
        self.notification_manager.show_error_notification(user_message)
    
    def toggle_monitoring(self, start_monitoring=None):
        """Toggle monitoring state with enhanced feedback"""
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
            print("🟢 Monitoring started")
        else:
            self.notification_manager.show_monitoring_stopped()
            print("🔴 Monitoring stopped")
    
    def toggle_monitoring_from_tray(self):
        """Toggle monitoring from tray menu"""
        self.toggle_monitoring()
        # Update main window button state
        self.main_window.is_monitoring = self.alert_engine.is_monitoring
        if self.alert_engine.is_monitoring:
            self.main_window.start_stop_btn.setText("⏹️ Stop Monitoring")
            self.main_window.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
        else:
            self.main_window.start_stop_btn.setText("▶️ Start Monitoring")
            self.main_window.start_stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
                QPushButton:hover {
                    background-color: #388e3c;
                }
            """)
    
    def test_sound(self):
        """Test sound system with enhanced feedback"""
        self.logger.info("🔊 Testing sound system...")
        print("🔊 Testing sound system...")
        try:
            self.sound_manager.test_alert_sound()
            print("✅ Sound test completed")
        except Exception as e:
            self.logger.error(f"Sound test failed: {e}")
            print(f"❌ Sound test failed: {e}")
    
    def test_notification(self):
        """Test notification system"""
        self.logger.info("📢 Testing notification system...")
        print("📢 Testing notification system...")
        try:
            self.notification_manager.test_notification()
            print("✅ Notification test completed")
        except Exception as e:
            self.logger.error(f"Notification test failed: {e}")
            print(f"❌ Notification test failed: {e}")
    
    def test_tts(self):
        """Test TTS system with enhanced Hebrew support"""
        self.logger.info("🗣️ Testing TTS system...")
        print("🗣️ Testing TTS system...")
        try:
            if self.tts_manager.is_enabled():
                test_message = "זוהי בדיקת מערכת קול של התרעת צבע אדום המשופרת"
                self.tts_manager.generate_tts([test_message], use_random_voice=False)
                print("✅ TTS test initiated")
            else:
                print("⚠️ TTS is disabled")
        except Exception as e:
            self.logger.error(f"TTS test failed: {e}")
            print(f"❌ TTS test failed: {e}")
    
    def on_settings_changed(self, setting_name, value):
        """Handle settings changes from main window"""
        self.logger.info(f"Setting changed: {setting_name} = {value}")
        print(f"⚙️ Setting changed: {setting_name} = {value}")
        
        # Update alert engine if needed
        if setting_name == "check_interval":
            self.alert_engine.update_check_interval(value)
        elif setting_name == "auto_start_monitoring":
            # This will be used on next startup
            pass
    
    def on_tts_ready(self, audio_files, temp_dir):
        """Handle TTS audio files ready"""
        self.logger.info(f"TTS ready: {len(audio_files)} files")
        print(f"🗣️ TTS ready: {len(audio_files)} files")
        try:
            self.sound_manager.play_tts_files(audio_files)
            # Clean up temp files after a delay
            QTimer.singleShot(30000, lambda: self.tts_manager.cleanup_temp_files(temp_dir))
        except Exception as e:
            self.logger.error(f"Error playing TTS files: {e}")
    
    def on_tts_error(self, error_message):
        """Handle TTS errors"""
        self.logger.error(f"TTS Error: {error_message}")
        print(f"❌ TTS Error: {error_message}")
    
    def on_playback_finished(self):
        """Handle playback finished"""
        self.logger.debug("Playback finished")
    
    def on_playback_error(self, error_message):
        """Handle playback errors"""
        self.logger.error(f"Playback Error: {error_message}")
        print(f"❌ Playback Error: {error_message}")
    
    def on_notification_sent(self, message):
        """Handle notification sent"""
        self.logger.debug(f"Notification sent: {message}")
    
    def on_notification_error(self, error_message):
        """Handle notification errors"""
        self.logger.error(f"Notification Error: {error_message}")
        print(f"❌ Notification Error: {error_message}")
    
    def show_window(self):
        """Show main window"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        self.logger.info("Main window shown")
    
    def quit_application(self):
        """Quit the application with proper cleanup"""
        self.logger.info("🚪 Quitting application...")
        print("🚪 Shutting down Red Alert Monitor...")
        
        try:
            # Stop monitoring
            if self.alert_engine.is_monitoring:
                self.alert_engine.stop_monitoring()
            
            # Clean up resources
            self.alert_engine.cleanup()
            self.sound_manager.cleanup()
            
            if self.tray_manager.is_available():
                self.tray_manager.cleanup()
            
            # Save window state and settings
            self.main_window.save_window_state()
            
            # Save alert history
            self.alert_history.save_history()
            
            self.logger.info("✅ Cleanup completed")
            print("✅ Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            print(f"❌ Error during cleanup: {e}")
        
        # Quit application
        QApplication.quit()

def check_prerequisites():
    """Check if Node.js is available"""
    import subprocess
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Node.js found: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js not found")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Node.js not available")
        return False

def main():
    """Main entry point with enhanced error handling"""
    print("🚨 Starting Enhanced Red Alert Desktop Application...")
    print("🔧 Checking prerequisites...")
    
    # Check Node.js availability
    if not check_prerequisites():
        print("⚠️  Node.js is required for the enhanced API functionality")
        print("📥 Please install Node.js from https://nodejs.org/")
        print("🔄 Falling back to basic functionality...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Enhanced Red Alert Monitor")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Red Alert Monitor Enhanced")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.ico"))
    
    # Check for system tray availability
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("⚠️  System tray is not available on this system.")
        print("📱 The application will run in window mode only.")
    
    # Set font for Hebrew text support
    app.setFont(QFont("Arial", 10))
    
    # Apply global qt-material theme if available
    try:
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='light_blue.xml')
        print("✅ Applied modern theme")
    except ImportError:
        print("⚠️  qt-material not available, using fallback styling")
    
    try:
        # Create and run the enhanced application
        red_alert_app = RedAlertApp()
        
        print("🚀 Enhanced Red Alert Monitor is running!")
        print("🎯 Rocket Alert Live API integration active")
        print("📡 Real-time monitoring with advanced features")
        print("🔊 Enhanced audio and notification system")
        print("💾 Persistent alert history")
        print("⚙️  Advanced settings and customization")
        print("🌐 Hebrew and English support")
        print("")
        print("👀 Check the system tray for monitoring controls")
        print("⏹️  Press Ctrl+C to stop")
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"Critical error starting application: {e}")
        print(f"❌ Critical error: {e}")
        
        QMessageBox.critical(
            None,
            "Critical Error",
            f"Failed to start Enhanced Red Alert Monitor:\n{str(e)}\n\n"
            f"Please check the logs for more details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main() 