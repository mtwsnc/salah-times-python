from flask import Flask, jsonify
import requests
from flask_caching import Cache
from datetime import datetime
import pytz

app = Flask(__name__)

# Configure caching
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # Cache timeout in seconds (5 minutes)
cache = Cache(app)

# Remote URL for fetching prayer times
REMOTE_URL = "https://northerly-robin-8705.dataplicity.io/mtws-iqaamah-times/all"

# Function to fetch and transform data from the remote URL
def fetch_prayer_times():
    response = requests.get(REMOTE_URL)
    if response.status_code == 200:
        raw_data = response.json()
        transformed_data = {
            day: {
                "Fajr": times[0],
                "Dhuhr": times[1],
                "Asr": times[2],
                "Maghrib": times[3],
                "Ishaa": times[4],
            }
            for day, times in raw_data.items()
        }
        return transformed_data
    else:
        raise Exception("Failed to fetch prayer times.")

# API route to get prayer times dynamically based on the current day
@app.route("/prayer-times/today", methods=["GET"])
def get_prayer_times_for_today():
    # Set the desired timezone
    tz = pytz.timezone("US/Eastern")
    current_day = datetime.now(tz).strftime("%A")  # Get the current day in Eastern Time

    prayer_times = cache.get("prayer_times")

    if not prayer_times:
        try:
            prayer_times = fetch_prayer_times()
            cache.set("prayer_times", prayer_times)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if current_day in prayer_times:
        return jsonify({current_day: prayer_times[current_day]})
    else:
        return jsonify({"error": "Failed to retrieve data for the current day."}), 500

# API route to fetch and cache all prayer times
@app.route("/prayer-times/all", methods=["GET"])
def get_all_prayer_times():
    prayer_times = cache.get("prayer_times")

    if not prayer_times:
        try:
            prayer_times = fetch_prayer_times()
            cache.set("prayer_times", prayer_times)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify(prayer_times)

if __name__ == "__main__":
    app.run(debug=True)
