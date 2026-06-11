"""英文分词：NLTK tokenize + stopwords + WordNet lemmatize。"""

from __future__ import annotations

import re

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from comment_analysis.analysis.nltk_data import ensure_nltk_data

_ENGLISH_TOKEN_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9'-]*$")
_lemmatizer: WordNetLemmatizer | None = None


def _get_lemmatizer() -> WordNetLemmatizer:
    global _lemmatizer
    if _lemmatizer is None:
        ensure_nltk_data()
        _lemmatizer = WordNetLemmatizer()
    return _lemmatizer


def tokenize_english(text: str) -> list[str]:
    ensure_nltk_data()
    english_stop = set(stopwords.words("english"))
    lemmatizer = _get_lemmatizer()
    tokens: list[str] = []

    for raw in word_tokenize(text):
        normalized = raw.lower().strip("-'")
        segments = (
            [part.strip("-'") for part in normalized.split("-")]
            if "-" in normalized
            else [normalized]
        )
        for segment in segments:
            if len(segment) < 2:
                continue
            if not _ENGLISH_TOKEN_PATTERN.match(segment):
                continue
            if segment in english_stop:
                continue
            lemma = lemmatizer.lemmatize(segment, pos="n")
            if lemma in english_stop:
                continue
            tokens.append(lemma)

    return tokens
