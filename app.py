import os
import sys
import math
from datetime import datetime
from flask import Flask, request, jsonify, Response
from prasnatantra import PrasnaChart, SIGN_LORDS
from prasnatantra.astronomy import get_sign_name, get_nakshatra_pada
from prasnatantra.engine import get_sign
from prasnatantra.tajaka import get_planetary_avastha
from prasnatantra.ai import map_question_to_house, generate_astrological_reading
from timezonefinder import TimezoneFinder
import pytz

tf = TimezoneFinder()


app = Flask(__name__, static_folder='static', static_url_path='')

def format_longitude(deg):
    """Formats decimal degrees into Dd Mm Ss format."""
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60)
    return f"{d}° {m}' {s}\""

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/chart', methods=['POST'])
def api_chart():
    """
    Computes and returns details of the Prasna chart based on date, time, and coordinates.
    """
    data = request.json or {}
    date_str = data.get("date")
    time_str = data.get("time")
    lat_str = data.get("latitude")
    lon_str = data.get("longitude")
    if not lat_str or lat_str == "undefined" or lat_str == "null":
        lat_str = "12:58:18"
    if not lon_str or lon_str == "undefined" or lon_str == "null":
        lon_str = "77:35:41"
        
    try:
        tz_offset = float(data.get("tz_offset", 5.5))
        if math.isnan(tz_offset):
            tz_offset = 5.5
    except (ValueError, TypeError):
        tz_offset = 5.5

    
    if not date_str or not time_str:
        now = datetime.now()
        date_str = date_str or now.strftime("%Y-%m-%d")
        time_str = time_str or now.strftime("%H:%M:%S")
        
    try:
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return jsonify({"error": f"Invalid date/time format: {e}"}), 400
        
    try:
        chart = PrasnaChart(local_dt, lat_str, lon_str, tz_offset)
        
        # Serialize planet details
        planets_data = {}
        for p, pdata in chart.planets.items():
            lon = pdata["longitude"]
            sign = get_sign(lon)
            nak, pada, abbr = get_nakshatra_pada(lon)
            avastha = get_planetary_avastha(p, lon, pdata, chart.planets["Sun"]["longitude"], chart.planets)
            
            planets_data[p] = {
                "longitude": lon,
                "formatted": format_longitude(lon),
                "sign": sign,
                "sign_name": get_sign_name(sign),
                "nakshatra": nak,
                "pada": pada,
                "avastha": avastha,
                "speed": pdata["speed"]
            }
            
        # Serialize house details
        houses_data = []
        for h_num in range(1, 13):
            h_data = chart.houses[h_num]
            sign = h_data["sign"]
            lord = SIGN_LORDS[sign]
            houses_data.append({
                "house": h_num,
                "sign": sign,
                "sign_name": get_sign_name(sign),
                "lord": lord,
                "longitude_start": h_data["start_longitude"]
            })
            
        # Serialize global chart properties
        response_data = {
            "local_time": local_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "utc_str": chart.utc_str,
            "ayanamsha": chart.ayanamsha,
            "ayanamsha_formatted": format_longitude(chart.ayanamsha),
            "lagna_longitude": chart.lagna_sidereal,
            "lagna_longitude_formatted": format_longitude(chart.lagna_sidereal),
            "lagna_sign": chart.lagna_sign,
            "lagna_sign_name": get_sign_name(chart.lagna_sign),
            "lagnapathi": chart.lagnapathi,
            "sincerity": chart.sincerity,
            "planets": planets_data,
            "houses": houses_data
        }
        
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": f"Chart calculation failed: {e}"}), 500

@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """
    Evaluates a specific query (standard house or special rules) on a recalculated Prasna chart.
    """
    data = request.json or {}
    date_str = data.get("date")
    time_str = data.get("time")
    lat_str = data.get("latitude")
    lon_str = data.get("longitude")
    if not lat_str or lat_str == "undefined" or lat_str == "null":
        lat_str = "12:58:18"
    if not lon_str or lon_str == "undefined" or lon_str == "null":
        lon_str = "77:35:41"
        
    try:
        tz_offset = float(data.get("tz_offset", 5.5))
        if math.isnan(tz_offset):
            tz_offset = 5.5
    except (ValueError, TypeError):
        tz_offset = 5.5
    
    house_num = int(data.get("house_num", 1))
    query_num = int(data.get("query_num", 1))
    special_category = data.get("special_category")
    question = data.get("question")

    
    if not date_str or not time_str:
        now = datetime.now()
        date_str = date_str or now.strftime("%Y-%m-%d")
        time_str = time_str or now.strftime("%H:%M:%S")
        
    try:
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return jsonify({"error": f"Invalid date/time format: {e}"}), 400
        
    try:
        chart = PrasnaChart(local_dt, lat_str, lon_str, tz_offset)
        evaluation = chart.evaluate_query(house_num, query_num=query_num, special_category=special_category, query_text=question)
        return jsonify(evaluation)
    except Exception as e:
        return jsonify({"error": f"Evaluation failed: {e}"}), 500

@app.route('/api/map-question', methods=['POST'])
def api_map_question():
    """
    Leverages LLM via map_question_to_house to classify natural language queries.
    """
    data = request.json or {}
    question = data.get("question")
    if not question:
        return jsonify({"error": "Question parameter is required"}), 400
        
    try:
        result = map_question_to_house(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Question mapping failed: {e}"}), 500

@app.route('/api/reading', methods=['POST'])
def api_reading():
    """
    Streams the token-by-token Groq AI reading back to the client.
    """
    data = request.json or {}
    question = data.get("question", "General outlook")
    chart_details = data.get("chart_details", {})
    
    if not chart_details:
        return jsonify({"error": "chart_details parameter is required"}), 400
        
    def generate():
        try:
            for chunk in generate_astrological_reading(question, chart_details):
                yield chunk
        except Exception as e:
            yield f"\n[AI Error] Could not generate reading: {e}"
            
    return Response(generate(), mimetype='text/plain')

@app.route('/api/resolve-timezone', methods=['POST'])
def api_resolve_timezone():
    """
    Resolves the timezone name and UTC offset (in hours) at a given coordinates and local time.
    """
    data = request.json or {}
    lat_val = data.get("latitude")
    lon_val = data.get("longitude")
    date_str = data.get("date")
    time_str = data.get("time")
    
    if lat_val is None or lon_val is None:
        return jsonify({"error": "Latitude and longitude are required"}), 400
        
    try:
        lat = float(lat_val)
        lon = float(lon_val)
    except ValueError:
        from prasnatantra.astronomy import parse_coord
        lat = parse_coord(str(lat_val))
        lon = parse_coord(str(lon_val))
        
    if not date_str or not time_str:
        now = datetime.now()
        date_str = date_str or now.strftime("%Y-%m-%d")
        time_str = time_str or now.strftime("%H:%M:%S")
        
    try:
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return jsonify({"error": f"Invalid date/time format: {e}"}), 400
        
    try:
        tz_name = tf.timezone_at(lng=lon, lat=lat)
        if not tz_name:
            return jsonify({"timezone": "UTC", "tz_offset": 0.0})
            
        tz = pytz.timezone(tz_name)
        try:
            localized = tz.localize(local_dt, is_dst=None)
            offset_seconds = localized.utcoffset().total_seconds()
            offset_hours = offset_seconds / 3600.0
        except Exception:
            localized = tz.localize(local_dt, is_dst=False)
            offset_seconds = localized.utcoffset().total_seconds()
            offset_hours = offset_seconds / 3600.0
            
        return jsonify({
            "timezone": tz_name,
            "tz_offset": offset_hours
        })
    except Exception as e:
        return jsonify({"error": f"Timezone resolution failed: {e}"}), 500


if __name__ == '__main__':
    # Defaulting to port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
