from flask import Flask, jsonify
from flask_caching import Cache
import requests
from datetime import datetime, timedelta
import pytz
import threading
import time
import os

app = Flask(__name__)

# Flask-Caching configuration
cache_config = {
    "CACHE_TYPE": "SimpleCache",  # Use a simple in-memory cache
    "CACHE_DEFAULT_TIMEOUT": 43200  # Cache timeout of 12 hours
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# Remote URL for prayer times
PRAYER_TIMES_URL = "https://northerly-robin-8705.dataplicity.io/mtws-iqaamah-times/all"

# Timezone
TIMEZONE = pytz.timezone("US/Eastern")


def fetch_prayer_times():
    """Fetch prayer times from the remote URL and cache them."""
    try:
        response = requests.get(PRAYER_TIMES_URL)
        response.raise_for_status()  # Raise an error for bad HTTP responses
        data = response.json()
        cache.set("prayer_times", data)  # Cache the fetched data
        return data
    except requests.RequestException as e:
        cached_data = cache.get("prayer_times")  # Use cached data if available
        if cached_data:
            return cached_data
        return {"error": "Failed to fetch prayer times", "details": str(e)}


def update_prayer_times():
    """Background thread to periodically update cached prayer times."""
    while True:
        fetch_prayer_times()
        time.sleep(43200)  # Wait for 12 hours before the next update


@app.before_first_request
def start_update_thread():
    """Start the background thread for periodic updates."""
    thread = threading.Thread(target=update_prayer_times, daemon=True)
    thread.start()


def transform_prayer_times(data, day):
    """Transform prayer times into a user-friendly format."""
    if day not in data:
        return {"error": f"No data available for {day}"}

    times = data[day]
    return {
        "Fajr": times[0],
        "Dhuhr": times[1],
        "Asr": times[2],
        "Maghrib": times[3],
        "Ishaa": times[4]
    }


@app.route("/prayer-times/<day>", methods=["GET"])
def get_prayer_times_for_day(day):
    """API endpoint to get prayer times for a specific day."""
    data = fetch_prayer_times()
    if "error" in data:
        return jsonify(data), 500

    day = day.capitalize()  # Ensure the day is properly capitalized
    prayer_times = transform_prayer_times(data, day)
    return jsonify(prayer_times)


@app.route("/prayer-times/today", methods=["GET"])
def get_today_prayer_times():
    """API endpoint to get prayer times for today."""
    data = fetch_prayer_times()
    if "error" in data:
        return jsonify(data), 500

    # Get the current day in the specified timezone
    current_day = datetime.now(TIMEZONE).strftime("%A")
    prayer_times = transform_prayer_times(data, current_day)
    return jsonify(prayer_times)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Use PORT environment variable or default to 8000
    app.run(host="0.0.0.0", port=port)
