#!/usr/bin/env python3
import requests
import time
import json
import os
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

TELEGRAM_BOT_TOKEN = "8479703528:AAFG2p9UsAC65_3IMm2aCvw9klvFTjJ5lvc"
ISRAEL_LAT = 32.0853
ISRAEL_LON = 34.7818
USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
MIN_MAGNITUDE = 4.0
SENT_FILE = "/tmp/sent_earthquakes.json"
SUBSCRIBERS_FILE = "/tmp/subscribers.json"


def load_sent():
    try:
        if os.path.exists(SENT_FILE):
            with open(SENT_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()


def save_sent(sent):
    try:
        with open(SENT_FILE, 'w') as f:
            json.dump(list(sent), f)
    except:
        pass


def load_subscribers():
    try:
        if os.path.exists(SUBSCRIBERS_FILE):
            with open(SUBSCRIBERS_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()


def save_subscribers(subs):
    try:
        with open(SUBSCRIBERS_FILE, 'w') as f:
            json.dump(list(subs), f)
    except:
        pass


def calc_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def send_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=30)
        return r.json().get("ok", False)
    except:
        return False


def broadcast(subscribers, text):
    for chat_id in subscribers:
        send_msg(chat_id, text)
        time.sleep(0.1)


def check_new_subscribers(subscribers):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        r = requests.get(url, timeout=30)
        updates = r.json().get("result", [])

        for update in updates:
            msg = update.get("message", {})
            text = msg.get("text", "")
            chat_id = msg.get("chat", {}).get("id")

            if chat_id and text == "/start" and chat_id not in subscribers:
                subscribers.add(chat_id)
                save_subscribers(subscribers)
                send_msg(chat_id, "🤖 <b>ברוך הבא לבוט התראות רעידות אדמה!</b>\n\nתקבל התראות על רעידות אדמה בעוצמה 4.0 ומעלה.\n\nשלח /stop כדי להפסיק לקבל התראות.")

            elif chat_id and text == "/stop" and chat_id in subscribers:
                subscribers.discard(chat_id)
                save_subscribers(subscribers)
                send_msg(chat_id, "👋 הוסרת מרשימת המנויים. שלח /start כדי להירשם מחדש.")

        # Clear processed updates
        if updates:
            last_update_id = updates[-1]["update_id"]
            requests.get(f"{url}?offset={last_update_id + 1}", timeout=10)
    except:
        pass

    return subscribers


def format_msg(eq):
    props = eq["properties"]
    coords = eq["geometry"]["coordinates"]
    lon, lat = coords[0], coords[1]
    mag = props.get("mag", "?")
    place = props.get("place", "Unknown")
    time_ms = props.get("time", 0)

    eq_time = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)
    time_str = eq_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    distance = calc_distance(lat, lon, ISRAEL_LAT, ISRAEL_LON)
    maps = f"https://www.google.com/maps?q={lat},{lon}"

    return f"""🌍 <b>רעידת אדמה התגלתה!</b>

📊 <b>עוצמה:</b> {mag}
📍 <b>מיקום:</b> {place}
📏 <b>מרחק מישראל:</b> {distance:,.0f} ק"מ
🎯 <b>קואורדינטות:</b> {lat:.4f}, {lon:.4f}
🕐 <b>זמן:</b> {time_str}

🗺️ <a href="{maps}">צפה במפה</a>"""


def main():
    sent = load_sent()
    subscribers = load_subscribers()

    # Add owner as default subscriber
    subscribers.add(159306920)
    save_subscribers(subscribers)

    while True:
        try:
            # Check for new subscribers
            subscribers = check_new_subscribers(subscribers)

            # Fetch earthquakes
            r = requests.get(USGS_API_URL, timeout=30)
            quakes = r.json().get("features", [])

            for eq in quakes:
                eq_id = eq.get("id")
                mag = eq["properties"].get("mag", 0) or 0

                if eq_id in sent:
                    continue

                sent.add(eq_id)

                if mag >= MIN_MAGNITUDE:
                    broadcast(subscribers, format_msg(eq))
                    save_sent(sent)
                    time.sleep(1)

            if len(sent) > 500:
                sent = set(list(sent)[-200:])
                save_sent(sent)

            time.sleep(60)

        except KeyboardInterrupt:
            break
        except:
            time.sleep(30)


if __name__ == "__main__":
    main()
