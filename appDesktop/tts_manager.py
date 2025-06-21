import asyncio
import tempfile
import os
import random
import edge_tts
from typing import List, Optional, Tuple
from PyQt6.QtCore import QObject, QThread, pyqtSignal

class TTSWorker(QThread):
    """Worker thread for TTS operations to avoid blocking the UI"""
    
    finished = pyqtSignal(list, str)  # audio_files, temp_dir
    error = pyqtSignal(str)
    
    def __init__(self, texts: List[str], voice: str):
        super().__init__()
        self.texts = texts
        self.voice = voice
    
    def run(self):
        """Run TTS conversion in background thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_files, temp_dir = loop.run_until_complete(
                self.convert_text_to_speech(self.texts, self.voice)
            )
            loop.close()
            
            if audio_files:
                self.finished.emit(audio_files, temp_dir)
            else:
                self.error.emit("Failed to generate TTS audio")
                
        except Exception as e:
            self.error.emit(f"TTS error: {str(e)}")
    
    async def convert_text_to_speech(self, texts: List[str], voice: str) -> Tuple[List[str], Optional[str]]:
        """Convert Hebrew text to speech using edge-tts"""
        try:
            temp_dir = tempfile.mkdtemp()
            audio_files = []
            
            for idx, text in enumerate(texts):
                if not text.strip():
                    continue
                
                temp_file = os.path.join(temp_dir, f"tts_{idx}.mp3")
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(temp_file)
                audio_files.append(temp_file)
            
            return audio_files, temp_dir
            
        except Exception as e:
            print(f"TTS conversion error: {e}")
            return [], None

class TTSManager(QObject):
    """Manages text-to-speech functionality"""
    
    tts_ready = pyqtSignal(list, str)  # audio_files, temp_dir
    tts_error = pyqtSignal(str)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.worker = None
        self.available_voices = [
            "he-IL-HilaNeural",
            "he-IL-AvriNeural"
        ]
    
    def get_available_voices(self) -> List[str]:
        """Get list of available Hebrew TTS voices"""
        return self.available_voices.copy()
    
    def get_current_voice(self) -> str:
        """Get currently selected TTS voice"""
        return self.config_manager.get("tts_voice", "he-IL-HilaNeural")
    
    def set_voice(self, voice: str):
        """Set TTS voice"""
        if voice in self.available_voices:
            self.config_manager.set("tts_voice", voice)
    
    def get_random_voice(self) -> str:
        """Get a random voice from available voices"""
        return random.choice(self.available_voices)
    
    def generate_tts(self, texts: List[str], use_random_voice: bool = False):
        """Generate TTS audio files for given texts"""
        if not texts or not self.config_manager.get("tts_enabled", True):
            return
        
        # Clean up any existing worker
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        
        # Choose voice
        voice = self.get_random_voice() if use_random_voice else self.get_current_voice()
        
        # Start TTS generation in background thread
        self.worker = TTSWorker(texts, voice)
        self.worker.finished.connect(self.tts_ready.emit)
        self.worker.error.connect(self.tts_error.emit)
        self.worker.start()
    
    def create_alert_texts(self, title: str, description: str) -> List[str]:
        """Create text list for alert announcement"""
        texts = []
        
        if title:
            texts.append(f"התרעה: {title}")
        
        if description:
            texts.append(description)
        
        return texts
    
    def cleanup_temp_files(self, temp_dir: str):
        """Clean up temporary TTS files"""
        try:
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"TTS cleanup error: {e}")
    
    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.config_manager.get("tts_enabled", True)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable TTS"""
        self.config_manager.set("tts_enabled", enabled) 