"""Category learning system for FinanceKit.

Records user corrections to auto-categorization and uses fuzzy matching
to apply learned rules to future transactions. Learned rules take priority
over keyword-based matching.
"""

from utils.data_persistence import load_json, save_json
from rapidfuzz import fuzz

RULES_FILE = "category_rules.json"
_MATCH_THRESHOLD = 85


def _load_rules() -> list[dict]:
    """Load learned category rules from disk."""
    return load_json(RULES_FILE, default=[])


def _save_rules(rules: list[dict]):
    """Persist category rules to disk."""
    save_json(RULES_FILE, rules)


def learn_from_correction(description: str, old_category: str, new_category: str):
    """Record a user correction for future auto-categorization.

    If a similar pattern already exists, increment its usage count and update
    confidence. Otherwise, create a new rule.
    """
    if not description or not new_category:
        return
    if old_category == new_category:
        return

    rules = _load_rules()
    norm = _normalize(description)

    # Check for an existing similar rule
    for rule in rules:
        if fuzz.token_sort_ratio(norm, rule["pattern"]) >= _MATCH_THRESHOLD:
            if rule["category"] == new_category:
                rule["times_used"] = rule.get("times_used", 1) + 1
                rule["confidence"] = min(1.0, 0.6 + rule["times_used"] * 0.05)
                _save_rules(rules)
                return
            # Different category correction — replace if new correction is more recent
            rule["category"] = new_category
            rule["times_used"] = 1
            rule["confidence"] = 0.6
            _save_rules(rules)
            return

    # New rule
    rules.append({
        "pattern": norm,
        "category": new_category,
        "confidence": 0.6,
        "times_used": 1,
    })
    _save_rules(rules)


def get_learned_category(description: str) -> str | None:
    """Return a learned category for the given description, or None.

    Uses fuzzy matching against stored patterns. Rules with higher
    times_used take priority.
    """
    if not description:
        return None

    rules = _load_rules()
    if not rules:
        return None

    norm = _normalize(description)
    best_match = None
    best_score = 0

    for rule in rules:
        score = fuzz.token_sort_ratio(norm, rule["pattern"])
        if score >= _MATCH_THRESHOLD:
            # Weight by times_used for tie-breaking
            weighted = score + rule.get("times_used", 1) * 0.5
            if weighted > best_score:
                best_score = weighted
                best_match = rule

    return best_match["category"] if best_match else None


def is_learned(description: str) -> bool:
    """Check if a category was determined by a learned rule (vs keyword)."""
    return get_learned_category(description) is not None


def get_rules_by_category() -> dict[str, int]:
    """Return count of learned rules per category."""
    rules = _load_rules()
    counts: dict[str, int] = {}
    for r in rules:
        cat = r.get("category", "Other")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


def get_all_rules() -> list[dict]:
    """Return all learned rules."""
    return _load_rules()


def delete_rule(pattern: str):
    """Delete a learned rule by pattern."""
    rules = _load_rules()
    rules = [r for r in rules if r["pattern"] != pattern]
    _save_rules(rules)


def _normalize(text: str) -> str:
    """Normalize a description for matching — lowercase, strip numbers/noise."""
    import re
    t = text.lower().strip()
    t = re.sub(r"#\d+", "", t)           # Remove # followed by digits
    t = re.sub(r"\b\d{4,}\b", "", t)     # Remove long numbers
    t = re.sub(r"[*_\-]+", " ", t)       # Replace dashes/stars with space
    t = re.sub(r"\s+", " ", t).strip()   # Collapse whitespace
    return t
