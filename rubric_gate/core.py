import hashlib
import re

OPERATORS = {"contains_all", "contains_any", "excludes", "regex", "length", "footnotes", "sha256"}


def validate(spec):
    if not isinstance(spec, dict) or type(spec.get("version")) is not int or spec["version"] != 1:
        raise ValueError("Expected a version=1 rule specification")
    rules = spec.get("rules")
    if not isinstance(rules, list) or not rules or len(rules) > 500:
        raise ValueError("Expected 1–500 rules")
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("Each rule must be an object")
        rid = rule.get("id")
        if not isinstance(rid, str) or not rid.strip() or rid in ids:
            raise ValueError("Rule ids must be non-empty and unique")
        ids.add(rid)
        op = rule.get("op")
        if not isinstance(op, str) or op not in OPERATORS:
            raise ValueError(f"Unknown operator in {rid}")
        if not isinstance(rule.get("hard", True), bool):
            raise ValueError(f"hard must be a boolean: {rid}")
        weight = rule.get("weight", 1)
        if isinstance(weight, bool) or not isinstance(weight, int) or weight < 1:
            raise ValueError(f"weight must be a positive integer: {rid}")
        if op in {"contains_all", "contains_any", "excludes"}:
            values = rule.get("values")
            if not isinstance(values, list) or not values or not all(isinstance(x, str) and x for x in values):
                raise ValueError(f"values must be non-empty strings: {rid}")
        elif op == "regex":
            if not isinstance(rule.get("pattern"), str) or not rule["pattern"]:
                raise ValueError(f"pattern must be non-empty: {rid}")
            try:
                re.compile(rule["pattern"])
            except re.error as error:
                raise ValueError(f"Invalid regex: {rid}") from error
        elif op == "length":
            unit = rule.get("unit", "characters")
            if not isinstance(unit, str) or unit not in {"characters", "words", "chinese"}:
                raise ValueError(f"Unknown length unit: {rid}")
            lo, hi = rule.get("min", 0), rule.get("max", 200000)
            if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in [lo, hi]) or lo > hi:
                raise ValueError(f"Invalid length bounds: {rid}")
        elif op == "sha256":
            if not isinstance(rule.get("value"), str) or not re.fullmatch(r"[a-f0-9]{64}", rule["value"]):
                raise ValueError(f"Expected lowercase SHA-256: {rid}")
    return spec


def footnotes(text):
    definitions = re.findall(r"^\[\^([^\]\n]+)\]:", text, re.M)
    body = re.sub(r"^\[\^[^\]\n]+\]:.*$", "", text, flags=re.M)
    references = set(re.findall(r"\[\^([^\]\n]+)\]", body))
    missing = sorted(references - set(definitions))
    unused = sorted(set(definitions) - references)
    duplicates = sorted({name for name in definitions if definitions.count(name) > 1})
    return not (missing or unused or duplicates), {"missing": missing, "unused": unused, "duplicates": duplicates}


def evaluate(text, spec, name="document"):
    validate(spec)
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    if len(text) > 200000:
        raise ValueError("Text exceeds the 200,000-character limit")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    results = []
    for rule in spec["rules"]:
        op = rule["op"]
        if op == "contains_all":
            missing = [value for value in rule["values"] if value not in text]
            passed, detail = not missing, {"missing": missing}
        elif op == "contains_any":
            matched = [value for value in rule["values"] if value in text]
            passed, detail = bool(matched), {"matched": matched}
        elif op == "excludes":
            forbidden = [value for value in rule["values"] if value in text]
            passed, detail = not forbidden, {"forbidden": forbidden}
        elif op == "regex":
            passed = re.search(rule["pattern"], text, re.M) is not None
            detail = {"pattern": rule["pattern"]}
        elif op == "length":
            unit = rule.get("unit", "characters")
            count = len(text) if unit == "characters" else (len(text.split()) if unit == "words" else len(re.findall(r"[\u4e00-\u9fff]", text)))
            lo, hi = rule.get("min", 0), rule.get("max", 200000)
            passed, detail = lo <= count <= hi, {"count": count, "unit": unit, "min": lo, "max": hi}
        elif op == "footnotes":
            passed, detail = footnotes(text)
        else:
            passed, detail = sha == rule["value"], {"expected": rule["value"], "actual": sha}
        results.append({"id": rule["id"], "op": op, "hard": rule.get("hard", True),
                        "weight": rule.get("weight", 1), "passed": passed, "detail": detail})
    weight = sum(row["weight"] for row in results)
    return {"name": name, "sha256": sha,
            "accepted": all(row["passed"] for row in results if row["hard"]),
            "score": round(100 * sum(row["weight"] for row in results if row["passed"]) / weight, 2),
            "score_meaning": "Weighted rule satisfaction, not semantic quality or factual accuracy.",
            "rules": results}
