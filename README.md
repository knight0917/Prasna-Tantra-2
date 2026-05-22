# ✦ Prasna Tantra - Vedic Horary Astrology Engine ✦

A premium, classical Vedic Horary Astrology (Prasna) analysis engine and interactive dashboard based on the authoritative texts **Prasna Tantra** (by Sri Neelakanta, translated by Bangalore Venkata Raman) and **Shatpanchasika** (by Prithuyasas).

🚀 **Live Application URL**: [https://prasna-tantra-2-eqcdmsstvnm6buvdjcjfad.streamlit.app](https://prasna-tantra-2-eqcdmsstvnm6buvdjcjfad.streamlit.app)

---

## 🌌 Classical Astrological Features

- **Automated House Mapping**: Translates natural language queries (e.g., *"Will I get my lost gold back?"*, *"Will I travel abroad?"*) into their corresponding astrological houses.
- **Tajaka Yoga Analysis**: Dynamically computes classical applying and separating aspects (Ithasala, Easarapha, Induvara, Ishrafe, etc.) between the Lagna lord (Lagnapathi) and the query lord (Karyesa).
- **Kalapinda Timing Method**: Calculates the exact event fructification timeline according to *Prasna Tantra* Chapter IV (Stanzas 15-19) using equinoctial midday shadow ($12 \times \tan(|\phi|)$) calibration and sequential planetary Gunaka deductions.
- **Query Object Identification (Dhatu / Moola / Jeeva)**: 
  - **Method A (Rising Navamsa)**: Odd/even Navamsa division classification.
  - **Method B (Navamsa Aspect Rule)**: Aspect matching of planetary owners to trines in the Navamsa chart (*Shatpanchasika* Stanzas 25-26).
- **Mushita (Combustion) & Planetary Strength**: Automatic detection of planetary combustion limits relative to the Sun.
- **Specialized House Rules**: Tailored evaluations for health/undertakings (1st), wealth/returns (2nd), travel intentions (6th/7th/8th), wishes realization (11th), and more.

---

## 🛠️ Installation & Local Setup

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/knight0917/Prasna-Tantra-2.git
cd Prasna-Tantra-2
```

### 3. Install Dependencies
Install all package requirements:
```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit Application
Launch the web interface locally:
```bash
streamlit run streamlit_app.py
```
The app will open automatically in your browser (typically at `http://localhost:8501`).

---

## 🧪 Verification & Testing

Verify the engine computations by running the test suite:
```bash
python -m unittest test_engine.py
```
The suite includes tests for coordinates parsing, shadow length calculations, Tajaka yogas, Shatpanchasika predictions, and the classical book examples for Kalapinda timing.

---

## ✉️ Contact & Feedback
For questions, support, or feedback, please contact:
- **Email**: [ankitkusingh@zohomail.eu](mailto:ankitkusingh@zohomail.eu)
