"""
Helper methods for the enhanced main window
Contains additional functionality for settings, export, and other features
"""

import csv
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QDate, Qt

class MainWindowHelpers:
    """Helper methods to be mixed into the MainWindow class"""
    
    # Audio Settings Handlers
    def browse_sound_file(self):
        """Browse for custom alert sound file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Alert Sound", "", 
            "Audio Files (*.mp3 *.wav *.ogg);;All Files (*)"
        )
        if file_path:
            self.config_manager.set("alert_sound_file", file_path)
            self.sound_file_label.setText(os.path.basename(file_path))
            self.settings_changed.emit("alert_sound_file", file_path)
    
    def on_tts_speed_changed(self, value):
        """Handle TTS speed change"""
        speed = value / 100.0
        self.config_manager.set("tts_speed", speed)
        self.tts_speed_label.setText(f"{speed:.1f}x")
        self.settings_changed.emit("tts_speed", speed)
    
    def on_random_voice_changed(self, enabled):
        """Handle random voice change"""
        self.config_manager.set("random_voice", enabled)
        self.settings_changed.emit("random_voice", enabled)
    
    def on_notification_duration_changed(self, value):
        """Handle notification duration change"""
        self.config_manager.set("notification_duration", value)
        self.settings_changed.emit("notification_duration", value)
    
    # Export/Import Functions
    def export_settings(self):
        """Export settings to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "red_alert_settings.json",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config_manager.config, f, ensure_ascii=False, indent=2)
                QMessageBox.information(
                    self, "Export Complete", 
                    f"Settings exported successfully to {file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self, "Export Error", 
                    f"Failed to export settings: {str(e)}"
                )
    
    def import_settings(self):
        """Import settings from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", 
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_config = json.load(f)
                
                # Validate and merge settings
                for key, value in imported_config.items():
                    if key in self.config_manager.default_config:
                        self.config_manager.set(key, value)
                
                QMessageBox.information(
                    self, "Import Complete", 
                    "Settings imported successfully. Please restart the application."
                )
            except Exception as e:
                QMessageBox.warning(
                    self, "Import Error", 
                    f"Failed to import settings: {str(e)}"
                )
    
    def export_history_csv(self):
        """Export history to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export History to CSV", "alert_history.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time", "Cities", "Type", "Duration", "Details"])
                    
                    # Export all visible items
                    for i in range(self.history_tree.topLevelItemCount()):
                        item = self.history_tree.topLevelItem(i)
                        if not item.isHidden():
                            row = [item.text(j) for j in range(5)]
                            writer.writerow(row)
                
                QMessageBox.information(
                    self, "Export Complete", 
                    f"History exported successfully to {file_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self, "Export Error", 
                    f"Failed to export CSV: {str(e)}"
                )
    
    def export_history_pdf(self):
        """Export history to PDF - placeholder"""
        QMessageBox.information(
            self, "Export PDF", 
            "PDF export functionality will be implemented in a future version."
        )

# Mix the helper methods into the MainWindow class
def enhance_main_window(main_window_class):
    """Enhance the MainWindow class with helper methods"""
    
    # Copy all methods from MainWindowHelpers to MainWindow
    for method_name in dir(MainWindowHelpers):
        if not method_name.startswith('_'):
            method = getattr(MainWindowHelpers, method_name)
            setattr(main_window_class, method_name, method)
    
    return main_window_class 