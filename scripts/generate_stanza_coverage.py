import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TXT_PATH = ROOT / "B.V.Raman - Raman Publication.txt"
OUT_PATH = ROOT / "stanza_coverage_matrix.json"


RULE_BUCKETS = {
    "editorial_noncomputational": [
        r"approach a learned astrologer", r"pleasant disposition", r"fruits, flowers",
        r"hands of men of learning", r"culture and humility", r"cannot go wrong",
        r"according to god siva", r"no need to explain"
    ],
    "planet_house_signification_reference": [
        r"the sun signifies", r"from the first house is to be discovered",
        r"the fourth rules", r"rules?", r"signifies"
    ],
    "core_house_rules": [
        r"ascendant lord", r"benefic", r"malefic", r"kendra", r"trikona",
        r"second house", r"third house", r"fourth house", r"fifth house", r"sixth house",
        r"wealth", r"siblings", r"children", r"property", r"domestic", r"education",
        r"lord of the ascendant", r"third lord", r"fifth and seventh", r"seventh house",
        r"tenth lord", r"twelfth lord", r"eleventh lord", r"sixth lord", r"resolution may occur soon",
        r"gain through a new position"
    ],
    "deity_curse": [r"curse", r"deit", r"divine anger"],
    "master_servant": [r"employment", r"job", r"service", r"master", r"servant"],
    "meals": [r"food", r"meal", r"taste"],
    "sports": [r"sport", r"contest", r"match"],
    "disputes": [r"dispute", r"litigation", r"lawsuit", r"judge"],
    "crops_trade": [r"crop", r"agriculture", r"harvest", r"trade"],
    "purchase_sale": [r"purchase", r"buy", r"sale", r"sell", r"transaction"],
    "dreams": [r"dream", r"sleep"],
    "ships": [r"ship", r"voyage", r"sea", r"boat", r"vessel"],
    "rumours": [r"rumou?r", r"news", r"report"],
    "sexual_matters": [r"sexual", r"intimacy", r"union", r"adultery"],
    "women_enquiry": [r"women", r"woman", r"female", r"venus"],
    "hunting": [r"hunting", r"hunt", r"game"],
    "incarceration": [r"captivity", r"incarceration", r"prison", r"jail", r"custody", r"detention"],
    "lost_objects": [r"stolen", r"theft", r"thief", r"lost property"],
    "traveler": [r"return", r"abroad", r"alive or dead", r"journey", r"traveler"],
    "misc_weather_thought": [r"weather", r"rain", r"thought", r"mind"],
}


def find_stanza_blocks(text: str):
    stanza_pat = re.compile(r"Stanza\s+(\d+)\s*:", re.IGNORECASE)
    matches = list(stanza_pat.finditer(text))
    blocks = []
    for idx, m in enumerate(matches):
        stanza_no = int(m.group(1))
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        snippet = text[start:end].strip()
        blocks.append((stanza_no, snippet))
    return blocks


def classify_block(snippet: str):
    s = snippet.lower()
    hits = []
    for bucket, pats in RULE_BUCKETS.items():
        for p in pats:
            if re.search(p, s):
                hits.append(bucket)
                break
    return sorted(set(hits))


def main():
    if not TXT_PATH.exists():
        raise FileNotFoundError(f"Input not found: {TXT_PATH}")

    text = TXT_PATH.read_text(encoding="utf-8", errors="ignore")
    blocks = find_stanza_blocks(text)

    stanza_rows = []
    bucket_counts = {k: 0 for k in RULE_BUCKETS}
    uncovered = 0

    for stanza_no, snippet in blocks:
        buckets = classify_block(snippet)
        if not buckets:
            uncovered += 1
        for b in buckets:
            bucket_counts[b] += 1
        stanza_rows.append({
            "stanza": stanza_no,
            "buckets": buckets,
            "excerpt": re.sub(r"\s+", " ", snippet[:260]).strip(),
        })

    payload = {
        "source_file": str(TXT_PATH),
        "total_stanza_blocks_detected": len(blocks),
        "unclassified_blocks": uncovered,
        "bucket_counts": bucket_counts,
        "rows": stanza_rows,
        "note": "Heuristic keyword-based mapping. Use as implementation planning aid, not as doctrinal authority."
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"Wrote: {OUT_PATH}")
    print(f"Detected stanza blocks: {len(blocks)}")
    print(f"Unclassified blocks: {uncovered}")


if __name__ == "__main__":
    main()
