import pygame
import requests
import tempfile
import os
import time
from typing import List, Optional
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class SoundPlayer(QThread):
    """Worker thread for sound playback to avoid blocking the UI"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, audio_files: List[str], volume: float = 0.8, repeat_count: int = 1):
        super().__init__()
        self.audio_files = audio_files
        self.volume = volume
        self.repeat_count = repeat_count
        self.should_stop = False
    
    def stop_playback(self):
        """Stop playback"""
        self.should_stop = True
    
    def run(self):
        """Run sound playback in background thread"""
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            
            for audio_file in self.audio_files:
                if self.should_stop:
                    break
                    
                if os.path.exists(audio_file):
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    
                    while pygame.mixer.music.get_busy() and not self.should_stop:
                        time.sleep(0.1)
                    
                    if not self.should_stop:
                        time.sleep(0.4)  # Small pause between segments
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Sound playback error: {str(e)}")
        finally:
            try:
                pygame.mixer.quit()
            except:
                pass

class AlertSoundPlayer(QThread):
    """Worker thread for alert sound playback with repeat functionality"""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, sound_url: str, volume: float = 0.8, repeat_count: int = 3):
        super().__init__()
        self.sound_url = sound_url
        self.volume = volume
        self.repeat_count = repeat_count
        self.should_stop = False
        self.temp_audio_path = None
    
    def stop_playback(self):
        """Stop playback"""
        self.should_stop = True
    
    def run(self):
        """Run alert sound playback in background thread"""
        try:
            # Download sound file
            response = requests.get(self.sound_url, timeout=10)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.content)
                self.temp_audio_path = tmp_file.name
            
            # Play sound
            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.load(self.temp_audio_path)
            
            for i in range(self.repeat_count):
                if self.should_stop:
                    break
                    
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy() and not self.should_stop:
                    time.sleep(0.1)
                
                if i < self.repeat_count - 1 and not self.should_stop:
                    time.sleep(0.3)
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Alert sound error: {str(e)}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            pygame.mixer.quit()
            if self.temp_audio_path and os.path.exists(self.temp_audio_path):
                os.unlink(self.temp_audio_path)
                self.temp_audio_path = None
        except:
            pass

class SoundManager(QObject):
    """Manages sound playback functionality"""
    
    playback_finished = pyqtSignal()
    playback_error = pyqtSignal(str)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.tts_player = None
        self.alert_player = None
        self.default_sound_urls = [
            "https://cdn.pixabay.com/audio/2025/03/05/audio_3f481e8b25.mp3",
            # "https://www.soundjay.com/misc/sounds/beep-07.wav",
            # "https://www.soundjay.com/misc/sounds/beep-10.wav"
        ]
    
    def get_volume(self) -> float:
        """Get current volume setting"""
        return self.config_manager.get("volume", 0.8)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        self.config_manager.set("volume", volume)
    
    def get_alert_sound_url(self) -> str:
        """Get current alert sound URL"""
        return self.config_manager.get("alert_sound_url", self.default_sound_urls[0])
    
    def set_alert_sound_url(self, url: str):
        """Set alert sound URL"""
        self.config_manager.set("alert_sound_url", url)
    
    def get_available_sounds(self) -> List[str]:
        """Get list of available sound URLs"""
        return self.default_sound_urls.copy()
    
    def play_tts_files(self, audio_files: List[str]):
        """Play TTS audio files"""
        if not audio_files or not self.is_sound_enabled():
            return
        
        # Stop any existing TTS playback
        if self.tts_player and self.tts_player.isRunning():
            self.tts_player.stop_playback()
            self.tts_player.wait()
        
        # Start new TTS playback
        self.tts_player = SoundPlayer(audio_files, self.get_volume())
        self.tts_player.finished.connect(self.playback_finished.emit)
        self.tts_player.error.connect(self.playback_error.emit)
        self.tts_player.start()
    
    def play_alert_sound(self, repeat_count: int = 3):
        """Play alert sound"""
        if not self.is_sound_enabled():
            return
        
        # Stop any existing alert sound playback
        if self.alert_player and self.alert_player.isRunning():
            self.alert_player.stop_playback()
            self.alert_player.wait()
        
        # Start new alert sound playback
        sound_url = self.get_alert_sound_url()
        self.alert_player = AlertSoundPlayer(sound_url, self.get_volume(), repeat_count)
        self.alert_player.finished.connect(self.playback_finished.emit)
        self.alert_player.error.connect(self.playback_error.emit)
        self.alert_player.start()
    
    def stop_all_sounds(self):
        """Stop all sound playback"""
        if self.tts_player and self.tts_player.isRunning():
            self.tts_player.stop_playback()
        
        if self.alert_player and self.alert_player.isRunning():
            self.alert_player.stop_playback()
    
    def test_alert_sound(self):
        """Test the current alert sound"""
        self.play_alert_sound(1)  # Play once for testing
    
    def is_sound_enabled(self) -> bool:
        """Check if sound is enabled"""
        return self.config_manager.get("sound_enabled", True)
    
    def set_sound_enabled(self, enabled: bool):
        """Enable or disable sound"""
        self.config_manager.set("sound_enabled", enabled)
        if not enabled:
            self.stop_all_sounds()
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_all_sounds()
        
        if self.tts_player:
            self.tts_player.wait()
        
        if self.alert_player:
            self.alert_player.wait() 