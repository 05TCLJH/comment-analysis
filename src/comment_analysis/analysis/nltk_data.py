"""首次使用时下载 NLTK 语料包。"""

from __future__ import annotations

import nltk

NLTK_PACKAGES = ("punkt_tab", "stopwords", "wordnet", "omw-1.4")
_downloaded = False


def ensure_nltk_data() -> None:
    """确保 punkt / stopwords / wordnet 可用；幂等。"""
    global _downloaded
    if _downloaded:
        return
    for package in NLTK_PACKAGES:
        try:
            if package == "punkt_tab":
                nltk.data.find("tokenizers/punkt_tab")
            elif package == "stopwords":
                nltk.data.find("corpora/stopwords")
            elif package == "wordnet":
                nltk.data.find("corpora/wordnet")
            elif package == "omw-1.4":
                nltk.data.find("corpora/omw-1.4")
        except LookupError:
            nltk.download(package, quiet=True)
    _downloaded = True
