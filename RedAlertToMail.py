import requests
import time
import json
import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime
import pytz
import re


logging.basicConfig(
    filename="alerts.log",      # הקובץ שאליו נרשמים הלוגים
    level=logging.INFO,         # רמת הלוג – INFO ומעלה
    format="%(asctime)s %(levelname)s: %(message)s",  # פורמט עם זמן ורמה
    filemode="a",               # מצב append – לא מוחק קיים
)

EMAIL_ADDRESS = 'YOUR_GMAIL'
EMAIL_PASSWORD = 'YOUR_APP_PASS'

def load_recipients(file_path="mails.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # מנקה רווחים ותווי שורה, ומחזיר רק שורות שאינן ריקות
            emails = [line.strip() for line in lines if line.strip()]
            return emails
    except Exception as e:
        print(f"שגיאה בטעינת רשימת נמענים: {e}")
        return []

def send_email(subject):
    recipients = load_recipients()
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(recipients)
    msg.set_content(subject)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print("✉️ המייל נשלח בהצלחה.")
    except Exception as e:
        print(f"שגיאה בשליחת מייל: {e}")
ALLOWED_AREAS = {
    "תל אביב - דרום העיר ויפו",
    "תל אביב - מזרח",
    "תל אביב - מרכז העיר",
    "תל אביב - עבר הירקון"
}


def check_alerts():
    print("בודק התראות...")
    url = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        text = response.content.decode('utf-8-sig')

        # שמירת התשובה לקובץ
        with open("last_alert_raw.json", "w", encoding="utf-8") as f:
            f.write(text)

        # אם קיבלנו בדיוק שני תווי שורה – אין התראה
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

        # סינון לפי אזורים מותרים
        matched_areas = [a for a in alerts if a in ALLOWED_AREAS]

        if matched_areas:
            print("התראה רלוונטית")

            tz = pytz.timezone("Asia/Jerusalem")
            now_str = datetime.now(tz).strftime("%H:%M")

            clean_title = re.sub(r'[\r\n]+', ' ', title).strip()
            clean_desc = re.sub(r'[\r\n]+', ' ', desc).strip()

            subject = f"התרעת פיקוד העורף: {title} הנחיה: {desc} *נשלח בשעה {now_str}*"



            send_email(subject)
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
