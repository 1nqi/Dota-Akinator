import csv

import numpy as np

def load(heroes_path="heroes.csv", questions_path="questions.csv"):
    with open(questions_path, encoding="utf-8") as f:
        asked = list(csv.DictReader(f))
    columns = [r["column"] for r in asked]
    questions = [r["question"] for r in asked]

    with open(heroes_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    traits = np.array([[cell(r[c]) for c in columns] for r in rows])
    base = np.nanmean(traits, axis=0)
    traits = np.where(np.isnan(traits), base, traits)

    return [r["hero"] for r in rows], questions, traits, [r["image"] for r in rows]
def cell(value):
    if value == "TRUE":
        return 1.0
    if value == "FALSE":
        return 0.0
    return np.nan
