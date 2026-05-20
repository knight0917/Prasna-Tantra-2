import os
import math
import urllib.parse
from datetime import datetime, date, time
import requests
import streamlit as st
import pandas as pd

# Import local engine
from prasnatantra import PrasnaChart, SIGN_LORDS
from prasnatantra.astronomy import get_nakshatra_pada, get_sign_name
from prasnatantra.engine import get_sign
from prasnatantra.tajaka import get_planetary_avastha
from prasnatantra.ai import map_question_to_house, generate_astrological_reading

# Configure timezone finder
from timezonefinder import TimezoneFinder
import pytz
tf = TimezoneFinder()


def format_longitude(deg):
    """Formats decimal degrees into Dd Mm Ss format."""
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60)
    return f"{d}° {m}' {s}\""


# Set Page Config
st.set_page_config(
    page_title="Prasna Tantra - Vedic Horary Astrology",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap');

/* Sidebar width adjustment */
[data-testid="stSidebar"] {
    min-width: 340px;
    max-width: 50vw;
}

/* Main Streamlit container background and stars effect */
.stApp {
    background-color: #080711;
    background-image: 
        radial-gradient(1px 1px at 20px 30px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1.5px 1.5px at 40px 70px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1px 1px at 50px 160px, #dddddd, rgba(0,0,0,0)),
        radial-gradient(2px 2px at 80px 120px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1px 1px at 110px 220px, #cccccc, rgba(0,0,0,0)),
        radial-gradient(1.5px 1.5px at 150px 50px, #ffffff, rgba(0,0,0,0));
    background-repeat: repeat;
    background-size: 300px 300px;
    color: #f3f4f6;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Custom fonts */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
}

/* Custom glass cards */
.glass-card {
    background: rgba(15, 14, 30, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 1.5rem;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    margin-bottom: 1.5rem;
}

/* Glowing text */
.glow-text {
    text-shadow: 0 0 10px rgba(129, 140, 248, 0.6), 0 0 20px rgba(192, 132, 252, 0.4);
    background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Sincerity status badge */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-weight: bold;
    font-size: 0.85rem;
    text-transform: uppercase;
}
.badge-sincere {
    background-color: rgba(52, 211, 153, 0.15);
    color: #34d399;
    border: 1px solid #34d399;
}
.badge-insincere {
    background-color: rgba(248, 113, 113, 0.15);
    color: #f87171;
    border: 1px solid #f87171;
}

/* Indicators Lists */
.indicator-item {
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    border-left: 3px solid;
}
.indicator-sincere {
    background: rgba(52, 211, 153, 0.08);
    border-left-color: #34d399;
    color: #34d399;
}
.indicator-insincere {
    background: rgba(248, 113, 113, 0.08);
    border-left-color: #f87171;
    color: #f87171;
}

/* Timing and Details Layout */
.timing-highlight {
    background: linear-gradient(90deg, rgba(129, 140, 248, 0.15) 0%, rgba(192, 132, 252, 0.15) 100%);
    border: 1px solid rgba(129, 140, 248, 0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 1.05rem;
    margin-bottom: 1rem;
}

.details-list {
    list-style-type: none;
    padding-left: 0;
}
.details-list li {
    padding: 0.4rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    font-size: 0.92rem;
}

/* SVG Container */
.kundali-container {
    background: rgba(5, 4, 12, 0.5);
    border-radius: 12px;
    padding: 0.5rem;
    border: 1px solid rgba(255, 255, 255, 0.03);
    display: flex;
    justify-content: center;
    align-items: center;
    max-width: 420px;
    margin: 0 auto;
}

/* AI stream box styling */
.ai-stream-box {
    background: rgba(10, 8, 20, 0.8);
    border: 1px solid rgba(129, 140, 248, 0.2);
    border-radius: 12px;
    padding: 1.5rem;
    font-size: 1rem;
    line-height: 1.6;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)


def resolve_timezone_offset(lat, lon, date_obj, time_obj):
    """Resolves timezone offset offline using timezonefinder and pytz."""
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        tz_name = tf.timezone_at(lat=lat_f, lng=lon_f)
        if not tz_name:
            return 5.5, "UTC (Default)"
        
        tz = pytz.timezone(tz_name)
        dt = datetime.combine(date_obj, time_obj)
        # Handle DST calculations correctly
        localized = tz.localize(dt, is_dst=None)
        offset = localized.utcoffset().total_seconds() / 3600.0
        return offset, tz_name
    except Exception as e:
        return 5.5, f"UTC (Default, error: {e})"


def generate_kundali_svg(chart):
    """Generates the North Indian Kundali SVG markup dynamically from chart data."""
    HOUSE_GEOMETRY = {
        1:  { "cx": 200, "cy": 90,  "sx": 200, "sy": 135 },
        2:  { "cx": 125, "cy": 50,  "sx": 150, "sy": 75  },
        3:  { "cx": 65,  "cy": 110, "sx": 90,  "sy": 135 },
        4:  { "cx": 110, "cy": 200, "sx": 150, "sy": 200 },
        5:  { "cx": 65,  "cy": 290, "sx": 90,  "sy": 265 },
        6:  { "cx": 125, "cy": 350, "sx": 150, "sy": 325 },
        7:  { "cx": 200, "cy": 310, "sx": 200, "sy": 265 },
        8:  { "cx": 275, "cy": 350, "sx": 250, "sy": 325 },
        9:  { "cx": 335, "cy": 290, "sx": 310, "sy": 265 },
        10: { "cx": 290, "cy": 200, "sx": 250, "sy": 200 },
        11: { "cx": 335, "cy": 110, "sx": 310, "sy": 135 },
        12: { "cx": 275, "cy": 50,  "sx": 250, "sy": 75  }
    }

    PLANET_METADATA = {
        "Sun": { "short": "Su", "malefic": True },
        "Moon": { "short": "Mo", "malefic": False },
        "Mars": { "short": "Ma", "malefic": True },
        "Mercury": { "short": "Me", "malefic": False },
        "Jupiter": { "short": "Ju", "malefic": False },
        "Venus": { "short": "Ve", "malefic": False },
        "Saturn": { "short": "Sa", "malefic": True },
        "Rahu": { "short": "Ra", "malefic": True },
        "Ketu": { "short": "Ke", "malefic": True }
    }

    lagna_sign = chart.lagna_sign
    
    svg = f"""
    <svg viewBox="0 0 400 400" width="100%" height="100%">
        <style>
            .chart-border {{ fill: none; stroke: #818cf8; stroke-width: 2.5; filter: drop-shadow(0 0 6px rgba(129, 140, 248, 0.3)); }}
            .chart-line {{ fill: none; stroke: rgba(129, 140, 248, 0.5); stroke-width: 1.5; }}
            .house-label {{ fill: #6b7280; font-family: 'Outfit', sans-serif; font-size: 11px; font-weight: 600; text-anchor: middle; }}
            .sign-number {{ fill: #c084fc; font-family: 'Outfit', sans-serif; font-size: 12px; font-weight: 700; text-anchor: middle; }}
            .planet-txt {{ font-family: 'Plus Jakarta Sans', sans-serif; font-size: 10.5px; font-weight: 500; text-anchor: middle; }}
            .planet-txt.benefic {{ fill: #22d3ee; }}
            .planet-txt.malefic {{ fill: #f87171; }}
        </style>
        <rect x="10" y="10" width="380" height="380" class="chart-border" />
        <line x1="10" y1="10" x2="390" y2="390" class="chart-line" />
        <line x1="390" y1="10" x2="10" y2="390" class="chart-line" />
        <polygon points="200,10 390,200 200,390 10,200" class="chart-line" />
        
        <!-- House Numbers -->
        <text x="200" y="105" class="house-label">H1</text>
        <text x="135" y="55" class="house-label">H2</text>
        <text x="65" y="125" class="house-label">H3</text>
        <text x="115" y="205" class="house-label">H4</text>
        <text x="65" y="285" class="house-label">H5</text>
        <text x="135" y="355" class="house-label">H6</text>
        <text x="200" y="305" class="house-label">H7</text>
        <text x="265" y="355" class="house-label">H8</text>
        <text x="335" y="285" class="house-label">H9</text>
        <text x="285" y="205" class="house-label">H10</text>
        <text x="335" y="125" class="house-label">H11</text>
        <text x="265" y="55" class="house-label">H12</text>
    """
    
    # Render Sign Numbers
    for h in range(1, 13):
        sign_num = ((lagna_sign + h - 1) % 12) + 1
        geom = HOUSE_GEOMETRY[h]
        svg += f'<text x="{geom["sx"]}" y="{geom["sy"]}" class="sign-number">{sign_num}</text>\n'

    # Render Planet Positions
    house_occupants = {h: [] for h in range(1, 13)}
    
    for p_name, p_data in chart.planets.items():
        p_sign = int(p_data["longitude"] / 30.0) % 12
        p_house = ((p_sign - lagna_sign + 12) % 12) + 1
        
        meta = PLANET_METADATA.get(p_name, {"short": p_name[:2], "malefic": False})
        label = meta["short"]
        
        if p_data.get("speed", 0.0) < 0.0:
            label += "(R)"
            
        sun_lon = chart.planets["Sun"]["longitude"]
        avastha = get_planetary_avastha(p_name, p_data["longitude"], p_data, sun_lon, chart.planets)
        if avastha == "Mushita":
            label += "c"
            
        house_occupants[p_house].append({
            "name": p_name,
            "label": label,
            "is_malefic": meta["malefic"]
        })
        
    for h, occupants in house_occupants.items():
        if not occupants:
            continue
        geom = HOUSE_GEOMETRY[h]
        num_occ = len(occupants)
        for idx, occ in enumerate(occupants):
            cx = geom["cx"]
            cy = geom["cy"]
            if num_occ > 1:
                cy = geom["cy"] - ((num_occ - 1) * 7) + (idx * 14)
            cls = "malefic" if occ["is_malefic"] else "benefic"
            svg += f'<text x="{cx}" y="{cy}" class="planet-txt {cls}">{occ["label"]}<title>{occ["name"]}</title></text>\n'
            
    svg += "</svg>"
    return svg


# Streamlit Session State Initialization
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []
if "latitude" not in st.session_state:
    st.session_state.latitude = "12:58:18"
if "longitude" not in st.session_state:
    st.session_state.longitude = "77:35:41"
if "tz_offset" not in st.session_state:
    st.session_state.tz_offset = 5.5
if "tz_name" not in st.session_state:
    st.session_state.tz_name = "Asia/Kolkata"
if "chart" not in st.session_state:
    st.session_state.chart = None
if "evaluation" not in st.session_state:
    st.session_state.evaluation = None
if "ai_reading" not in st.session_state:
    st.session_state.ai_reading = ""
if "query_counter" not in st.session_state:
    st.session_state.query_counter = 1

# Header Section
st.markdown("<h1 class='glow-text' style='text-align: center; margin-bottom: 0.5rem;'>✦ PRASNA TANTRA ✦</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 1.15rem; margin-bottom: 2.5rem;'>Vedic Horary Astrology and Shatpanchasika Decision Engine</p>", unsafe_allow_html=True)

# Main Application Layout: Sidebar (Inputs) & Main Panel (Results)
with st.sidebar:
    st.markdown("<h3 class='glow-text'>✦ Astronomical Inputs</h3>", unsafe_allow_html=True)
    
    # Date & Time Pickers
    date_val = st.date_input("Select Query Date", date.today())
    time_str = st.text_input("Select Query Time (HH:MM:SS)", datetime.now().strftime("%H:%M:%S"))
    try:
        time_val = datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        time_val = time(12, 0, 0)
        st.warning("Invalid time format. Defaulted to 12:00:00")

    # Geocoding Autocomplete Section
    st.markdown("---")
    st.markdown("##### 📍 Resolve Location")
    search_query = st.text_input("Type City/Town Name", value="Bangalore")
    
    if st.button("Search Location"):
        with st.spinner("Fetching coordinates..."):
            url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(search_query)}&format=json&addressdetails=1&limit=5"
            headers = {"User-Agent": "PrasnaTantraAstrologyDashboard/1.0", "Accept-Language": "en"}
            try:
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    results = r.json()
                    if results:
                        st.session_state.suggestions = results
                        st.success(f"Found {len(results)} matches!")
                    else:
                        st.session_state.suggestions = []
                        st.error("No locations found.")
                else:
                    st.error(f"Geocoding server error: status {r.status_code}")
            except Exception as ex:
                st.error(f"Geocoding failed: {ex}")

    # Display geocoding options if found
    if st.session_state.suggestions:
        options_map = {res["display_name"]: res for res in st.session_state.suggestions}
        selected = st.selectbox("Select precise location:", list(options_map.keys()))
        if selected:
            sel_res = options_map[selected]
            st.session_state.latitude = sel_res["lat"]
            st.session_state.longitude = sel_res["lon"]
            # Auto-resolve timezone
            offset, tz_name = resolve_timezone_offset(sel_res["lat"], sel_res["lon"], date_val, time_val)
            st.session_state.tz_offset = offset
            st.session_state.tz_name = tz_name
            st.success(f"Configured: {tz_name} (UTC+{offset})")

    # Advanced Coordinates Expander
    with st.expander("✦ Show Advanced Coordinates Override"):
        lat_override = st.text_input("Latitude", value=str(st.session_state.latitude))
        lon_override = st.text_input("Longitude", value=str(st.session_state.longitude))
        tz_override = st.number_input("Timezone Offset (Hours East)", value=float(st.session_state.tz_offset), step=0.5)
        
        if lat_override != str(st.session_state.latitude) or lon_override != str(st.session_state.longitude) or tz_override != float(st.session_state.tz_offset):
            st.session_state.latitude = lat_override
            st.session_state.longitude = lon_override
            st.session_state.tz_offset = tz_override

    # Query Input
    st.markdown("---")
    st.markdown("<h3 class='glow-text'>✦ Ask Your Question</h3>", unsafe_allow_html=True)
    question_text = st.text_area(
        "Type your question in plain English", 
        value="Will I get the job I interviewed for yesterday?",
        placeholder="e.g. Will my travel be safe? Will it rain today?"
    )

    # Core Action Button
    submit_btn = st.button("✦ Analyze Prasna Chart", use_container_width=True)

# Process query on submission
if submit_btn:
    with st.spinner("Decoding the celestial movements & mapping query..."):
        try:
            # 1. Initialize local dt
            dt_combined = datetime.combine(date_val, time_val)
            
            # 2. Map question to house using LLM mapper
            map_res = map_question_to_house(question_text)
            house_num = map_res.get("house_num", 1)
            special_category = map_res.get("special_category")
            
            # 3. Calculate Prasna Chart
            chart = PrasnaChart(
                dt_combined, 
                str(st.session_state.latitude), 
                str(st.session_state.longitude), 
                float(st.session_state.tz_offset)
            )
            
            # 4. Evaluate query parameters
            evaluation = chart.evaluate_query(
                house_num, 
                query_num=st.session_state.query_counter, 
                special_category=special_category
            )
            
            # 5. Save variables in session state
            st.session_state.chart = chart
            st.session_state.evaluation = evaluation
            st.session_state.query_counter += 1
            st.session_state.ai_reading = "" # Reset reading to force a new stream
            
        except Exception as e:
            st.error(f"Failed to compute chart: {e}")

# Display results if a query has been processed
if st.session_state.chart and st.session_state.evaluation:
    chart = st.session_state.chart
    eval_res = st.session_state.evaluation
    
    # ------------------ TOP PANEL: Genuinity/Sincerity Card ------------------
    sinc = eval_res.get("sincerity", {"is_sincere": True})
    is_sincere = sinc.get("is_sincere", True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col_s1, col_s2 = st.columns([1, 4])
    with col_s1:
        st.markdown("<h5>Genuinity / Sincerity</h5>", unsafe_allow_html=True)
        if is_sincere:
            st.markdown("<span class='badge badge-sincere'>✦ Sincere Query ✦</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='badge badge-insincere'>✦ Insincere / Test ✦</span>", unsafe_allow_html=True)
    with col_s2:
        st.markdown("##### Astrological Authenticity Breakdown")
        if is_sincere:
            for r in sinc.get("reasons_sincere", []):
                st.markdown(f"<div class='indicator-item indicator-sincere'>✓ {r}</div>", unsafe_allow_html=True)
        else:
            for r in sinc.get("reasons_insincere", []):
                st.markdown(f"<div class='indicator-item indicator-insincere'>✗ {r}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ------------------ CENTER PANEL: Evaluation Summary ------------------
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h4>✦ Evaluation Summary</h4>", unsafe_allow_html=True)
    
    # Display Key Metrics
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric(label="Success Chance", value=eval_res.get("success_probability", "Medium"))
    with col_m2:
        st.metric(label="Score Percentage", value=f"{eval_res.get('score_pct', 50)}%")
        
    # Display Timing
    st.markdown(f"<div class='timing-highlight'>⏰ <strong>Estimated Timing:</strong> {eval_res.get('timing', 'N/A')}</div>", unsafe_allow_html=True)
    
    # Coordinates details
    st.markdown(f"**Ayanamsha:** `{format_longitude(chart.ayanamsha)}` | **Lagna:** `{format_longitude(chart.lagna_sidereal)}` in **{get_sign_name(chart.lagna_sign)}**", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Combinations Log
    st.markdown("##### Astrological Rationale Details")
    st.markdown("<ul class='details-list'>", unsafe_allow_html=True)
    for detail in eval_res.get("details", []):
        st.markdown(f"<li>✦ {detail}</li>", unsafe_allow_html=True)
    st.markdown("</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ BOTTOM PANEL: AI Astrological Interpretation ------------------
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 class='glow-text'>✦ AI Astrological Reading (Prasna Tantra & Shatpanchasika Analysis)</h3>", unsafe_allow_html=True)
    
    # If session state reading is empty, trigger the live stream
    if not st.session_state.ai_reading:
        try:
            # We serialize the chart details exactly as the Flask app does
            planets_data = {}
            for p, pdata in chart.planets.items():
                lon = pdata["longitude"]
                sign = get_sign(lon)
                nak, pada, abbr = get_nakshatra_pada(lon)
                avastha = get_planetary_avastha(p, lon, pdata, chart.planets["Sun"]["longitude"], chart.planets)
                planets_data[p] = {
                    "longitude": lon,
                    "formatted": f"{int(lon%30)}° {int((lon%30-int(lon%30))*60)}' {int(((lon%30-int(lon%30))*60-int((lon%30-int(lon%30))*60))*60)}\"",
                    "sign": sign,
                    "sign_name": get_sign_name(sign),
                    "nakshatra": nak,
                    "pada": pada,
                    "speed": pdata["speed"],
                    "is_retrograde": pdata["speed"] < 0,
                    "avastha": avastha
                }
                
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
                    "longitude_start": h_data["start_longitude"],
                    "longitude_end": h_data["end_longitude"]
                })
                
            chart_summary_data = {
                "house": eval_res.get("house"),
                "ref_point_name": eval_res.get("ref_point_name"),
                "ref_sign_name": eval_res.get("ref_sign_name"),
                "query_sign_name": eval_res.get("query_sign_name"),
                "lagnapathi": eval_res.get("lagnapathi"),
                "karyesa": eval_res.get("karyesa"),
                "success_probability": eval_res.get("success_probability"),
                "score_pct": eval_res.get("score_pct"),
                "timing": eval_res.get("timing"),
                "details": eval_res.get("details"),
                "direct_relationship": eval_res.get("direct_relationship"),
                "yogas": eval_res.get("yogas"),
                "shatpanchasika_predictions": eval_res.get("shatpanchasika_predictions")
            }
            
            # Run streaming read
            reading_placeholder = st.empty()
            full_text = ""
            
            # Capture stream
            for chunk in generate_astrological_reading(question_text, chart_summary_data):
                full_text += chunk
                reading_placeholder.markdown(f"<div class='ai-stream-box'>{full_text}</div>", unsafe_allow_html=True)
            
            st.session_state.ai_reading = full_text
            
        except Exception as e:
            st.error(f"Failed to generate AI Reading: {e}")
    else:
        # Display cached reading
        st.markdown(f"<div class='ai-stream-box'>{st.session_state.ai_reading}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ DETAILED TABS: Planet Table, Shatpanchasika, Yogas & Combustions ------------------
    tab1, tab2, tab3 = st.tabs(["🪐 Planetary Longitudes & Avasthas", "📜 Shatpanchasika & Special Predictions", "🧬 Aspect & Combustion Logs"])
    
    with tab1:
        st.markdown("##### Planetary Positions: Planets, Rashi (Sign), Nakshatra, Pada, and House")
        rows = []
        # Add Lagna row
        rows.append({
            "Planet / Body": "Lagna (Ascendant)",
            "House": 1,
            "Rashi (Sign)": get_sign_name(chart.lagna_sign),
            "Nakshatra": "—",
            "Pada": "—",
            "State (Avastha)": "—",
            "Longitude": format_longitude(chart.lagna_sidereal),
            "Speed (deg/day)": "—"
        })
        # Add Planet rows
        for p, pdata in chart.planets.items():
            lon = pdata["longitude"]
            p_sign = get_sign(lon)
            p_house = ((p_sign - chart.lagna_sign + 12) % 12) + 1
            nak, pada, abbr = get_nakshatra_pada(lon)
            sun_lon = chart.planets["Sun"]["longitude"]
            avastha = get_planetary_avastha(p, lon, pdata, sun_lon, chart.planets)
            speed_str = f"{pdata['speed']:.4f}"
            if pdata["speed"] < 0:
                speed_str += " (Retro)"
                
            rows.append({
                "Planet / Body": p,
                "House": p_house,
                "Rashi (Sign)": get_sign_name(p_sign),
                "Nakshatra": nak,
                "Pada": pada,
                "State (Avastha)": avastha,
                "Longitude": format_longitude(lon),
                "Speed (deg/day)": speed_str
            })
            
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
    with tab2:
        st.markdown("##### Shatpanchasika Chapters I-VII Specific Predictions")
        shat_preds = eval_res.get("shatpanchasika_predictions", [])
        if shat_preds:
            for p in shat_preds:
                st.markdown(f"""
                <div class='glass-card' style='margin-bottom: 0.75rem; padding: 1rem;'>
                    <strong>Category:</strong> <span style='color: #22d3ee;'>{p.get('category')}</span><br>
                    <strong>Prediction:</strong> {p.get('prediction')}<br>
                    <small style='color: #9ca3af;'>Rule Basis: {p.get('rule')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No specific Shatpanchasika rules apply to this house query.")
            
    with tab3:
        st.markdown("##### Tajaka Aspects & Combustions Log")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("##### Active Applying/Separating Aspects")
            yogas = eval_res.get("yogas", [])
            if yogas:
                for y in yogas:
                    st.markdown(f"- **{y.get('yoga_name')}**: {y.get('description')}")
            
            # Print direct relation details
            rel = eval_res.get("direct_relationship")
            if rel:
                st.markdown(f"- **Direct Aspect**: {rel.get('aspect_type')} between Lagnapathi and Karyesa (Strength: `{rel.get('strength')}`, Applying: `{rel.get('is_applying')}`)")
            else:
                st.markdown("- **Direct Aspect**: No direct applying aspect exists between Lagnapathi and Karyesa.")
                
        with col_t2:
            st.markdown("##### Combustion (Mushita) Analysis")
            sun_lon = chart.planets["Sun"]["longitude"]
            for p, pdata in chart.planets.items():
                if p == "Sun" or p in ["Rahu", "Ketu"]:
                    continue
                diff = abs(pdata["longitude"] - sun_lon) % 360
                if diff > 180:
                    diff = 360 - diff
                comb_limit = {"Mars": 12.0, "Mercury": 8.0, "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0}.get(p, 9.0)
                is_comb = diff <= comb_limit
                status = "<span style='color: #f87171;'>Combust (Mushita)</span>" if is_comb else "<span style='color: #34d399;'>Safe</span>"
                st.markdown(f"- **{p}**: Orb {diff:.2f}° / Limit {comb_limit}° | {status}", unsafe_allow_html=True)
else:
    st.info("👈 Set the time, date, location, and type your question in the sidebar, then click 'Analyze Prasna Chart' to compute calculations.")
