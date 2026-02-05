#!/usr/bin/env python3
"""
Earthquake Alert Telegram Bot
"""

import requests
import time
import json
import os
from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

# Configuration
TELEGRAM_BOT_TOKEN = "8479703528:AAFG2p9UsAC65_3IMm2aCvw9klvFTjJ5lvc"
TELEGRAM_CHAT_ID = 159306920

# Israel coordinates (Tel Aviv)
ISRAEL_LAT = 32.0853
ISRAEL_LON = 34.7818

# USGS Earthquake API
USGS_API_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

# Minimum magnitude
MIN_MAGNITUDE = 4.0

# File to track sent earthquakes
SENT_FILE = os.path.join(os.path.dirname(__file__), "sent_earthquakes.json")


def load_sent_earthquakes():
    try:
        if os.path.exists(SENT_FILE):
            with open(SENT_FILE, 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()


def save_sent_earthquakes(sent):
    try:
        with open(SENT_FILE, 'w') as f:
            json.dump(list(sent), f)
    except:
        pass


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.json().get("ok", False)
    except Exception as e:
        return False


def format_earthquake_message(eq):
    props = eq["properties"]
    coords = eq["geometry"]["coordinates"]

    lon, lat, depth = coords[0], coords[1], coords[2] or 0
    magnitude = props.get("mag", "N/A")
    place = props.get("place", "Unknown location")
    time_ms = props.get("time", 0)

    eq_time = datetime.fromtimestamp(time_ms / 1000, tz=timezone.utc)
    time_str = eq_time.strftime("%Y-%m-%d %H:%M:%S UTC")

    distance_km = calculate_distance(lat, lon, ISRAEL_LAT, ISRAEL_LON)
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"

    message = f"""🌍 <b>רעידת אדמה התגלתה!</b>

📊 <b>עוצמה:</b> {magnitude}
📍 <b>מיקום:</b> {place}
📏 <b>מרחק מישראל:</b> {distance_km:,.0f} ק"מ
🎯 <b>קואורדינטות:</b> {lat:.4f}, {lon:.4f}
🕐 <b>זמן:</b> {time_str}

🗺️ <a href="{maps_link}">צפה במפה</a>"""

    return message


def fetch_earthquakes():
    try:
        response = requests.get(USGS_API_URL, timeout=30)
        data = response.json()
        return data.get("features", [])
    except:
        return []


def main():
    sent_earthquakes = load_sent_earthquakes()

    # Send startup message
    send_telegram_message("🤖 <b>בוט התראות רעידות אדמה פעיל!</b>\n\nמקור הנתונים: USGS")

    while True:
        try:
            earthquakes = fetch_earthquakes()

            for eq in earthquakes:
                eq_id = eq.get("id")
                magnitude = eq["properties"].get("mag", 0) or 0

                if eq_id in sent_earthquakes:
                    continue

                if magnitude < MIN_MAGNITUDE:
                    sent_earthquakes.add(eq_id)
                    continue

                message = format_earthquake_message(eq)
                if send_telegram_message(message):
                    sent_earthquakes.add(eq_id)
                    save_sent_earthquakes(sent_earthquakes)

                time.sleep(1)

            # Clean old entries (keep last 500)
            if len(sent_earthquakes) > 500:
                sent_earthquakes = set(list(sent_earthquakes)[-500:])
                save_sent_earthquakes(sent_earthquakes)

            time.sleep(60)

        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(30)


if __name__ == "__main__":
    main()
