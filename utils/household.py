"""Household management — shared finance for couples and families."""
import uuid
import string
import random
from utils.data_persistence import load_json, save_json

HOUSEHOLD_FILE = "household.json"
SPLITS_FILE = "splits.json"

DEFAULT_HOUSEHOLD = {
    "enabled": False,
    "name": "",
    "members": [],
    "invite_code": "",
    "shared_budgets": True,
    "shared_goals": True,
}


def _load_household():
    return load_json(HOUSEHOLD_FILE, default=DEFAULT_HOUSEHOLD.copy())


def _save_household(data):
    save_json(HOUSEHOLD_FILE, data)


def _load_splits():
    return load_json(SPLITS_FILE, default=[])


def _save_splits(splits):
    save_json(SPLITS_FILE, splits)


def is_household_enabled():
    hh = _load_household()
    return hh.get("enabled", False)


def get_household():
    return _load_household()


def get_members():
    hh = _load_household()
    return hh.get("members", [])


def get_member_names():
    return [m.get("name", m.get("id", "Unknown")) for m in get_members()]


def enable_household(name, owner_name):
    hh = _load_household()
    hh["enabled"] = True
    hh["name"] = name
    if not hh["members"]:
        hh["members"] = [{"id": str(uuid.uuid4())[:8], "name": owner_name, "role": "owner"}]
    hh["invite_code"] = _generate_invite_code()
    _save_household(hh)
    return hh


def disable_household():
    hh = _load_household()
    hh["enabled"] = False
    _save_household(hh)


def _generate_invite_code():
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=6))


def regenerate_invite_code():
    hh = _load_household()
    hh["invite_code"] = _generate_invite_code()
    _save_household(hh)
    return hh["invite_code"]


def add_member(name):
    hh = _load_household()
    member = {"id": str(uuid.uuid4())[:8], "name": name, "role": "member"}
    hh["members"].append(member)
    _save_household(hh)
    return member


def remove_member(member_id):
    hh = _load_household()
    hh["members"] = [m for m in hh["members"] if m["id"] != member_id]
    _save_household(hh)


def join_household(invite_code, member_name):
    hh = _load_household()
    if not hh.get("enabled"):
        return None, "Household mode is not enabled."
    if hh.get("invite_code") != invite_code:
        return None, "Invalid invite code."
    existing_names = [m["name"].lower() for m in hh.get("members", [])]
    if member_name.lower() in existing_names:
        return None, "A member with this name already exists."
    member = {"id": str(uuid.uuid4())[:8], "name": member_name, "role": "member"}
    hh["members"].append(member)
    _save_household(hh)
    return member, "Joined successfully!"


# ── Split expenses ──────────────────────────────────────────────────────

def create_split(description, total_amount, paid_by, split_with, method="even",
                 percentages=None, amounts=None):
    splits = _load_splits()
    member_names = [paid_by] + split_with
    n = len(member_names)

    if method == "even":
        per_person = round(total_amount / n, 2)
        shares = {name: per_person for name in member_names}
    elif method == "percentage" and percentages:
        shares = {name: round(total_amount * pct / 100, 2)
                  for name, pct in zip(member_names, percentages)}
    elif method == "amount" and amounts:
        shares = dict(zip(member_names, amounts))
    elif method == "one_paid":
        shares = {paid_by: total_amount}
        for name in split_with:
            shares[name] = round(total_amount / len(split_with), 2)
    else:
        per_person = round(total_amount / n, 2)
        shares = {name: per_person for name in member_names}

    split = {
        "id": str(uuid.uuid4())[:8],
        "description": description,
        "total": total_amount,
        "paid_by": paid_by,
        "shares": shares,
        "method": method,
        "settled": False,
        "created": str(__import__("datetime").date.today()),
    }
    splits.append(split)
    _save_splits(splits)
    return split


def get_balances():
    splits = _load_splits()
    balances = {}
    for s in splits:
        if s.get("settled"):
            continue
        paid_by = s["paid_by"]
        shares = s.get("shares", {})
        for person, share in shares.items():
            if person == paid_by:
                continue
            key = (person, paid_by)
            balances[key] = balances.get(key, 0) + share
    # Net out mutual debts
    net = {}
    processed = set()
    for (debtor, creditor), amount in balances.items():
        if (debtor, creditor) in processed or (creditor, debtor) in processed:
            continue
        reverse = balances.get((creditor, debtor), 0)
        diff = amount - reverse
        if diff > 0:
            net[(debtor, creditor)] = round(diff, 2)
        elif diff < 0:
            net[(creditor, debtor)] = round(abs(diff), 2)
        processed.add((debtor, creditor))
        processed.add((creditor, debtor))
    return net


def settle_split(split_id):
    splits = _load_splits()
    for s in splits:
        if s["id"] == split_id:
            s["settled"] = True
            break
    _save_splits(splits)


def get_unsettled_splits():
    splits = _load_splits()
    return [s for s in splits if not s.get("settled")]


def get_all_splits():
    return _load_splits()
