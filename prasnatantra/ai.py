import os
import json
import requests

def load_groq_key():
    """Loads the Groq API key from environment variables or a local .env file."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
        
    # Look for .env in current and parent directories
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for path in [current_dir, os.path.dirname(current_dir), os.path.dirname(os.path.dirname(current_dir))]:
        env_path = os.path.join(path, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GROQ_API_KEY="):
                        val = line.strip().split("=", 1)[1].strip()
                        # Strip optional quotes
                        if val.startswith('"') and val.endswith('"'):
                            val = val[1:-1]
                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1]
                        return val
    return None

def query_groq(payload):
    """Sends a request to the Groq completions endpoint with retry logic and exponential backoff."""
    import time
    key = load_groq_key()
    if not key:
        raise ValueError("GROQ_API_KEY not found. Please set it in your environment or in a .env file.")
        
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            # Handle rate limits (429) or temporary server errors (5xx)
            status_code = response.status_code
            if isinstance(status_code, int) and (status_code == 429 or status_code >= 500):
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to communicate with Groq API after {max_retries} attempts: {e}")
            time.sleep(base_delay * (2 ** attempt))

def query_groq_stream(payload):
    """Sends a request to the Groq completions endpoint and yields chunks of text in real-time with retries."""
    import time
    key = load_groq_key()
    if not key:
        raise ValueError("GROQ_API_KEY not found. Please set it in your environment or in a .env file.")
        
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = dict(payload)
    payload["stream"] = True  # Force stream mode
    
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20, stream=True)
            status_code = response.status_code
            if isinstance(status_code, int) and (status_code == 429 or status_code >= 500):
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
            
            response.raise_for_status()
            
            # Yield streaming chunks
            for line in response.iter_lines():
                if not line:
                    continue
                line_str = line.decode("utf-8").strip()
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_str)
                        delta = chunk_data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
            return  # Successful stream completion
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to stream from Groq API after {max_retries} attempts: {e}")
            time.sleep(base_delay * (2 ** attempt))

def map_question_to_house(question: str) -> dict:
    """
    Analyzes a free-text question using Groq LLM to map it to the most relevant
    Vedic astrological house (1 to 12) based on Tajaka/Prasna principles.
    Uses robust JSON schema validation and safe fallbacks.
    """
    system_prompt = """You are an expert Vedic Horary Astrologer. Your task is to map a user's natural language question to the single most relevant astrological house (from 1 to 12).
    
    Here are the core house significations:
    - House 1 (Lagna): Health, longevity, physical body, general outlook, appearance, past/present/future, start of new ventures.
    - House 2: Wealth, finance, money, profits, family assets, personal possessions.
    - House 3: Brothers, sisters, short journeys, writing, communication, courage, rumors, messages, news.
    - House 4: Mother, home, real estate, lands, crops, agriculture, vehicles, peace of mind, purchase/sale of property and transaction base.
    - House 5: Romance, emotional attachment, pre-marital courtship, children, pregnancy, education, intellect, speculation. (Map love/attraction/courtship queries here if the focus is on courtship or emotional bond, but prefer House 7 for committed marriage/union).
    - House 6: Service, employment under a master, servants, daily jobs, illness, disease recovery, debts, enemies, disputes, hunting/expedition risk. (Map career/job changes or employee-employer relations here if focused on service/employment under a master, but prefer House 10 for general career status/promotions).
    - House 7: Marriage, committed spouse/partner, union, love affairs (committed union), enquiry about women/feminine counterpart, disputes, partnerships, trade, foreign travel/spouse return.
    - House 8: Death, danger, longevity, inheritance, hidden secrets, lost wealth.
    - House 9: Religion, pilgrimages, long journeys, father, higher knowledge, good fortune, righteousness.
    - House 10: Career, profession, high-status jobs, business, promotions, status, government, authority.
    - House 11: Realization of desires, financial gains, honors, friendships.
    - House 12: Expenditure, losses, captivity/imprisonment/detention, release, foreign travel/settlement.

    Return your response strictly in JSON format with the following keys:
    {
        "house": <int, between 1 and 12>,
        "category_name": "<str, name of mapped domain>",
        "explanation": "<str, 1-2 sentences explaining why this house is chosen>"
    }
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Map this question: '{question}'"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }
    
    def infer_special_category(question_text: str, house_num: int):
        q = question_text.lower()
        if any(k in q for k in ["dream", "sleep"]):
            return "dreams"
        if any(k in q for k in ["ship", "voyage", "sea", "boat", "vessel"]):
            return "ships"
        if any(k in q for k in ["rumour", "rumor", "news", "hearsay", "report"]):
            return "rumours"
        if any(k in q for k in ["sexual", "intimacy", "union", "adultery", "copulation"]):
            return "sexual_matters"
        if any(k in q for k in ["hunt", "hunting", "expedition", "game"]):
            return "hunting"
        if any(k in q for k in ["prison", "jail", "custody", "incarceration", "detention", "captivity"]):
            return "incarceration"
        if any(k in q for k in ["woman", "women", "lady", "female", "her nature"]):
            return "women_enquiry"
        if any(k in q for k in ["purchase", "buy", "sale", "sell", "transaction", "acquisition"]):
            return "purchase_sale"
        if house_num == 12:
            return "deity_curse"
        if house_num == 6:
            return "master_servant"
        if house_num == 4:
            return "crops_trade"
        if house_num == 8:
            return "disputes"
        return None

    try:
        res = query_groq(payload)
        content_str = res["choices"][0]["message"]["content"]
        data = json.loads(content_str)
        
        # Safe schema validation
        house = int(data.get("house", 1))
        if house < 1 or house > 12:
            house = 1
            
        special_category = infer_special_category(question, house)
        return {
            "house": house,
            "category_name": str(data.get("category_name", "General Outlook")),
            "explanation": str(data.get("explanation", "Mapped by AI Horary Classifier.")),
            "special_category": special_category
        }
    except Exception as e:
        # Graceful fallback to prevent crashes on invalid LLM responses
        fallback_house = 1
        return {
            "house": fallback_house,
            "category_name": "General Outlook",
            "explanation": f"Fallback to House 1 due to mapping error: {e}",
            "special_category": infer_special_category(question, fallback_house)
        }

def generate_astrological_reading(question: str, chart_details: dict):
    """
    Generates a rich, personalized Vedic astrological reading based on calculated
    astronomical positions, aspects, yogas, and success score.
    Yields chunks of text in real-time as they are streamed.
    """
    system_prompt = """You are a master Vedic Horary (Tajaka/Prasna) Astrologer. You interpret query evaluations in the authentic style of Sri Neelakanta's *Prasna Tantra* and Prithuyasas's *Shatpanchasika*.
    
    Explain the results to the client. Keep the tone professional, mystical, and reassuring, yet clear and structured.
    
    CRITICAL Horary Interpretation Rule (Cross-Referencing Related Houses):
    - For **Love, Courtship, and Marriage** queries: You MUST analyze and cross-reference both House 5 (governing pre-marital courtship, romance, emotions, and affection) and House 7 (governing committed union, marriage, and partner). Check Venus as the karaka for relationships and its condition.
    - For **Job, Service, and Career** queries: You MUST analyze and cross-reference both House 10 (governing career status, profession, rank, and promotions) and House 6 (governing service, employment under an employer/master, and daily work). Explain the relationship between Lagna (the employee) and the 10th/6th/12th houses (signifying master, service, and change).
    
    Structure the reading exactly as follows:
    1. **The Pronouncement (Karyasiddhi)**: A direct, unambiguous answer to their question. State whether the goal will be realized, and the level of success probability. Explicitly acknowledge the question number (e.g., "For your Question #2...") and state the celestial body used as the starting reference point for counting houses (e.g., "counting from the Moon").
    2. **Astrological Rationale**: Explain the mathematical/astrological configurations that decided this outcome. Speak of:
       - The shift in the starting reference point: explain why Vedic Horary astrology shifts the starting reference point (Lagna for 1st query, Moon for 2nd query, Sun for 3rd query, Jupiter for 4th query, etc.) to evaluate subsequent questions from the same chart.
       - The Lagnapathi (Lord of Ascendant/Reference point, representing the querent) and the Karyesa (Lord of the house of query, representing the object in view).
       - Their respective signs, positions, and planetary conditions (Avasthas, e.g. Deeptha/Exalted, Swastha/Own sign, Deena/Debilitated, Mushita/Combust).
       - Active aspects or Tajaka Yogas (e.g. Ithasala/Applying, Easarapha/Separating, Nakta, Yamaya, Kamboola).
       - The specific Shatpanchasika predictions (e.g., child gender, insider/outsider theft details, lost property direction/distance, travel timing, or rain/weather indicators).
       - The specialized Prasna Tantra Chapter III outcomes (Deity curse details, master-servant loyalty/retention, dietary tastes, sports contest strengths, lawsuit arbitration/verdicts, crop directions/famines, and trade price volatility).
    3. **Timing of Event**: Explain when the outcome is expected to unfold, based on the degree differences, sign multiplications, or Shatpanchasika timing methods.
    4. **Remedial Guidance**: Offer brief Vedic wisdom or practical advice based on the planetary alignments.
    """
    
    # Strip down chart_details to keep token count clean while retaining all astrological info
    summary_data = {
        "query_num": chart_details.get("query_num", 1),
        "house": chart_details.get("house"),
        "ref_point": chart_details.get("ref_point_name"),
        "ref_sign": chart_details.get("ref_sign_name"),
        "query_sign": chart_details.get("query_sign_name"),
        "lagnapathi": chart_details.get("lagnapathi"),
        "karyesa": chart_details.get("karyesa"),
        "success_probability": chart_details.get("success_probability"),
        "score_pct": chart_details.get("score_pct"),
        "timing": chart_details.get("timing"),
        "details": chart_details.get("details"),
        "direct_relationship": chart_details.get("direct_relationship"),
        "yogas": chart_details.get("yogas"),
        "shatpanchasika_predictions": chart_details.get("shatpanchasika_predictions"),
        "lost_property_analysis": chart_details.get("lost_property_analysis"),
        "traveler_analysis": chart_details.get("traveler_analysis"),
        "misc_analysis": chart_details.get("misc_analysis")
    }
    
    user_prompt = f"""
    Client's Question: "{question}"
    
    Astrological Engine Output:
    {json.dumps(summary_data, indent=2)}
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.5
    }
    
    return query_groq_stream(payload)
