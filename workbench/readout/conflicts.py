"""Find verified claims that disagree, so a contradiction cannot be averaged away.

The model is not asked to notice. Two claims conflict when they cite different documents, exactly
one of them is negated, and they share a content bigram that is not just a span of time ("last
twelve months" is not, on its own, a disagreement). The shared bigram is what stops an unrelated
negation -- "no supplier can use the portal" -- from being paired with a ticket that merely
mentions a supplier.

The quotes that get rendered are the claims' own quotes, copied from the store. The model's
wording of the disagreement is never kept.
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Sequence

from workbench.core.store import Claim

_WORD = re.compile(r"[a-z0-9]+")

_NEGATION = frozenset(
    {
        "no",
        "none",
        "never",
        "without",
        "not",
        "zero",
        "nothing",
        "neither",
        "nor",
    }
)

_STOP = frozenset(
    {
        "about",
        "after",
        "again",
        "also",
        "because",
        "been",
        "before",
        "being",
        "both",
        "could",
        "does",
        "doing",
        "during",
        "each",
        "from",
        "have",
        "inside",
        "into",
        "just",
        "many",
        "more",
        "most",
        "much",
        "only",
        "onto",
        "other",
        "over",
        "same",
        "should",
        "some",
        "such",
        "than",
        "that",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "under",
        "very",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "with",
        "would",
        "your",
    }
)

#: A bigram made only of these does not carry a disagreement. "Last twelve months" appears on
#: both sides of the planted contradiction and must not be what pairs them; "duplicate payment"
#: is.
_TIME = frozenset(
    {
        "day",
        "last",
        "month",
        "quarter",
        "today",
        "twelve",
        "week",
        "year",
        "yesterday",
    }
)

#: How many disagreements one readout will spell out. Past this, the section would crowd out the
#: rest of a bounded readout; the committed pack has one.
MAX_CONFLICTS = 8


def _stem(word: str) -> str:
    if word.endswith("s") and not word.endswith("ss") and len(word) > 4:
        return word[:-1]
    return word


def _content_words(text: str) -> list[str]:
    words: list[str] = []
    for word in _WORD.findall(text.lower()):
        if word in _NEGATION or word in _STOP or len(word) < 4:
            continue
        stemmed = _stem(word)
        if len(stemmed) < 4 or stemmed in _STOP:
            continue
        words.append(stemmed)
    return words


def _bigrams(text: str) -> set[tuple[str, str]]:
    words = _content_words(text)
    grams: set[tuple[str, str]] = set()
    for left, right in itertools.pairwise(words):
        if left in _TIME and right in _TIME:
            continue
        grams.add((left, right))
    return grams


def _claim_bigrams(claim: Claim) -> set[tuple[str, str]]:
    # Text and quote separately, so a bigram cannot form across the join between them.
    return _bigrams(claim.text) | _bigrams(claim.quote)


def _negated(claim: Claim) -> bool:
    words = _WORD.findall(f"{claim.text} {claim.quote}".lower())
    return any(word in _NEGATION for word in words)


def find_conflicts(claims: Sequence[Claim]) -> tuple[tuple[Claim, Claim], ...]:
    """Pairs of verified claims that disagree. Order is stable: by claim id."""
    usable = [claim for claim in claims if claim.verified]
    prepared = [(claim, _claim_bigrams(claim), _negated(claim)) for claim in usable]
    pairs: list[tuple[Claim, Claim]] = []
    for index, (left, left_grams, left_neg) in enumerate(prepared):
        for right, right_grams, right_neg in prepared[index + 1 :]:
            if left.doc_id == right.doc_id or left.id == right.id:
                continue
            if left_neg == right_neg:
                continue
            if not (left_grams & right_grams):
                continue
            ordered = tuple(sorted((left, right), key=lambda claim: claim.id))
            pairs.append((ordered[0], ordered[1]))
    pairs.sort(key=lambda pair: (pair[0].id, pair[1].id))
    return tuple(pairs[:MAX_CONFLICTS])
