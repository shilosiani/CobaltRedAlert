import requests
import time
import json
import logging
from datetime import datetime
import pytz
import re

logging.basicConfig(
    filename="alerts.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    filemode="a",
)

ALLOWED_AREAS = {
    "תל אביב - דרום העיר ויפו",
    "תל אביב - מזרח",
    "תל אביב - מרכז העיר",
    "תל אביב - עבר הירקון"
}

def send_sms(message_text):
    url = "https://019sms.co.il/api"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_TOKEN_HERE"
    }

    data = {
        "sms": {
            "user": {
                "username": "YOUR_USERNAME"
            },
            "source": "YOUR_SENDER",
            "destinations": {
                "cl_id": [
                        "YOUR_CL_ID"
                ]
            },
            "phone": [
        {
          "$": {
            "id": "external id1"
          },
            "message": message_text
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print("📱 ההודעה נשלחה בהצלחה.")
        else:
            print(f"שגיאה בשליחת SMS: {response.status_code} {response.text}")
    except Exception as e:
        print(f"שגיאה בביצוע בקשת SMS: {e}")

def check_alerts():
    print("בודק התראות...")
    url = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        text = response.content.decode('utf-8-sig')

        with open("last_alert_raw.json", "w", encoding="utf-8") as f:
            f.write(text)

        if text.strip() in ("", "\n", "\n\n"):
            print("🟩 אין התראה חדשה (תגובה ריקה).")
            return None

        if not (text.startswith('[') or text.startswith('{')):
            print("⚠️ תשובה לא תקינה:", text[:50])
            return None

        logging.info(f"התקבלה התרעה חדשה:\n{text}")
        data = json.loads(text)

        title = data.get("title", "")
        desc = data.get("desc", "")
        alerts = data.get("data", [])

        matched_areas = [a for a in alerts if a in ALLOWED_AREAS]

        if matched_areas:
            print("התראה רלוונטית")

            tz = pytz.timezone("Asia/Jerusalem")
            now_str = datetime.now(tz).strftime("%H:%M")

            clean_title = re.sub(r'[\r\n]+', ' ', title).strip()
            clean_desc = re.sub(r'[\r\n]+', ' ', desc).strip()

            subject = f" העורף במצפה רמון: {clean_title} \nהנחיה:  {clean_desc} \n *נשלח בשעה {now_str}*"

            send_sms(subject)
            return "alert"
        else:
            print("🔕 התראה לא רלוונטית.")
            return None

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
        time.sleep(30)

if __name__ == "__main__":
    main()
