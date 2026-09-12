# v1 (2024)

The original Dota Akinator, kept on purpose so the two versions can be compared.

```bash
python legacy/legacy.py
```

It trains a `DecisionTreeClassifier` on `data/legacy_t.csv`, where every hero
appears exactly once, and then walks `clf.tree_` by hand. That has three problems
the rewrite fixes:

- the tree memorises rows, it does not reason about 20 questions
- `calculate_bayesian_probability` is decorative: the prior is set to 1.0 or 0.0
  on the answer itself, and at 0.0 the posterior is identically zero
- "don't know" and a wrong guess both do `node_index += 1`, which jumps to the
  next slot in the tree array, an arbitrary node unrelated to the current one

`baseline.py` reproduces this walk headlessly so `experiments.py` can measure it.
