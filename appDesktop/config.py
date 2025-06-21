import json
import os
from typing import List, Dict, Any

class ConfigManager:
    """Manages application configuration and user settings"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.default_config = {
            # City monitoring
            "monitored_cities": ["בני ברק", "מודיעין עילית"],
            
            # Audio settings
            "tts_voice": "he-IL-HilaNeural",
            "tts_enabled": True,
            "tts_speed": 1.0,
            "random_voice": False,
            "sound_enabled": True,
            "volume": 0.8,
            "alert_sound_file": "",
            
            # Monitoring settings
            "check_interval": 3,
            "alert_pause_time": 25,
            "auto_start_monitoring": False,
            "connection_timeout": 10,
            "max_retries": 3,
            "priority_monitoring": True,
            "alert_level_filter": "All Alerts",
            "prevent_duplicates": True,
            
            # Notification settings
            "notifications_enabled": True,
            "notification_duration": 5,
            
            # Interface settings
            "theme": "Light Blue",
            "font_size": 11,
            "language": "he",
            "minimize_to_tray": True,
            "close_to_tray": True,
            "start_minimized": False,
            "always_on_top": False,
            "high_contrast": False,
            "large_fonts": False,
            
            # Window settings
            "window_position": {"x": 100, "y": 100},
            "window_size": {"width": 800, "height": 600},
            
            # Advanced settings
            "data_retention_days": 30,
            "auto_backup": True,
            "log_level": "INFO",
            "log_to_file": True,
            
            # Legacy
            "autorun": False,
            "alert_sound_url": "https://cdn.pixabay.com/audio/2025/03/05/audio_3f481e8b25.mp3"
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
    
    def add_monitored_city(self, city: str):
        """Add city to monitoring list"""
        if city not in self.config["monitored_cities"]:
            self.config["monitored_cities"].append(city)
            self.save_config()
    
    def remove_monitored_city(self, city: str):
        """Remove city from monitoring list"""
        if city in self.config["monitored_cities"]:
            self.config["monitored_cities"].remove(city)
            self.save_config()
    
    def get_monitored_cities(self) -> List[str]:
        """Get list of monitored cities"""
        return self.config.get("monitored_cities", [])
    
    def get_tts_voices(self) -> List[str]:
        """Get available TTS voices"""
        return ["he-IL-HilaNeural", "he-IL-AvriNeural"] 