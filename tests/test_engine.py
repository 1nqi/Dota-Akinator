import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_loader import load
from engine import ANSWERS, Akinator, answer_model


@pytest.fixture(scope="module")
def game():
    heroes, questions, traits, images = load()
    return Akinator(heroes, questions, traits)


@pytest.fixture
def toy():
    # one question, one hero that has the trait, one that does not, one unlabelled
    traits = np.array([[1.0], [0.0], [0.5]])
    return Akinator(["yes hero", "no hero", "unknown hero"], ["does it?"], traits)


def test_answer_model_is_a_distribution():
    model = answer_model(0.07, 0.15, 0.08)
    assert np.allclose(model.sum(axis=1), 1.0)


def test_idk_is_uninformative(game):
    game.reset()
    before = game.belief.copy()
    game.answer(0, "idk")
    assert np.allclose(game.belief, before)


def test_belief_stays_normalised(game):
    game.reset()
    for q, a in [(0, "yes"), (1, "no"), (2, "probably"), (3, "probably not")]:
        game.answer(q, a)
        assert game.belief.sum() == pytest.approx(1.0)
        assert (game.belief >= 0).all()


def test_unknown_trait_sits_in_between(toy):
    toy.answer(0, "yes")
    yes_hero, no_hero, unknown = toy.belief
    assert no_hero < unknown < yes_hero


def test_honest_answers_find_the_hero(game):
    for hero in ["Pudge", "Zeus", "Riki"]:
        truth = game.heroes.index(hero)
        game.reset()
        while not game.should_guess():
            q, _ = game.next_question()
            game.answer(q, "yes" if game.traits[truth, q] > 0.5 else "no")
        assert game.heroes[game.best_guess()] == hero


def test_questions_are_not_repeated(game):
    game.reset()
    seen = []
    while not game.should_guess():
        q, _ = game.next_question()
        assert q not in seen
        seen.append(q)
        game.answer(q, "yes")


def test_reject_lowers_but_does_not_zero(game):
    game.reset()
    game.answer(0, "yes")
    hero = game.best_guess()
    before = game.belief[hero]
    game.reject(hero)
    assert 0 < game.belief[hero] < before
    assert game.best_guess() != hero


def test_information_gain_is_never_negative(game):
    game.reset()
    assert min(game.information_gain(q) for q in range(len(game.questions))) >= -1e-12


def test_replay_matches_sequential_play(game):
    history = [(0, "yes"), (5, "no"), (9, "idk"), (12, "probably")]
    game.reset()
    for q, a in history:
        game.answer(q, a)
    expected = game.belief.copy()
    assert np.allclose(game.replay(history).belief, expected)


def test_every_answer_is_usable(game):
    for a in ANSWERS:
        game.reset()
        game.answer(0, a)
        assert game.belief.sum() == pytest.approx(1.0)
