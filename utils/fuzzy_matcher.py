import re
from rapidfuzz import fuzz


def normalize_description(text: str) -> str:
    text = text.lower().strip()
    # Remove dates, reference numbers, trailing digits
    text = re.sub(r"\d{2,4}[/-]\d{2}[/-]\d{2,4}", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"\b(ref|txn|id|no)\s*:?\s*\w+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def group_similar_transactions(descriptions: list[str], threshold: int = 75) -> dict[str, list[int]]:
    """Group transaction indices by similar description.

    Returns a dict mapping a representative description to the list of
    original indices that belong to that group.
    """
    normalized = [normalize_description(d) for d in descriptions]
    groups: dict[str, list[int]] = {}
    assigned = set()

    for i, desc_i in enumerate(normalized):
        if i in assigned or not desc_i:
            continue
        group_key = descriptions[i]
        members = [i]
        assigned.add(i)

        for j in range(i + 1, len(normalized)):
            if j in assigned or not normalized[j]:
                continue
            score = fuzz.token_sort_ratio(desc_i, normalized[j])
            if score >= threshold:
                members.append(j)
                assigned.add(j)

        groups[group_key] = members

    return groups
