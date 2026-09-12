import csv
import json
import os
import random
import statistics
import numpy as np
from baseline import TreeBaseline
from data_loader import load
from engine import Akinator
from players import Player

TRIALS = 500
SEED = 7
GUESSES = 3
RESULTS = "results"
ALIASES = {"Rattletrap": "Clockwerk", "Wisp": "Io"}

def play(guesser, player, hero):
    guesser.reset()
    made = 0
    first = None
    while made < GUESSES:
        while not guesser.should_guess():
            q, _ = guesser.next_question()
            guesser.answer(q, player.answer(hero, q))

        guess = guesser.best_guess()
        made += 1
        if first is None:
            first = (guess == hero, confidence(guesser, guess))

        if guess == hero:
            break
        if len(guesser.asked) >= guesser.max_questions:
            break
        guesser.reject(guess)

    return {
        "won": guess == hero,
        "questions": len(guesser.asked),
        "guesses": made,
        "first_correct": first[0],
        "first_confidence": first[1],
    }


def confidence(guesser, hero):
    belief = getattr(guesser, "belief", None)
    return float(belief[hero]) if belief is not None else 1.0

def evaluate(make_guesser, make_player, heroes, traits, pool=None, trials=TRIALS, seed=SEED):
    rng = random.Random(seed)
    guesser = make_guesser()
    player = make_player(rng)
    pool = list(pool) if pool is not None else list(range(len(heroes)))

    games = [play(guesser, player, rng.choice(pool)) for _ in range(trials)]

    won = [g for g in games if g["won"]]
    return {
        "win_rate": len(won) / trials,
        "first_guess_accuracy": sum(g["first_correct"] for g in games) / trials,
        "mean_questions": statistics.mean(g["questions"] for g in won) if won else None,
        "median_questions": statistics.median(g["questions"] for g in won) if won else None,
        "games": games,
    }


def summary(result):
    return {k: v for k, v in result.items() if k != "games"}


def accuracy_at_k(heroes, questions, traits, ks, trials=TRIALS, seed=SEED):
    rng = random.Random(seed)
    game = Akinator(heroes, questions, traits)
    player = Player(traits, rng=rng)
    # defaultdict = {k: 0 for k in ks}

    hits = {k: 0 for k in ks}
    for _ in range(trials):
        hero = rng.randrange(len(heroes))
        game.reset()
        for k in range(1, max(ks) + 1):
            q, _ = game.next_question()
            if q is not None:
                game.answer(q, player.answer(hero, q))
            if k in hits and int(np.argmax(game.belief)) == hero:
                hits[k] += 1
    return {k: hits[k] / trials for k in ks}


def calibration(result, bins=10):
    conf = np.array([g["first_confidence"] for g in result["games"]])
    correct = np.array([g["first_correct"] for g in result["games"]], dtype=float)
    edges = np.linspace(0, 1, bins + 1)

    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (conf >= lo) & ((conf < hi) if hi < 1 else (conf <= hi))
        if mask.sum() >= 10:
            out.append({
                "confidence": float(conf[mask].mean()),
                "accuracy": float(correct[mask].mean()),
                "count": int(mask.sum()),
            })
    return out


def hand_labelled():
    with open("data/legacy_t.csv", encoding="utf-8") as f:
        names = [r["hero"].replace("_", " ").title() for r in csv.DictReader(f)]
    return {ALIASES.get(n, n) for n in names}


def main():
    heroes, questions, traits, images = load()
    engine = lambda **kw: (lambda: Akinator(heroes, questions, traits, **kw))
    tree = lambda: TreeBaseline(heroes, questions, traits)
    honest = lambda rng: Player(traits, rng=rng)
    report = {"heroes": len(heroes), "questions": len(questions), "trials": TRIALS}

    print(f"{len(heroes)} heroes, {len(questions)} questions, {TRIALS} games each\n")

    print(f"{'guesser':10s} {'win':>7s} {'1st try':>8s} {'mean q':>7s} {'median':>7s}")
    report["honest"] = {}
    for name, make in [("engine", engine()), ("legacy tree", tree)]:
        r = evaluate(make, honest, heroes, traits)
        report["honest"][name] = summary(r)
        print(f"{name:10s} {r['win_rate']:6.1%} {r['first_guess_accuracy']:7.1%} "
              f"{r['mean_questions'] or 0:7.1f} {r['median_questions'] or 0:7.0f}")

    print("\nrobustness, share of answers the player gets wrong")
    print(f"{'flip':>6s} {'engine win':>11s} {'engine q':>9s} {'tree win':>9s}")
    report["robustness"] = []
    for flip in [0.0, 0.05, 0.1, 0.2, 0.3]:
        maker = lambda rng, f=flip: Player(traits, flip=f, rng=rng)
        e = evaluate(engine(), maker, heroes, traits)
        t = evaluate(tree, maker, heroes, traits)
        report["robustness"].append({"flip": flip, "engine_win": e["win_rate"],
                                     "engine_questions": e["mean_questions"],
                                     "tree_win": t["win_rate"]})
        print(f"{flip:6.0%} {e['win_rate']:10.1%} {e['mean_questions'] or 0:9.1f} {t['win_rate']:8.1%}")

    print("\nplayers that keep saying they don't know")
    print(f"{'idk':>6s} {'engine win':>11s} {'engine q':>9s} {'tree win':>9s}")
    report["unsure"] = []
    for idk in [0.0, 0.1, 0.2, 0.3]:
        maker = lambda rng, i=idk: Player(traits, idk=i, rng=rng)
        e = evaluate(engine(), maker, heroes, traits)
        t = evaluate(tree, maker, heroes, traits)
        report["unsure"].append({"idk": idk, "engine_win": e["win_rate"],
                                 "engine_questions": e["mean_questions"],
                                 "tree_win": t["win_rate"]})
        print(f"{idk:6.0%} {e['win_rate']:10.1%} {e['mean_questions'] or 0:9.1f} {t['win_rate']:8.1%}")

    ks = [1, 3, 5, 7, 10, 15, 20]
    report["accuracy_at_k"] = accuracy_at_k(heroes, questions, traits, ks)
    print("\naccuracy after k questions, honest player")
    print("  " + "   ".join(f"k={k} {report['accuracy_at_k'][k]:.0%}" for k in ks))

    print("\nassumed eps against a player who flips 10% of answers")
    report["eps_sweep"] = []
    maker = lambda rng: Player(traits, flip=0.1, rng=rng)
    for eps in [0.01, 0.03, 0.07, 0.12, 0.2]:
        r = evaluate(engine(eps=eps), maker, heroes, traits)
        report["eps_sweep"].append({"eps": eps, "win_rate": r["win_rate"],
                                    "mean_questions": r["mean_questions"]})
        print(f"  eps={eps:<5} win {r['win_rate']:5.1%}  mean q {r['mean_questions'] or 0:.1f}")

    labelled = hand_labelled()
    print("\nwhat the hand labelling buys")
    report["coverage"] = {}
    for name, subset in [("hand labelled", labelled), ("api only", set(heroes) - labelled)]:
        # sorted, otherwise set iteration order changes the sample between runs
        pool = sorted(heroes.index(h) for h in subset)
        r = evaluate(engine(), honest, heroes, traits, pool=pool)
        report["coverage"][name] = dict(summary(r), n=len(pool))
        print(f"  {name:14s} n={len(pool):3d}  win {r['win_rate']:5.1%}  "
              f"mean q {r['mean_questions'] or 0:.1f}")

    r = evaluate(engine(), lambda rng: Player(traits, flip=0.05, rng=rng), heroes, traits)
    report["calibration"] = calibration(r)
    print("\ncalibration, player flips 5%")
    for b in report["calibration"]:
        print(f"  said {b['confidence']:5.1%}  right {b['accuracy']:5.1%}  (n={b['count']})")

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
    print(f"\nwrote {RESULTS}/metrics.json")
    return report


if __name__ == "__main__":
    main()
