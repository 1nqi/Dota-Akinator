import numpy as np

ANSWERS = ["yes", "probably", "idk", "probably not", "no"]


def answer_model(eps, hedge, idk):
    yes = (1 - idk) * (1 - hedge) * (1 - eps)
    probably = (1 - idk) * hedge * (1 - eps)
    probably_not = (1 - idk) * hedge * eps
    no = (1 - idk) * (1 - hedge) * eps

    given_true = np.array([yes, probably, idk, probably_not, no])
    return np.array([given_true[::-1], given_true])  #given false, given true


class Akinator:
    def __init__(self, heroes, questions, traits, eps=0.07, hedge=0.15, idk=0.08,
                 eps_guess=0.02, confidence=0.85, max_questions=20, min_gain=0.01,
                 max_guesses=3):
        self.heroes = heroes
        self.questions = questions
        self.traits = traits
        self.model = answer_model(eps, hedge, idk)
        self.eps_guess = eps_guess
        self.confidence = confidence
        self.max_questions = max_questions
        self.min_gain = min_gain
        self.max_guesses = max_guesses
        self.reset()

    def reset(self):
        self.belief = np.full(len(self.heroes), 1.0 / len(self.heroes))
        self.asked = set()
        self.rejected = set()

    def likelihood_table(self, q):
        t = self.traits[:, q]
        return np.outer(self.model[0], 1 - t) + np.outer(self.model[1], t)

    def likelihood(self, answer, q):
        return self.likelihood_table(q)[ANSWERS.index(answer)]

    def answer(self, q, answer):
        self.belief = self.belief * self.likelihood(answer, q)
        self.belief /= self.belief.sum()
        self.asked.add(q)

    def reject(self, hero):
        # self.belief[hero] = 0
        # self.belief /= self.belief.sum()
        # self.belief[0] += 1e-10
        # self.rejected.add(hero)
        self.belief[hero] *= self.eps_guess
        self.belief /= self.belief.sum()
        self.rejected.add(hero)

    def information_gain(self, q):
        table = self.likelihood_table(q)
        marginal = table @ self.belief
        conditional = -(table * np.log2(table)).sum(axis=0) @ self.belief
        return entropy(marginal) - conditional

    def next_question(self):
        best, best_gain = None, self.min_gain
        for q in range(len(self.questions)):
            if q in self.asked:
                continue
            gain = self.information_gain(q)
            if gain > best_gain:
                best, best_gain = q, gain
        return best, best_gain

    def top(self, n=3, skip_rejected=False):
        order = np.argsort(self.belief)[::-1]
        if skip_rejected:
            order = [i for i in order if i not in self.rejected]
        return [(self.heroes[i], float(self.belief[i])) for i in order[:n]]

    def best_guess(self):
        candidates = [i for i in range(len(self.heroes)) if i not in self.rejected]
        if not candidates:
            return int(np.argmax(self.belief))
        return max(candidates, key=lambda i: self.belief[i])

    def should_guess(self):
        if len(self.asked) >= self.max_questions:
            return True
        if self.next_question()[0] is None:
            return True
        return self.belief[self.best_guess()] >= self.confidence

    def entropy(self):
        #return entropy(self.belief) if self.belief.sum() > 0 else 0.0
        return entropy(self.belief) 

    def replay(self, history):
        self.reset()
        for q, answer in history:
            if answer == "reject":
                self.reject(q)
            else:
                self.answer(q, answer)
        return self


def entropy(p):
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())
