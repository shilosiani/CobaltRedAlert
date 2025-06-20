







import requests
import time
import json
import hashlib
import pygame
import tempfile
import os
import asyncio
import random
import edge_tts

MONITORED_AREAS = {"בני ברק",    "תל אביב - מרכז העיר",   "תל אביב - עבר הירקון"}
SOUND_URL = "https://cdn.pixabay.com/audio/2025/03/05/audio_3f481e8b25.mp3"

class RedAlertMonitor:
    def __init__(self):

        self.last_alert_hash = None
        self.temp_audio_path = None
        
    async def convert_text_to_speech(self, texts):
        """Convert Hebrew text to speech using edge-tts"""
        try:
            
            to_voices_options = ["he-IL-HilaNeural", "he-IL-AvriNeural"]
            voice_name = to_voices_options[random.randint(0, len(to_voices_options) - 1)]
            
            temp_dir = tempfile.mkdtemp()
            audio_files = []
            
            for idx, text in enumerate(texts):
                if not text.strip():
                    continue
                    
                temp_file = os.path.join(temp_dir, f"tts_{idx}.mp3")
                communicate = edge_tts.Communicate(text, voice_name)
                await communicate.save(temp_file)
                audio_files.append(temp_file)
            
            return audio_files, temp_dir
            
        except Exception as e:
            print(f"TTS error: {e}")
            return [], None
    
    def play_tts_files(self, audio_files):
        """Play TTS audio files"""
        try:
            pygame.mixer.init()
            
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    time.sleep(0.4)  # Small pause between segments
                    
        except Exception as e:
            print(f"TTS playback error: {e}")
    
    def cleanup_tts_files(self, temp_dir):
        """Clean up temporary TTS files"""
        try:
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"Cleanup not done - will override ...")
        
    def play_sound(self):

        try:

            response = requests.get(SOUND_URL, timeout=10)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file.write(response.content)
                self.temp_audio_path = tmp_file.name
            
            pygame.mixer.init()
            pygame.mixer.music.load(self.temp_audio_path)
            
            for i in range(3):
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                if i < 2:
                    time.sleep(0.3)
                    
        except Exception as e:
            print(f"Sound error: {e}")
        finally:
            self.cleanup()
    
    async def play_alert_announcement(self, title, description):
        """Play text-to-speech announcement of the alert"""
        try:
            texts_to_speak = []
            
            if title:
                texts_to_speak.append(f"התרעה: {title}")
            
            if description:
                texts_to_speak.append(description)
            
            if not texts_to_speak:
                return
            
            audio_files, temp_dir = await self.convert_text_to_speech(texts_to_speak)
            
            if audio_files:
                self.play_tts_files(audio_files)

                self.play_sound()
                
                self.cleanup_tts_files(temp_dir)
            
        except Exception as e:
            print(f"Announcement error: {e}")
    
    def cleanup(self):
        try:
            pygame.mixer.quit()
            if self.temp_audio_path and os.path.exists(self.temp_audio_path):
                os.unlink(self.temp_audio_path)
                self.temp_audio_path = None
        except:
            pass
    
    def check_alerts(self):
        try:
            url = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            text = response.content.decode('utf-8-sig')

            # "test-for-debug"
            # text = open("Alerts.json", "r", encoding="utf-8").read()

            # print(response.content)

            if not text.strip() or not (text.startswith('[') or text.startswith('{')):
                print("🟩 no alert ...")
                return False
            
            data = json.loads(text)
            alert_hash = hashlib.md5(text.encode()).hexdigest()
            
            if alert_hash == self.last_alert_hash:
                return False
            
            areas = data.get("data", [])
            relevant_areas = [area for area in areas if area in MONITORED_AREAS]
            
            if relevant_areas:
                title = data.get('title', '')
                description = data.get('desc', '')
                
                print(f"🚨 ALERT : {title}")
                print(f"📝 Description : {description}")
                print(f"📍 Areas : {', '.join(relevant_areas)}")
                
                self.last_alert_hash = alert_hash
                
                self.play_sound()
                
                asyncio.run(self.play_alert_announcement(title, description))
                
                return True
                
            return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def run(self):
        
        print("🚨 Red Alert Sound - Press Ctrl+C to stop ..")
        
        try:
            while True:
                if self.check_alerts():
                    time.sleep(25)
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped")
        finally:
            self.cleanup()

if __name__ == "__main__":
    RedAlertMonitor().run() 