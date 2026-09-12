import os

from flask import Flask, jsonify, request, send_from_directory

from data_loader import load
from engine import ANSWERS, Akinator

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
ASSETS = os.path.join(HERE, "assets")

app = Flask(__name__, static_folder=None)
heroes, questions, traits, images = load(
    os.path.join(HERE, "heroes.csv"), os.path.join(HERE, "questions.csv"))


def new_game():
    # a fresh belief vector per request, the traits table is shared read only.
    # nothing is kept between requests, so two players never touch the same state
    return Akinator(heroes, questions, traits)


def parse_history(payload):
    history = []
    for item in payload.get("history", []):
        index, answer = int(item[0]), str(item[1])
        limit = len(heroes) if answer == "reject" else len(questions)
        if answer != "reject" and answer not in ANSWERS:
            raise ValueError(f"unknown answer {answer!r}")
        if not 0 <= index < limit:
            raise ValueError("index out of range")
        history.append((index, answer))
    return history


@app.post("/api/next")
def next_step():
    try:
        history = parse_history(request.get_json(force=True) or {})
    except (ValueError, TypeError, IndexError, KeyError):
        return jsonify({"error": "bad history"}), 400

    game = new_game().replay(history)
    order = [i for i in game.belief.argsort()[::-1] if i not in game.rejected]

    def card(i):
        return {"hero": heroes[i], "image": images[i], "p": float(game.belief[i])}

    state = {
        "asked": len(game.asked),
        "max_questions": game.max_questions,
        "entropy": game.entropy(),
        "top": [card(i) for i in order[:8]],
    }

    if game.should_guess() or len(game.rejected) >= game.max_guesses:
        best = int(order[0])
        state["done"] = True
        state["guess"] = dict(card(best), index=best)
        state["gave_up"] = len(game.rejected) >= game.max_guesses
        return jsonify(state)

    q, gain = game.next_question()
    state["done"] = False
    state["question"] = questions[q]
    state["question_index"] = int(q)
    state["gain"] = float(gain)
    return jsonify(state)


@app.get("/api/meta")
def meta():
    return jsonify({"heroes": len(heroes), "questions": len(questions), "answers": ANSWERS})


@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/assets/<path:name>")
def asset(name):
    return send_from_directory(ASSETS, name)


@app.get("/<path:name>")
def static_file(name):
    return send_from_directory(WEB, name)


if __name__ == "__main__":
    # railway injects PORT, and 127.0.0.1 is unreachable from outside a container
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
