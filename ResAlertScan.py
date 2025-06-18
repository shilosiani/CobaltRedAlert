import requests
import time
import json
import logging

logging.basicConfig(
    filename="alerts.log",      # הקובץ שאליו נרשמים הלוגים
    level=logging.INFO,         # רמת הלוג – INFO ומעלה
    format="%(asctime)s %(levelname)s: %(message)s",  # פורמט עם זמן ורמה
    filemode="a",               # מצב append – לא מוחק קיים
)


def check_alerts():
    print("בודק התראות...")
    url = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        text = response.content.decode('utf-8-sig')
        #print(text)
        if not text:
            print("🟨 קיבלנו תגובה ריקה")
            return []
        if not (text.startswith('[') or text.startswith('{')):
            print("תשובה ריקה:", text[:10])
            return []

        logging.info(f"התקבלה התרעה חדשה:\n{text}")
        data = json.loads(text)
        #print("פורמט JSON:", data)
        titel = data.get("titel", [])
        alerts = data.get("data", [])
        for alert in alerts:
            if alert == "חיפה - מפרץ":
                print("האירוע: ", titel)
                print("התראה:", alert)
            if alert == "מצפה רמון":
                return alert
    except Exception as e:
        print(f"שגיאה בבדיקת התראות: {e}")
    
    return None

def main():
    last_alert = ""
    while True:
        alert = check_alerts()
        if alert and alert != last_alert:
            print(f"התראה חדשה: {alert}")
            last_alert = alert
        else:
            print("אין התראה חדשה.")
        time.sleep(15)

if __name__ == "__main__":
    main()