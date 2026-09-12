import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def styled(title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.set_title(title, fontsize=11)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(alpha=0.25, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    return fig, ax


def save(fig, name):
    path = os.path.join("results", name)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print("wrote", path)


def robustness(report):
    rows = report["robustness"]
    x = [r["flip"] * 100 for r in rows]
    fig, ax = styled("Accuracy when the player answers wrong",
                     "share of answers flipped, %", "games won, %")
    ax.plot(x, [r["engine_win"] * 100 for r in rows], "o-", color="#ff2600", label="engine")
    ax.plot(x, [r["tree_win"] * 100 for r in rows], "s--", color="#8a8a8a", label="legacy decision tree")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=9)
    save(fig, "robustness.png")


def accuracy(report):
    items = sorted((int(k), v) for k, v in report["accuracy_at_k"].items())
    fig, ax = styled("Top candidate is correct after k questions",
                     "questions asked", "correct, %")
    ax.plot([k for k, _ in items], [v * 100 for _, v in items], "o-", color="#ff2600")
    ax.set_ylim(0, 100)
    save(fig, "accuracy_at_k.png")


def calibration(report):
    rows = report["calibration"]
    fig, ax = styled("Calibration: is 80% confidence actually 80%?",
                     "stated confidence, %", "games actually won, %")
    ax.plot([0, 100], [0, 100], ":", color="#999", linewidth=1, label="perfect")
    ax.plot([r["confidence"] * 100 for r in rows], [r["accuracy"] * 100 for r in rows],
            "o-", color="#ff2600", label="engine")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=9)
    save(fig, "calibration.png")


def main():
    with open(os.path.join("results", "metrics.json"), encoding="utf-8") as f:
        report = json.load(f)
    robustness(report)
    accuracy(report)
    calibration(report)


if __name__ == "__main__":
    main()
