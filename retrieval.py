"""
retrieval.py - the cheap ways to find the right lesson. No AI and no downloads.

1. lookup   exact match on a word, verb or section name found inside the question
2. keyword  TF-IDF search over the text of every lesson unit
3. router   try lookup first; if nothing matches, fall back to keyword search

These are the baselines that embedding retrieval must beat to earn its cost.
"""
import math
import re
import unicodedata
from collections import Counter

STOPWORDS = set("""
a an the of to in on at for from by with and or is are was were be been do does did i you he she
we they it me my your our how what when where why which who can could would should will say
show open find about into than then there here this that these those if so not no yes please
el la los las un una de del al y o en
""".split())

# words in the question that hint at what KIND of lesson the learner wants
TYPE_CUES = {
    "conv": {"conversation", "dialogue", "dialog"},
    "verb": {"verb", "conjugate", "conjugation", "conjugations", "tense"},
    "vocab": {"word", "vocabulary", "vocab", "meaning", "mean", "means"},
    "phrase": {"phrase", "phrases", "expression"},
    "pronoun": {"pronoun", "pronouns"},
    "numbers": {"number", "numbers"},
    "math": {"math", "sum", "arithmetic"},
    "time": {"time", "clock"},
    "measurements": {"measure", "measurement", "measurements"},
}


def normalize(text):
    """lowercase, no accents, only letters and digits separated by single spaces"""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def _stem(word):
    """Very light plural handling: numbers -> number, pesos -> peso, categories -> category."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokens(text, drop_stopwords=True):
    words = normalize(text).split()
    if drop_stopwords:
        words = [w for w in words if w not in STOPWORDS]
    return [_stem(w) for w in words]


MEANING_CUES = {"mean", "means", "meaning", "translate", "translation", "word"}


def _stemmed(text):
    return " ".join(_stem(w) for w in normalize(text).split())


# ------------------------------------------------------------------ 1. exact lookup
def lookup(query, units):
    """Units whose name appears, as whole words, inside the question.

    * Spanish titles and section names always count.
    * English meanings count only if the question asks what something MEANS.
    * Scenario names ("market") count only if the question also says "conversation".
    Returns [(unit_id, score)] best first. The score is the number of words matched
    plus 0.5 when the question also names the kind of lesson ("verb", "conversation"...).
    """
    words = normalize(query).split()
    padded = " " + _stemmed(query) + " "
    asked = set(words)
    asks_meaning = bool(MEANING_CUES & asked)
    hits = []
    for unit in units:
        type_cue = bool(TYPE_CUES.get(unit.type, set()) & asked)
        names = list(unit.aliases)
        if asks_meaning:
            names += unit.glosses
        if type_cue:
            names += unit.scoped_aliases
        best = 0
        for alias in names:
            alias_norm = _stemmed(alias)
            if alias_norm and f" {alias_norm} " in padded:
                best = max(best, len(alias_norm.split()))
        if best:
            hits.append((unit.id, best + (0.5 if type_cue else 0.0)))
    hits.sort(key=lambda pair: (-pair[1], pair[0]))
    return hits


# ------------------------------------------------------------------ 2. keyword search
class KeywordIndex:
    """TF-IDF over the unit texts (titles count three times)."""

    def __init__(self, units):
        self.ids = [u.id for u in units]
        docs = [tokens(u.title) * 3 + tokens(u.text) for u in units]
        document_frequency = Counter(word for doc in docs for word in set(doc))
        count = len(docs)
        self.idf = {w: math.log((count + 1) / (df + 1)) + 1 for w, df in document_frequency.items()}
        self.vectors = [self._vector(Counter(doc)) for doc in docs]

    def _vector(self, counts):
        vector = {w: (1 + math.log(c)) * self.idf.get(w, 0.0) for w, c in counts.items() if w in self.idf}
        norm = math.sqrt(sum(v * v for v in vector.values()))
        return {w: v / norm for w, v in vector.items()} if norm else {}

    def search(self, query, k=3, min_score=0.0):
        """Top k [(unit_id, score)] with score >= min_score. Scores are between 0 and 1."""
        query_vector = self._vector(Counter(tokens(query)))
        if not query_vector:
            return []
        scored = []
        for unit_id, vector in zip(self.ids, self.vectors):
            score = sum(weight * vector.get(word, 0.0) for word, weight in query_vector.items())
            if score > 0 and score >= min_score:
                scored.append((unit_id, round(score, 6)))
        scored.sort(key=lambda pair: (-pair[1], pair[0]))
        return scored[:k]


# ------------------------------------------------------------------ 3. the router
def route(query, units, index, k=3, min_score=0.0):
    """Lookup first (it is exact), then keyword search. Returns (method, results)."""
    found = lookup(query, units)
    if found:
        return "lookup", found[:k]
    return "keyword", index.search(query, k=k, min_score=min_score)
