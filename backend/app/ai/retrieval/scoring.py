import re
from dataclasses import dataclass

STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "may",
        "me",
        "might",
        "my",
        "of",
        "on",
        "or",
        "our",
        "should",
        "that",
        "the",
        "their",
        "them",
        "there",
        "these",
        "they",
        "this",
        "to",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
    }
)

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

TITLE_WEIGHT = 1.0
KEYWORD_WEIGHT = 0.9
SPECIALTY_WEIGHT = 0.7
CONTENT_WEIGHT = 0.6

MAXIMUM_TERM_WEIGHT = max(
    TITLE_WEIGHT,
    KEYWORD_WEIGHT,
    SPECIALTY_WEIGHT,
    CONTENT_WEIGHT,
)


@dataclass(frozen=True, slots=True)
class WeightedTextField:
    text: str
    weight: float


def tokenize(text: str) -> set[str]:
    normalized_tokens = TOKEN_PATTERN.findall(text.casefold())

    return {
        token
        for token in normalized_tokens
        if len(token) >= 2 and token not in STOPWORDS
    }


def lexical_score(
    query: str,
    searchable_text: str,
) -> tuple[float, list[str]]:
    return weighted_lexical_score(
        query,
        fields=(
            WeightedTextField(
                text=searchable_text,
                weight=1.0,
            ),
        ),
    )


def weighted_lexical_score(
    query: str,
    *,
    fields: tuple[WeightedTextField, ...],
) -> tuple[float, list[str]]:
    query_terms = tokenize(query)

    if not query_terms:
        return 0.0, []

    term_scores = {term: 0.0 for term in query_terms}

    for field in fields:
        if not 0.0 <= field.weight <= 1.0:
            raise ValueError("Field weights must be between 0.0 and 1.0.")

        field_terms = tokenize(field.text)

        for matched_term in query_terms.intersection(field_terms):
            term_scores[matched_term] = max(
                term_scores[matched_term],
                field.weight,
            )

    matched_terms = sorted(term for term, score in term_scores.items() if score > 0.0)

    score = sum(term_scores.values()) / (len(query_terms) * MAXIMUM_TERM_WEIGHT)

    return min(score, 1.0), matched_terms
