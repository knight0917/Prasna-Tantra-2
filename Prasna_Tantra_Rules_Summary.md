# Sri Neelakanta's Prasna Tantra (Horary Astrology) - Rules & Calculations Summary

This document serves as the primary technical reference for Sri Neelakanta's *Prasna Tantra*, translated by Bangalore Venkata Raman. It outlines the mathematical calculations, aspects, orbs of influence (Deepthamsas), planetary conditions (Avasthas), Tajaka Yogas, and house-wise evaluation rules required to build a Python horary astrology engine.

---

## 1. PRELIMINARIES & QUERY EVALUATION

### Sincerity of the Querent
Before answering any query, the astrologer must verify if the query is sincere or put forth for fun/testing:
- **Insincere Intent (Query fails / reject prediction)**:
  - The Moon is in the Ascendant (Lagna), Saturn is in a quadrant (Kendra: 1st, 4th, 7th, or 10th), and Mercury is combust.
  - Mars and Mercury aspect the Moon in the Ascendant.
  - A natural malefic (Sun, Mars, Saturn, Rahu, Ketu) joins the Ascendant (without benefic aspects).
  - Jupiter or Mercury cast an inimical aspect (square or opposition) on the lord of the 7th.
- **Sincere Intent (Proceed with prediction)**:
  - A benefic (Jupiter, Venus, unafflicted Mercury, waxing Moon) joins the Ascendant.
  - Mars or a full Moon and Jupiter aspect the Ascendant.
  - Jupiter or Mercury cast a friendly aspect (trine or sextile) on the lord of the 7th.

### Answering Multiple Queries
If a querent asks more than one question at the same moment:
1. **1st Question**: Read from the Ascendant (Lagna) and its lord.
2. **2nd Question**: Read from the sign occupied by the Moon and its lord.
3. **3rd Question**: Read from the sign occupied by the Sun and its lord.
4. **4th Question**: Read from the sign occupied by Jupiter and its lord.
5. **5th Question**: Read from the sign occupied by Mercury or Venus (whichever is stronger) and its lord.

*Note: Classic horary dictates that only one query should ideally be answered per chart to ensure maximum accuracy.*

---

## 2. TAJAKA ASPECTS & ORBS OF INFLUENCE

Prasna Tantra relies entirely on the **Tajaka system** of aspects, which differ significantly from standard Parasari aspects.

### Tajaka Aspects
Aspects are calculated based on the house positions relative to each other:
1. **Trine (5th / 9th houses - 120°)**: 75% strength. Openly friendly, highly auspicious.
2. **Sextile (3rd / 11th houses - 60°)**: Secretly friendly.
   - Aspect on 3rd house: 40% strength.
   - Aspect on 11th house: 10% strength.
3. **Square (4th / 10th houses - 90°)**: Openly hostile/inimical. 45% strength. Causes obstacles, though the event may eventually happen with effort.
4. **Opposition (1st / 7th houses - 180°)**: Openly hostile/inimical. 100% strength. Extremely unfavorable; denotes failure or destruction.
5. **Conjunction (0°)**: Favorable with benefics, unfavorable with malefics.

### Deepthamsas (Orbs of Operation)
Unlike Western aspects which use aspect-specific orbs, Tajaka uses **planet-specific orbs**. Two planets form an aspect only if their distance is within the average of their combined orbs.

| Planet | Orb of Operation (Deepthamsa) |
| :--- | :--- |
| **Sun** | 15° |
| **Moon** | 12° |
| **Mars** | 8° (or 7°) |
| **Mercury** | 7° |
| **Jupiter** | 9° |
| **Venus** | 7° |
| **Saturn** | 9° (or 8°) |

**Aspect Validity Calculation:**
$$\text{Max Allowable Orb} = \frac{\text{Orb}(\text{Planet}_1) + \text{Orb}(\text{Planet}_2)}{2}$$
*Example: For an aspect between the Sun (15°) and Moon (12°), they must be within $(15 + 12) / 2 = 13.5°$ of the exact aspect angle (e.g., 0°, 60°, 90°, 120°, 180°).*

### Combustion Orbs (Asta)
Planets are considered combust (and thus weak/incapable of giving good results) when conjoined with the Sun within the following limits:
- **Mars**: 12°
- **Mercury**: 8° (or 14° according to some Tajaka variations)
- **Jupiter**: 9°
- **Venus**: 7°
- **Saturn**: 9°

---

## 3. PLANETARY AVASTHAS (TEN STATES)

The strength and results of a planet are judged by its state (Avastha):
1. **Deeptha** (Exaltation): Confers success, joy, and fulfillment of the query.
2. **Deena** (Debilitation): Brings sorrow, delays, and failure.
3. **Swastha** (Own House / Swakshetra): Confers fame, stability, and success.
4. **Muditha** (Friendly Sign): Brings wealth, joy, and cooperative outcomes.
5. **Suptha** (Inimical House): Causes fear, anxiety, and trouble from enemies.
6. **Nipeeditha** (Vanquished in planetary war - exact conjunction with a malefic): Causes loss of wealth.
7. **Mushita** (Combust / conjoined with the Sun within combustion orb): Causes failure, loss of money, and vanity.
8. **Pariheena** (Fallen / descending strength): Results in deterioration and failure.
9. **Suveerya** (Ascending towards exaltation): Access to conveyances, gold, and rapid gains.
10. **Athiveerya** (High benefic divisions - Shadvargas): Promotes outstanding success and prestigious contacts.

---

## 4. TAJAKA YOGAS (THE COMPUTATIONAL ENGINE)

The core logical decisions in horary interpretation are governed by the relationship between the **Lagnapathi** (Lord of the Ascendant, representing the querent) and the **Karyesa** (Lord of the house of query, representing the object in view).

### Planetary Speeds (Fastest to Slowest)
1. Moon (Fastest)
2. Mercury
3. Venus
4. Sun
5. Mars
6. Jupiter
7. Saturn (Slowest)

### Core Yogas

#### I. Ithasala (Muthasila) Yoga (Applying Aspect)
Occurs when a faster-moving planet is behind a slower-moving planet in longitude and is catching up to it within their combined Deepthamsas.
- **Poorna (Complete) Ithasala**: When the distance between the two planets is less than $1°0'0"$. The result is guaranteed and immediate.
- **Bhavishya (Applying) Ithasala**: The aspect is applying but the distance is greater than 1° (within the Deepthamsa boundary). The event will occur after some time.

#### II. Easarapha (Musaripha) Yoga (Separating Aspect)
Occurs when the faster-moving planet has passed the slower-moving planet in longitude by more than 1° (or is separating).
- **Result**: Indicates failure, disappointment, or separation of the object from the querent.

#### III. Nakta Yoga (Intermediary Fast Translation)
When there is no direct aspect between the Lagnapathi and the Karyesa, but a faster planet (usually the Moon) is in aspect with both.
- **Mechanism**: The faster planet "translates" the light from the Lagnapathi to the Karyesa.
- **Result**: The objective will be achieved through the mediation/help of a third party represented by the translating planet.

#### IV. Yamaya Yoga (Intermediary Slow Translation)
When there is no direct aspect between the Lagnapathi and the Karyesa, but a slower-moving planet is placed in between them and aspects both.
- **Mechanism**: The slower planet receives the light from the faster Lagnapathi/Karyesa and carries it to the other.
- **Result**: Success through a third party (often an authority figure or older person represented by the slower planet).

#### V. Kamboola Yoga
Occurs when Lagnapathi and Karyesa are in Ithasala Yoga, and the Moon is also in Ithasala with one or both of them.
- **Grades of Kamboola**:
  - *Uttamottama*: All three planets are exalted or in their own houses. Excellent success.
  - *Madhymottama*: Moon is exalted, other planets are in own Navamsa/Drekkana.
  - *Uttama*: Moon is not exalted, but other lords are in own Navamsas.
  - *Uttamadhama*: Moon is exalted/own house, but the other two lords are debilitated.

---

## 5. GENERAL CRITERIA FOR SUCCESS (KARYASIDDHI)

A query is successful when:
1. The **Lagnapathi** aspects the Ascendant and the **Karyesa** aspects the house of the query.
2. The **Lagnapathi** aspects the house of query, and the **Karyesa** aspects the Ascendant.
3. The **Lagnapathi** and **Karyesa** are in mutual aspect (Trine or Sextile).
4. The **Moon** aspects both the Lagnapathi and the Karyesa.
5. The Ascendant is a **Sirshodaya** sign: Gemini (3), Leo (5), Virgo (6), Libra (7), Scorpio (8), or Aquarius (11).
6. Natural benefics are in the Ascendant or aspecting it, and the Moon is unafflicted.

### Percentages of Success
- **100% Success**: Ascendant is aspected by its lord, the Moon is unafflicted, and benefics aspect the Lagna.
- **75% Success**: At least one benefic aspects the Ascendant or its lord, or Lagnapathi / 2-3 benefics occupy the 10th house.
- **50% Success**: Benefics aspect the lord of the Ascendant.
- **25% Success**: The rising sign is completely devoid of the aspect of its lord or any benefic.

---

## 6. HOUSE-WISE (BHAVA) PRASNA EVALUATION

Each house signifies specific domains of queries. Success is judged by identifying the **Karyesa** (ruler of the house of query) and checking its relationship with the **Lagnapathi** (Lagna lord) and the **Moon**.

| House | Query Domain | Lagnapathi (Querent) | Karyesa (Significator) | Key Success Rules |
| :--- | :--- | :--- | :--- | :--- |
| **1st** | Life, health, past/present/future, happiness | Lagna Lord | Lagna Lord / Moon | Lagna and Moon must be strong. Sincerity checked. |
| **2nd** | Money, wealth, financial transactions | Lagna Lord | 2nd Lord | Ithasala between Lagna Lord/Moon and 2nd Lord. Benefics in 2nd. |
| **3rd** | Brothers, short journeys, news, messages | Lagna Lord | 3rd Lord | 3rd lord must not be combust or in 6th/8th. Ithasala with 3rd Lord. |
| **4th** | Lands, mother, crops, vehicles, hidden treasure | Lagna Lord | 4th Lord | Moon in 4th in Ithasala with Lagna Lord. Benefic in 4th/7th. |
| **5th** | Children, pregnancy, twins, legitimacy | Lagna Lord | 5th Lord | Ithasala between 1st & 5th lords. If in masculine signs, male child. |
| **6th** | Disease, cure, recovery, servants, theft | Lagna Lord | 6th Lord / 7th Lord | Lagna = physician, 7th = disease, 10th = patient, 4th = treatment. |
| **7th** | Marriage, wife's return, disputes, partnerships | Lagna Lord | 7th Lord | Ithasala between 1st & 7th lords. Moon in 7th. Venus placement. |
| **8th** | Death, war, battle victory, lost property | Lagna Lord | 8th Lord | 8th lord in Lagna = death/defeat. Victory if superior planets lead. |
| **9th** | Long journeys, pilgrimages, righteousness | Lagna Lord | 9th Lord | Ithasala between 1st & 9th lords. Benefics in 9th. |
| **10th** | Profession, status, job change, authority | Lagna Lord | 10th Lord | Mutual exchange of 1st & 10th lords. Kamboola Yoga with Moon. |
| **11th** | Gains, honors, friendship, realization of desires | Lagna Lord | 11th Lord | Friendly Ithasala between 1st & 11th lords. Benefics in 11th. |
| **12th** | Captivity, release, expenditure, loss | Lagna Lord | 12th Lord | 12th lord in Lagna = power to querent. Ithasala with 3rd/9th lord. |

---

## 7. KEY ALGORITHMS FOR TIMING OF EVENTS

To predict *when* a query will fructify:
1. **Degree Difference Method**: Measure the exact degrees separating the Lagnapathi and Karyesa.
   - If the Ascendant is in a **Movable** (Chara) sign: Degrees = Days/Weeks.
   - If the Ascendant is in a **Common** (Dwiswabhava) sign: Degrees = Weeks/Months.
   - If the Ascendant is in a **Fixed** (Sthira) sign: Degrees = Months/Years.
2. **Constellation Method (Krishneeya)**: Count the number of constellations intervening between Lagna and Karyesa:
   - If Lagna is in a Fixed sign: count = number of Days.
   - If Lagna is in a Common sign: double the count.
   - If Lagna is in a Movable sign: triple the count.
3. **Sign Multiplication Method**: Multiply the number of signs intervening between the Ascendant and the sign of the Karyesa by 12. The product represents the days, months, or years depending on the Movable, Common, or Fixed nature of the Ascendant.
