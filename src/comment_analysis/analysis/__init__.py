"""分析模块入口。"""

from .insights import (
    build_sentiment_score_summary,
    build_word_cloud,
    generate_insights,
)
from .keywords import assign_keywords, build_keyword_report, extract_keywords_from_record, tokenize_text
from .language import LanguageLabel, detect_language
from .report import build_analysis_report
from .sentiment import assign_sentiment, classify_sentiment

__all__ = [
    "LanguageLabel",
    "assign_keywords",
    "assign_sentiment",
    "build_analysis_report",
    "build_keyword_report",
    "build_sentiment_score_summary",
    "build_word_cloud",
    "classify_sentiment",
    "detect_language",
    "extract_keywords_from_record",
    "generate_insights",
    "tokenize_text",
]
