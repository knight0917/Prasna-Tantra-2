import os
import sys
from datetime import datetime
from tabulate import tabulate
from prasnatantra import PrasnaChart, SIGN_LORDS
from prasnatantra.astronomy import get_sign_name, get_nakshatra_pada
from prasnatantra.tajaka import get_planetary_avastha
from prasnatantra.ai import map_question_to_house, generate_astrological_reading, load_groq_key

# Mapping of query types to house numbers
QUERY_MAP = {
    1: ("Health, Longevity, General Outlook, Past/Present/Future", 1),
    2: ("Wealth, Finance, Money, Profits, Financial Gains", 2),
    3: ("Brothers, Sisters, Travels, News, Messages", 3),
    4: ("Land, Home, Vehicles, Mother, Immovable Property", 4),
    5: ("Children, Pregnancy, Speculation, Twins, Legitimacy", 5),
    6: ("Disease, Illness, Servants, Obstacles, Maternal Uncle", 6),
    7: ("Marriage, Spouse, Wife's Return, Disputes, Partnerships, Trade", 7),
    8: ("War, Defeat, Death, Lost Wealth, Longevity", 8),
    9: ("Long Journeys, Pilgrimages, Religion, Righteousness", 9),
    10: ("Profession, Career, Job Change, Promotion, Success", 10),
    11: ("Financial Gains, Honors, Realization of Desires", 11),
    12: ("Captivity, Release, Expenditure, Loss", 12)
}

# Special Prasna Tantra Chapter III Queries
SPECIAL_QUERY_MAP = {
    13: ("Curse of Deities (Misfortune, Disease, Divine Anger)", 12, "deity_curse"),
    14: ("Master-Servant Relations / Job Change / Employer Support", 6, "master_servant"),
    15: ("Meals & Dietary Queries (Quality of food, tastes, missing meals)", 1, "meals"),
    16: ("Sports & Contests (Querent/Home Team vs. Opponent/Away Team)", 7, "sports"),
    17: ("Disputes & Lawsuits (Querent vs. Defendant, Arbitrator, Final Verdict)", 8, "disputes"),
    18: ("Crops, Purchase/Sale & Trade (Agriculture yields, price trends, transactions)", 4, "crops_trade")
}

def format_longitude(deg):
    """Formats decimal degrees into Dd Mm Ss format."""
    d = int(deg)
    m = int((deg - d) * 60)
    s = int(((deg - d) * 60 - m) * 60)
    return f"{d}d {m}m {s}s"

def print_premium_header(title):
    print("=" * 65)
    print(f" {title.upper()} ".center(65, "*"))
    print("=" * 65)

def run_cli():
    print_premium_header("Sri Neelakanta's Prasna Tantra Engine")
    print("This engine computes astrological positions using the Swiss Ephemeris")
    print("and evaluates horary queries using Tajaka rules.")
    print("-" * 65)
    
    # Get user inputs with defaults for easy testing
    print("\n[STEP 1: Enter Birth / Query Details]")
    
    # Date
    default_date = datetime.now().strftime("%Y-%m-%d")
    date_input = input(f"Enter local date (YYYY-MM-DD) [Default: {default_date}]: ").strip()
    if not date_input:
        date_input = default_date
        
    # Time
    default_time = datetime.now().strftime("%H:%M:%S")
    time_input = input(f"Enter local time (HH:MM:SS) [Default: {time_input if 'time_input' in locals() else default_time}]: ").strip()
    if not time_input:
        time_input = default_time
        
    # Timezone
    default_tz = "5.5" # India
    tz_input = input(f"Enter timezone offset in hours East (e.g. +5.5 for India, -5 for EST) [Default: {default_tz}]: ").strip()
    if not tz_input:
        tz_input = default_tz
    tz_offset = float(tz_input)
    
    # Latitude
    default_lat = "12:58:18" # Bangalore
    lat_input = input(f"Enter Latitude (DD:MM:SS N/S or decimal) [Default: {default_lat} (Bangalore)]: ").strip()
    if not lat_input:
        lat_input = default_lat
        
    # Longitude
    default_lon = "77:35:41" # Bangalore
    lon_input = input(f"Enter Longitude (DD:MM:SS E/W or decimal) [Default: {default_lon} (Bangalore)]: ").strip()
    if not lon_input:
        lon_input = default_lon
        
    # Parse date/time
    try:
        local_dt = datetime.strptime(f"{date_input} {time_input}", "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        print(f"\n[ERROR] Invalid date/time format: {e}. Exiting.")
        return
        
    print("\n[Calculating chart...]")
    chart = PrasnaChart(local_dt, lat_input, lon_input, tz_offset)
    
    # Print General Chart Info
    print_premium_header("Chart Details")
    print(f"Local Time : {chart.local_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC {tz_offset:+.1f}h)")
    print(f"UTC Time   : {chart.utc_str}")
    print(f"Coordinates: Lat {lat_input}, Lon {lon_input}")
    print(f"Ayanamsha  : {format_longitude(chart.ayanamsha)} (Lahiri)")
    lag_nak, lag_pada, lag_abbr = get_nakshatra_pada(chart.lagna_sidereal)
    print(f"Lagna      : {format_longitude(chart.lagna_sidereal)} in {get_sign_name(chart.lagna_sign)} ({lag_nak} - {lag_pada}) (Lagnapathi: {chart.lagnapathi})")
    
    # Sincerity Check Result
    print("\n" + "-"*65)
    print(" Sincerity Check ".center(65, "-"))
    sinc = chart.sincerity
    if sinc["is_sincere"]:
        print(">> STATUS: Sincere Query. Predictions are reliable.")
        if sinc["reasons_sincere"]:
            print("Indicators:")
            for r in sinc["reasons_sincere"]:
                print(f"  * {r}")
    else:
        print(">> WARNING: Insincere Query. The chart indicates testing/fun.")
        if sinc["reasons_insincere"]:
            print("Indicators:")
            for r in sinc["reasons_insincere"]:
                print(f"  ! {r}")
    print("-"*65)

    # Planets Table
    planet_headers = ["Planet/Point", "Longitude (Sidereal)", "Sign Position", "Nakshatra - Pada", "Speed (deg/day)", "Avastha"]
    planet_rows = []
    
    # 1. Add Ascendant (Lagna) Row
    lag_nak, lag_pada, lag_abbr = get_nakshatra_pada(chart.lagna_sidereal)
    lag_sign_deg = chart.lagna_sidereal % 30
    lag_sign_name = get_sign_name(chart.lagna_sign)
    planet_rows.append([
        "Ascendant (Lagna)",
        format_longitude(chart.lagna_sidereal),
        f"{lag_sign_name} {lag_sign_deg:.2f} deg",
        f"{lag_nak} - {lag_pada}",
        "-",
        "-"
    ])
    
    sun_lon = chart.planets["Sun"]["longitude"]
    for p_name, p_data in chart.planets.items():
        lon = p_data["longitude"]
        sign_idx = int(lon / 30)
        sign_deg = lon % 30
        sign_name = get_sign_name(sign_idx)
        sign_pos_str = f"{sign_name} {sign_deg:.2f} deg"
        
        nak_name, pada, nak_abbr = get_nakshatra_pada(lon)
        nak_str = f"{nak_name} - {pada}"
        
        speed_str = f"{p_data['speed']:.2f}"
        if p_data["is_retrograde"]:
            speed_str += " (R)"
            
        avastha = get_planetary_avastha(p_name, lon, p_data, sun_lon, chart.planets)
        
        planet_rows.append([
            p_name,
            format_longitude(lon),
            sign_pos_str,
            nak_str,
            speed_str,
            avastha
        ])
    
    print("\nPLANETARY & ASCENDANT POSITIONS:")
    print(tabulate(planet_rows, headers=planet_headers, tablefmt="grid"))
    
    # Houses Table
    house_headers = ["House", "Rasi Sign", "House Lord", "Occupying Planets"]
    house_rows = []
    
    # Pre-map planets to their house numbers
    lagna_sign = chart.lagna_sign
    house_occupants = {h: [] for h in range(1, 13)}
    house_occupants[1].append("Ascendant")
    
    for p_name, p_data in chart.planets.items():
        p_lon = p_data["longitude"]
        p_sign = int(p_lon / 30.0) % 12
        h_idx = (p_sign - lagna_sign) % 12 + 1
        house_occupants[h_idx].append(p_name)
        
    for h_num, h_data in chart.houses.items():
        sign_name = get_sign_name(h_data["sign"])
        lord_name = SIGN_LORDS[h_data["sign"]]
        occupants = house_occupants[h_num]
        occupants_str = ", ".join(occupants) if occupants else "-"
        house_rows.append([f"House {h_num}", sign_name, lord_name, occupants_str])
        
    print("\nHOUSE SYSTEM:")
    print(tabulate(house_rows, headers=house_headers, tablefmt="grid"))

    # Query Evaluation Loop
    query_counter = 1
    has_groq_key = load_groq_key() is not None
    
    while True:
        print("\n" + "=" * 65)
        print("[STEP 2: Select Query Category]")
        print("=" * 65)
        for key, value in QUERY_MAP.items():
            print(f"[{key:2d}] {value[0]}")
        print("\nSpecial Prasna Tantra Chapter III Queries:")
        for key, value in SPECIAL_QUERY_MAP.items():
            print(f"[{key:2d}] {value[0]}")
        print("\nAI Assistance:")
        if has_groq_key:
            print("[19] Ask AI (Free Text Question - AI Mapped & Interpreted) *Active*")
        else:
            print("[19] Ask AI (Free Text Question - Needs GROQ_API_KEY)")
        print("[ 0] Exit")
        
        try:
            choice = int(input("\nEnter category number: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue
            
        if choice == 0:
            print("\nThank you for using the Prasna Tantra Engine. Om Tat Sat.")
            break
            
        special_cat = None
        if choice == 19:
            if not load_groq_key():
                print("\n[ERROR] Groq API Key is not set. Please set the GROQ_API_KEY environment variable or write it in .env file.")
                continue
            question = input("\nEnter your question: ").strip()
            if not question:
                print("Question cannot be empty.")
                continue
            print("\n[AI is analyzing your question...]")
            try:
                mapping = map_question_to_house(question)
                house_num = mapping["house"]
                category_name = mapping["category_name"]
                
                # Check if mapped category matches any special rules
                for skey, sval in SPECIAL_QUERY_MAP.items():
                    if sval[1] == house_num:
                        special_cat = sval[2]
                        break
                print(f"\nAI Mapping Success:")
                print(f"  * Mapped House  : House {house_num} ({category_name})")
                if special_cat:
                    print(f"  * Special Rules : Active ({special_cat})")
                print(f"  * Rationale     : {mapping['explanation']}")
            except Exception as e:
                print(f"\n[AI Error] Could not map question to house: {e}. Defaulting to House 1.")
                house_num = 1
                category_name = QUERY_MAP[1][0]
                question = "General outlook"
        elif choice in QUERY_MAP:
            category_name, house_num = QUERY_MAP[choice]
            question = None
        elif choice in SPECIAL_QUERY_MAP:
            category_name, house_num, special_cat = SPECIAL_QUERY_MAP[choice]
            question = None
        else:
            print("Invalid category. Please select from the menu.")
            continue
            
        res = chart.evaluate_query(house_num, query_num=query_counter, special_category=special_cat)
        
        print(f"\nEvaluating Query #{query_counter}: {category_name} (House {house_num})")
        print(f"Reference Point    : {res['ref_point_name']} (Sign: {res['ref_sign_name']})")
        print(f"Target Query Sign  : {res['query_sign_name']}")
        
        # Query-Specific Sincerity Check Result
        print("\n" + "-"*65)
        print(f" Sincerity Check (Query #{query_counter}) ".center(65, "-"))
        sinc = res.get("sincerity", {"is_sincere": True, "reasons_sincere": [], "reasons_insincere": []})
        if sinc["is_sincere"]:
            print(">> STATUS: Sincere Query. Predictions are reliable.")
            if sinc["reasons_sincere"]:
                print("Indicators:")
                for r in sinc["reasons_sincere"]:
                    print(f"  * {r}")
        else:
            print(">> WARNING: Insincere Query. The chart indicates testing/fun.")
            if sinc["reasons_insincere"]:
                print("Indicators:")
                for r in sinc["reasons_insincere"]:
                    print(f"  ! {r}")
        print("-"*65)
        print("-" * 65)
        
        print(f"Lagnapathi (Querent)      : {res['lagnapathi']}")
        print(f"Karyesa (Query Signifier) : {res['karyesa']}")
        print(f"Success Probability       : {res['success_probability']}")
        print(f"Calculated Score          : {res['score_pct']}%")
        print(f"Estimated Fructification  : {res['timing']}")
        
        print("\nEvaluation Details:")
        for det in res["details"]:
            print(f"  * {det}")
            
        if "shatpanchasika_predictions" in res and res["shatpanchasika_predictions"]:
            print("\nShatpanchasika Predictions:")
            for sp_pred in res["shatpanchasika_predictions"]:
                print(f"  * [{sp_pred['category']}] {sp_pred['prediction']} (Rule: {sp_pred['rule']})")
            
        if res["direct_relationship"]:
            rel = res["direct_relationship"]
            friendliness = "Openly Friendly" if rel['is_friendly'] == True else ("Secretly Friendly" if rel['is_friendly'] is not None else "Neutral/Conjunction")
            if rel['is_friendly'] == False:
                friendliness = "Secretly Hostile" if rel['aspect_type'] == "Opposition" else "Openly Hostile"
            print(f"\nDirect Aspect Found: {rel['aspect_type']} ({rel['angle']} deg) - {friendliness}")
            print(f"  * Aspect Strength: {int(rel['strength'] * 100)}%")
            print(f"  * Orb Separation : {rel['orb_diff']:.2f} deg")
            print(f"  * Aspect Status  : {'Applying (Ithasala)' if rel['is_applying'] else 'Separating (Easarapha)'}")
            print(f"  * Completion     : {'Poorna (Complete)' if rel['is_complete'] else 'Approaching'}")
            
        if res["yogas"]:
            print("\nActive Tajaka Yogas:")
            for yoga in res["yogas"]:
                print(f"  * {yoga['name']}:")
                if yoga["name"] in ["Nakta Yoga", "Yamaya Yoga"]:
                    for item in yoga["details"]:
                        print(f"    - Intermediary translation via {item['translator']}")
                        
        if choice == 19 and question:
            print("\n" + "=" * 65)
            print(" AI ASTROLOGICAL INTERPRETATION ".center(65, "*"))
            print("=" * 65)
            print("[AI is generating reading (streaming)...]")
            try:
                for chunk in generate_astrological_reading(question, res):
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
                print()  # Add a trailing newline
            except Exception as e:
                print(f"\n[AI Error] Could not generate reading: {e}")
            print("=" * 65)
            
        query_counter += 1

if __name__ == "__main__":
    run_cli()
