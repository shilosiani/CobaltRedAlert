import requests
import time
import json
import hashlib
import pygame
import tempfile
import os

MONITORED_AREAS = {"בני ברק"}
SOUND_URL = "https://cdn.pixabay.com/audio/2025/03/05/audio_3f481e8b25.mp3"

class RedAlertMonitor:
    def __init__(self):
        self.last_alert_hash = None
        self.temp_audio_path = None
        
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
                    time.sleep(0.5)
                    
        except Exception as e:
            print(f"Sound error: {e}")
        finally:
            self.cleanup()
    
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
            # text = open("Alerts.json", "r", encoding="utf-8").read()
            text = response.content.decode('utf-8-sig')     
            if not text.strip() or not (text.startswith('[') or text.startswith('{')):
                return False
            
            data = json.loads(text)
            alert_hash = hashlib.md5(text.encode()).hexdigest()
            
            if alert_hash == self.last_alert_hash:
                return False
            
            areas = data.get("data", [])
            relevant_areas = [area for area in areas if area in MONITORED_AREAS]
            
            if relevant_areas:
                print(f"🚨 ALERT: {data.get('title', '')}")
                print(f"📍 Areas: {', '.join(relevant_areas)}")
                self.last_alert_hash = alert_hash
                self.play_sound()
                return True
                
            return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def run(self):
        print("🚨 Red Alert Monitor Started")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                if self.check_alerts():
                    time.sleep(30)
                else:
                    time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped")
        finally:
            self.cleanup()

if __name__ == "__main__":
    RedAlertMonitor().run() 