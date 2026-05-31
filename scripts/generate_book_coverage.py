import json
import re
from pathlib import Path


RULE_BUCKETS = {
    "editorial_noncomputational": [
        r"approach a learned astrologer", r"pleasant disposition", r"fruits, flowers",
        r"hands of men of learning", r"culture and humility", r"cannot go wrong",
        r"according to god siva", r"no need to explain", r"after saluting the sun", r"benefit of the world"
    ],
    "planet_house_signification_reference": [
        r"the sun signifies", r"from the first house is to be discovered",
        r"the fourth rules", r"rules?", r"signifies", r"planetary indications"
    ],
    "core_house_rules": [
        r"ascendant lord", r"benefic", r"malefic", r"kendra", r"trikona", r"lagna",
        r"ascendant", r"query", r"querent", r"significator", r"muthasila", r"musaripha", r"easarapha",
        r"bhava", r"aspect", r"mutual aspect", r"transfer[s]?\s+light",
        r"second house", r"third house", r"fourth house", r"fifth house", r"sixth house",
        r"seventh house", r"eighth house", r"ninth house", r"tenth house", r"eleventh house", r"twelfth house",
        r"first house", r"wealth", r"siblings", r"children", r"property", r"domestic", r"education",
        r"lord of the ascendant", r"third lord", r"fifth and seventh", r"tenth lord",
        r"twelfth lord", r"eleventh lord", r"sixth lord", r"ithasala", r"karyesa",
        r"navamsa", r"dwadasamsa", r"drekkana", r"planetary states", r"patient",
        r"arrival and departure", r"time of fructification", r"immense gain", r"stronger lord"
    ],
    "deity_curse": [r"curse", r"deit", r"divine anger"],
    "master_servant": [r"employment", r"job", r"service", r"master", r"servant"],
    "meals": [r"food", r"meal", r"taste"],
    "sports": [r"sport", r"contest", r"match"],
    "disputes": [r"dispute", r"litigation", r"lawsuit", r"judge", r"war", r"enemy"],
    "crops_trade": [r"crop", r"agriculture", r"harvest", r"trade", r"grain"],
    "purchase_sale": [r"purchase", r"buy", r"sale", r"sell", r"transaction"],
    "dreams": [r"dream", r"sleep"],
    "ships": [r"ship", r"voyage", r"sea", r"boat", r"vessel", r"cargo"],
    "rumours": [r"rumou?r", r"news", r"report", r"hearsay"],
    "sexual_matters": [r"sexual", r"intimacy", r"union", r"adultery"],
    "women_enquiry": [r"women", r"woman", r"female", r"venus", r"wife", r"pregnant", r"pregnancy", r"bride", r"character"],
    "hunting": [r"hunting", r"hunt", r"game", r"expedition"],
    "incarceration": [r"captivity", r"incarceration", r"prison", r"jail", r"custody", r"detention"],
    "lost_objects": [r"stolen", r"theft", r"thief", r"lost property", r"lost article"],
    "traveler": [r"return", r"abroad", r"alive or dead", r"journey", r"traveler", r"traveller"],
    "misc_weather_thought": [r"weather", r"rain", r"thought", r"mind"],
}


def _find_blocks(text: str):
    # Primary markers
    primary = list(re.finditer(r"(?im)^\s*(?:stanza|sloka)\s+(\d+)\s*[:.\-]?", text))
    if primary:
        return [(int(m.group(1)), m.start()) for m in primary]

    # Fallback for prose layouts like "1-2. ..." or "10. ..."
    fallback = list(re.finditer(r"(?im)^\s*(\d{1,3})(?:\s*-\s*\d{1,3})?\.\s+", text))
    return [(int(m.group(1)), m.start()) for m in fallback]


def _classify(snippet: str):
    s = snippet.lower()
    hits = []
    for bucket, pats in RULE_BUCKETS.items():
        for p in pats:
            if re.search(p, s):
                hits.append(bucket)
                break
    hits = sorted(set(hits))
    # OCR artifacts / empty marker lines should not remain unresolved.
    if not hits:
        token_count = len(re.findall(r"[a-z0-9]+", s))
        if token_count <= 2:
            hits = ["editorial_noncomputational"]
    return hits


def generate_coverage(source_file: Path, out_file: Path):
    text = source_file.read_text(encoding="utf-8", errors="ignore")
    anchors = _find_blocks(text)
    if not anchors:
        raise ValueError(f"No stanza/sloka/numbered blocks detected in: {source_file}")

    rows = []
    bucket_counts = {k: 0 for k in RULE_BUCKETS}
    uncovered = 0

    for idx, (num, start) in enumerate(anchors):
        end = anchors[idx + 1][1] if idx + 1 < len(anchors) else len(text)
        snippet = text[start:end].strip()
        buckets = _classify(snippet)
        if not buckets:
            uncovered += 1
        for b in buckets:
            bucket_counts[b] += 1
        rows.append({
            "block_number": num,
            "buckets": buckets,
            "excerpt": re.sub(r"\s+", " ", snippet[:260]).strip(),
        })

    payload = {
        "source_file": str(source_file),
        "total_blocks_detected": len(anchors),
        "unclassified_blocks": uncovered,
        "bucket_counts": bucket_counts,
        "rows": rows,
        "note": "Heuristic keyword-based mapping. Use as implementation planning aid, not as doctrinal authority.",
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return payload
