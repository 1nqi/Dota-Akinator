API = "https://api.opendota.com/api/heroes"
CACHE = "data/opendota_heroes.json"
CDN = "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{}.png"
ROLES = ["Carry", "Disabler", "Durable", "Escape", "Initiator", "Nuker", "Pusher", "Support"]
DUPLICATES = {"is carry": "role carry", "is support": "role support"}
ALIASES = {"Rattletrap": "Clockwerk", "Wisp": "Io"}

API_QUESTIONS = [
    ("is strength", "Is your hero's main attribute Strength?"),
    ("is agility", "Is your hero's main attribute Agility?"),
    ("is intelligence", "Is your hero's main attribute Intelligence?"),
    ("is universal", "Is your hero Universal?"),
    ("is melee", "Is your hero melee?"),
    ("has no legs", "Does your hero have no legs at all?"),
    ("has two legs", "Does your hero have exactly two legs?"),
    ("has four or more legs", "Does your hero have four or more legs?"),
    ("role carry", "Does your hero play carry?"),
    ("role disabler", "Does your hero have a disable (stun, root, hex)?"),
    ("role durable", "Is your hero durable?"),
    ("role escape", "Does your hero have an escape?"),
    ("role initiator", "Does your hero initiate fights?"),
    ("role nuker", "Does your hero nuke with spell damage?"),
    ("role pusher", "Does your hero push lanes?"),
    ("role support", "Does your hero play support?"),
]

import csv
import json
import os
import requests
def fetch_heroes():
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)

    heroes = requests.get(API, timeout=30).json()
    os.makedirs("data", exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(heroes, f, indent=1, ensure_ascii=False)
    return heroes

def api_traits(hero):
    attr = hero["primary_attr"]
    legs = hero["legs"]
    row = {
        "is strength": attr == "str",
        "is agility": attr == "agi",
        "is intelligence": attr == "int",
        "is universal": attr == "all",
        "is melee": hero["attack_type"] == "Melee",
        "has no legs": legs == 0,
        "has two legs": legs == 2,
        "has four or more legs": legs >= 4,
    }
    for role in ROLES:
        row["role " + role.lower()] = role in hero["roles"]
    return row
def load_manual():
    with open("data/legacy_t.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open("data/legacy_q.csv", encoding="utf-8") as f:
        questions = {r["column"]: r["question"] for r in csv.DictReader(f)}
    drop = set(DUPLICATES) | {c for c, _ in API_QUESTIONS}
    columns = [c for c in rows[0] if c != "hero" and c not in drop]

    traits = {}
    for r in rows:
        name = r["hero"].replace("_", " ").title()
        traits[ALIASES.get(name, name)] = {c: r[c] == "TRUE" for c in columns}
    return traits, columns, questions


def short_name(hero):
    return hero["name"].replace("npc_dota_hero_", "")

def main():
    heroes = fetch_heroes()
    manual, manual_columns, manual_questions = load_manual()

    columns = [c for c, _ in API_QUESTIONS] + manual_columns
    matched = 0
    rows = []

    for hero in sorted(heroes, key=lambda h: h["localized_name"]):
        name = hero["localized_name"]
        row = {"hero": name, "image": CDN.format(short_name(hero))}
        row.update(api_traits(hero))

        hand = manual.get(name)
        if hand:
            matched += 1
        for c in manual_columns:
            row[c] = "" if hand is None else hand[c]

        rows.append(row)
    header = ["hero", "image"] + columns
    with open("heroes.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: (v if isinstance(v, str) else str(v).upper()) for k, v in row.items()})

    questions = list(API_QUESTIONS) + [(c, manual_questions[c]) for c in manual_columns]
    with open("questions.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["column", "question"])
        w.writerows(questions)

    unmatched = sorted(set(manual) - {h["localized_name"] for h in heroes})
    print(f"heroes: {len(rows)}, questions: {len(questions)}")
    print(f"hand labelled: {matched}/{len(manual)}")
    if unmatched:
        print(f"manual heroes not found in the api: {unmatched}")
if __name__ == "__main__":
    main()