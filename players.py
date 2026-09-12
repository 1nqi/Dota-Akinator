import random


class Player:
    """Answers questions about one hero, with a configurable amount of human noise."""

    def __init__(self, traits, flip=0.0, idk=0.0, hedge=0.0, rng=None):
        self.traits = traits
        self.flip = flip
        self.idk = idk
        self.hedge = hedge
        self.rng = rng or random.Random()

    def answer(self, hero, q):
        if self.rng.random() < self.idk:
            return "idk"

        truth = self.traits[hero, q] > 0.5
        if self.rng.random() < self.flip:
            truth = not truth

        if self.rng.random() < self.hedge:
            return "probably" if truth else "probably not"
        return "yes" if truth else "no"
