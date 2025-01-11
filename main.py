import os
import json
import requests
from datetime import datetime
from flask import Flask, jsonify
import pytz
from threading import Timer

# Initialize Flask app
app = Flask(__name__)

# Cache file path
CACHE_FILE = 'prayer_times_cache.json'

# Fetch prayer times from the remote URL
def fetch_prayer_times():
    url = "https://northerly-robin-8705.dataplicity.io/mtws-iqaamah-times/all"
    response = requests.get(url)
    data = response.json()

    # Save the data to cache file
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

# Read cached prayer times from file
def read_cached_prayer_times():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Set the timezone (US/Eastern)
TIMEZONE = pytz.timezone('US/Eastern')

# Fetch and cache prayer times every 12 hours
def update_cache_periodically():
    fetch_prayer_times()
    # Set the next update time (12 hours later)
    Timer(12 * 60 * 60, update_cache_periodically).start()

# Initial caching of prayer times and periodic update
fetch_prayer_times()
update_cache_periodically()

@app.route("/<day>", methods=["GET"])
def get_prayer_times(day):
    # Get current prayer times from cache
    cached_times = read_cached_prayer_times()

    # Ensure the day is a valid key
    valid_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if day not in valid_days:
        return jsonify({"error": "Invalid day"}), 400

    # Get the prayer times for the requested day
    times = cached_times.get(day, {})
    if not times:
        return jsonify({"error": f"No data found for {day}"}), 404

    # Return the prayer times in a user-friendly format
    prayer_times = {
        "Fajr": times[0],
        "Dhuhr": times[1],
        "Asr": times[2],
        "Maghrib": times[3],
        "Ishaa": times[4]
    }

    return jsonify(prayer_times)

# Start the Flask app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
