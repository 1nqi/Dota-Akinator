from data_loader import load
from engine import Akinator

KEYS = {"1": "yes", "2": "probably", "3": "idk", "4": "probably not", "5": "no"}
PROMPT = "  1) yes   2) probably   3) don't know   4) probably not   5) no   (q to quit)\n> "


def ask(question):
    while True:
        try:
            choice = input(f"\n{question}\n{PROMPT}").strip().lower()
        except EOFError:
            return None
        if choice in ("q", "quit"):
            return None
        if choice in KEYS:
            return KEYS[choice]
        print("  pick a number from 1 to 5")


def yes_no(question, default=False):
    while True:
        try:
            choice = input(f"\n{question} (y/n) > ").strip().lower()
        except EOFError:
            return default
        if choice.startswith("y"):
            return True
        if choice.startswith("n"):
            return False


def show_thinking(game):
    print(f"\n  {game.entropy():.2f} bits left, best candidates:")
    for hero, p in game.top(3, skip_rejected=True):
        bar = "#" * int(round(p * 30))
        print(f"    {hero:22s} {p:6.1%} {bar}")


def give_up(game):
    print("\n  I give up. My shortlist was:")
    for name, p in game.top(5, skip_rejected=True):
        print(f"    {name:22s} {p:6.1%}")


def round_of_guesses(game):
    guesses = 0
    while True:
        while not game.should_guess():
            q, gain = game.next_question()
            answer = ask(game.questions[q])
            if answer is None:
                return
            game.answer(q, answer)
            show_thinking(game)

        hero = game.best_guess()
        print(f"\n  I am {game.belief[hero]:.0%} sure.")
        if yes_no(f"Is your hero {game.heroes[hero]}?"):
            print(f"\n  Got it in {len(game.asked)} questions.")
            return

        guesses += 1
        if guesses >= game.max_guesses or len(game.asked) >= game.max_questions:
            give_up(game)
            return

        # not a restart, just one more observation
        game.reject(hero)
        print("\n  Noted. Let me keep asking.")


def main():
    heroes, questions, traits, images = load()
    game = Akinator(heroes, questions, traits)

    print(f"Dota Akinator - think of one of {len(heroes)} heroes.")
    while True:
        game.reset()
        round_of_guesses(game)
        if not yes_no("\nPlay again?"):
            print("\n  Well played.")
            return


if __name__ == "__main__":
    main()
