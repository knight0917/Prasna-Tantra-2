import math
from datetime import datetime
import libephemeris as swe

# Nakshatra Names and Abbreviation tables
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRAS_ABBR = [
    "Aswi", "Bhar", "Krit", "Rohi", "Mrig", "Ardr", "Puna", "Push", "Asle",
    "Magh", "PPha", "UPha", "Hast", "Chit", "Swat", "Vish", "Anur", "Jyes",
    "Mool", "PAsh", "UAsh", "Shra", "Dhan", "Sata", "PBha", "UBha", "Reva"
]

def parse_coord(coord_str):
    """Parses a coordinate string (DD:MM:SS) or decimal string into float degrees."""
    try:
        return float(coord_str)
    except ValueError:
        parts = coord_str.split(':')
        if len(parts) == 3:
            deg = float(parts[0])
            min_part = float(parts[1])
            sec_part = float(parts[2])
            sign = -1.0 if deg < 0 or parts[0].strip().startswith('-') else 1.0
            return sign * (abs(deg) + min_part/60.0 + sec_part/3600.0)
        return 0.0

def get_ayanamsha(jd, ayanamsha_mode="Lahiri"):
    """
    Calculates the Ayanamsha using the Swiss Ephemeris library based on mode.
    """
    if ayanamsha_mode.lower() == "raman":
        swe.set_sid_mode(swe.SIDM_RAMAN, 0.0, 0.0)
    else:
        swe.set_sid_mode(swe.SIDM_LAHIRI_1940, 0.0, 0.0)
    return swe.get_ayanamsa_ut(jd)

def get_nakshatra_pada(longitude):
    """
    Calculates the Nakshatra name, abbreviation, and Pada (1-4) for a sidereal longitude.
    """
    total_padas = int(longitude / (10.0 / 3.0))
    nakshatra_idx = total_padas // 4
    pada_num = (total_padas % 4) + 1
    nakshatra_idx = max(0, min(26, nakshatra_idx))
    return NAKSHATRAS[nakshatra_idx], pada_num, NAKSHATRAS_ABBR[nakshatra_idx]

def calculate_lagna(utc_datetime_str, lat_str, lon_str, ayanamsha_mode="Lahiri"):
    """
    Calculates the tropical and sidereal Lagna (Ascendant) using Swiss Ephemeris houses.
    """
    dt = datetime.strptime(utc_datetime_str, "%Y/%m/%d %H:%M:%S")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
    
    lat_deg = parse_coord(lat_str)
    lon_deg = parse_coord(lon_str)
    
    # Set sidereal mode based on ayanamsha_mode
    if ayanamsha_mode.lower() == "raman":
        swe.set_sid_mode(swe.SIDM_RAMAN, 0.0, 0.0)
    else:
        swe.set_sid_mode(swe.SIDM_LAHIRI_1940, 0.0, 0.0)
    ayanamsha = swe.get_ayanamsa_ut(jd)
    
    # Calculate houses (Whole Sign system 'W')
    cusps, ascmc = swe.houses(jd, lat_deg, lon_deg, ord('W'))
    lagna_tropical = ascmc[0]
    lagna_sidereal = (lagna_tropical - ayanamsha) % 360
    
    # LST (Local Sidereal Time) in degrees is the ARMC (ascmc[2])
    lst_deg = ascmc[2]
    
    return {
        "tropical": lagna_tropical,
        "sidereal": lagna_sidereal,
        "ayanamsha": ayanamsha,
        "lst": lst_deg
    }

def get_planetary_positions(utc_datetime_str, ayanamsha, ayanamsha_mode="Lahiri"):
    """
    Calculates high-precision geocentric sidereal positions of planets and Moon's nodes.
    Uses Swiss Ephemeris calc_ut with FLG_SIDEREAL flag.
    """
    dt = datetime.strptime(utc_datetime_str, "%Y/%m/%d %H:%M:%S")
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
    
    # Set sidereal mode based on ayanamsha_mode
    if ayanamsha_mode.lower() == "raman":
        swe.set_sid_mode(swe.SIDM_RAMAN, 0.0, 0.0)
    else:
        swe.set_sid_mode(swe.SIDM_LAHIRI_1940, 0.0, 0.0)
    
    bodies = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Rahu": swe.MEAN_NODE
    }
    
    positions = {}
    
    # 1. Physical Planets and Rahu
    for name, p_id in bodies.items():
        pos, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        lon_sid = pos[0]
        speed = pos[3]
        positions[name] = {
            "longitude": lon_sid,
            "speed": speed,
            "is_retrograde": speed < 0.0
        }
        
    # 2. Ketu (exactly opposite of Rahu)
    rahu_sid = positions["Rahu"]["longitude"]
    rahu_speed = positions["Rahu"]["speed"]
    positions["Ketu"] = {
        "longitude": (rahu_sid + 180.0) % 360,
        "speed": rahu_speed,
        "is_retrograde": rahu_speed < 0.0
    }
    
    return positions

def get_house_cusps(lagna_sidereal):
    lagna_sign = int(lagna_sidereal / 30)
    houses = {}
    for house_num in range(1, 13):
        sign = (lagna_sign + house_num - 1) % 12
        houses[house_num] = {
            "sign": sign,
            "start_longitude": sign * 30.0,
            "end_longitude": ((sign + 1) * 30.0) % 360
        }
    return houses

def get_sign_name(sign_index):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[sign_index]
