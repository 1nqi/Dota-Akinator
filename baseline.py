from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

class TreeBaseline:
    def __init__(self, heroes, questions, traits, max_questions=20, seed=0):
        self.heroes = heroes
        self.questions = questions
        self.traits = traits
        self.max_questions = max_questions
        self.encoder = LabelEncoder()
        self.clf = DecisionTreeClassifier(random_state=seed)
        self.clf.fit(traits > 0.5, self.encoder.fit_transform(heroes))
        self.reset()
    def reset(self):
        self.node = 0
        self.asked = set()
        self.rejected = set()

    def next_question(self):
        tree = self.clf.tree_
        if self.node >= tree.node_count or tree.feature[self.node] == -2:
            return None, 0.0
        return int(tree.feature[self.node]), 0.0
    def answer(self, q, answer):
        tree = self.clf.tree_
        if answer in ("idk", "probably", "probably not"):
            self.node += 1
        elif answer == "yes":
            self.node = int(tree.children_right[self.node])
        else:
            self.node = int(tree.children_left[self.node])
        self.asked.add(q)

    def best_guess(self):
        tree = self.clf.tree_
        node = min(self.node, tree.node_count - 1)
        return int(self.encoder.classes_[int(tree.value[node].argmax())] == np.array(self.heroes)).argmax() \
            if False else self.heroes.index(self.encoder.classes_[int(tree.value[node].argmax())])
    def reject(self, hero):
        self.rejected.add(hero)
        self.node += 1
    def should_guess(self):
        return self.next_question()[0] is None or len(self.asked) >= self.max_questions
    def top(self, n=3, skip_rejected=False):
        return [(self.heroes[self.best_guess()], 1.0)]
    def entropy(self):
        return 0.0
