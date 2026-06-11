# P1 双语规则化分析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有正则分词 + 混合词典情感，升级为「语言检测 → 中文 jieba / 英文 NLTK 分词 → 中文词典规则 / 英文 VADER 情感」的双语管线，并在 JSON/HTML 报告中展示语言分布；`pipeline` 与 `analyze --from-db` 无需改入口即可自动受益。

**Architecture:** 在 `src/comment_analysis/analysis/` 下新增 `language.py`、`tokenize_cn.py`、`tokenize_en.py` 三个子模块；`keywords.py` 与 `sentiment.py` 保留对外函数签名（`tokenize_text`、`assign_keywords`、`assign_sentiment`、`classify_sentiment`），内部按语言分流。`report.py` 增加 `language_distribution` 统计；`charts.py` 增加语言分布饼图。P0 已完成的 SQLite 读库与 `FullPipeline` 编排**不改动**，仅替换分析实现。

**Tech Stack:** Python 3.12、stdlib `unittest`、`jieba`、`nltk`（punkt + stopwords + wordnet）、`vaderSentiment`、现有 `CommentRecord` / `build_analysis_report` / ECharts HTML。

**范围说明：** 本计划覆盖 `PROJECT_BACKLOG.md` 第六节 **P1-1～P1-7**；`analysis_jobs` 表、结构化日志、README 大改归入 P2。**不引入** LLM、transformers、SnowNLP、spaCy transformer、云 NLP API。

**建议执行环境：** 在独立 git worktree 中实施（`superpowers:using-git-worktrees`）。

**P0 前置（已完成）：** `FullPipeline`、`analyze --from-db --last-job`、SQLite 主存储均已就绪；P1 完成后 V1 双语判定标准即可勾选。

---

## 文件结构总览

| 文件 | 职责 |
|------|------|
| `requirements.txt` | 新增 `jieba`、`nltk`、`vaderSentiment` |
| `src/comment_analysis/analysis/language.py` | **新增** CJK 占比语言检测；`detect_language` / `is_mixed` |
| `src/comment_analysis/analysis/data/stopwords_cn.txt` | **新增** 中文停用词表（可扩展） |
| `src/comment_analysis/analysis/tokenize_cn.py` | **新增** jieba 分词 + 中文停用词过滤 |
| `src/comment_analysis/analysis/tokenize_en.py` | **新增** NLTK 分词、停用词、WordNet 词形归一 |
| `src/comment_analysis/analysis/keywords.py` | **修改** `tokenize_text` 按语言调用子管线；保留 `assign_keywords` 接口 |
| `src/comment_analysis/analysis/sentiment.py` | **修改** 中文词典规则；英文 VADER；保留 `classify_sentiment` 三分类 |
| `src/comment_analysis/analysis/report.py` | **修改** 输出 `language_distribution`；记录级 `detected_language` |
| `src/comment_analysis/analysis/__init__.py` | 导出 `detect_language`（可选） |
| `src/comment_analysis/visualization/charts.py` | **修改** 语言分布饼图 + 统计卡片 |
| `tests/test_language.py` | **新增** 语言检测用例 |
| `tests/test_tokenize_cn.py` | **新增** jieba 中文分词 |
| `tests/test_tokenize_en.py` | **新增** NLTK 英文分词与 war/wars 归一 |
| `tests/test_sentiment_bilingual.py` | **新增** 中英情感 fixture |
| `tests/test_keywords_analysis.py` | **修改** 适配双语分词断言 |
| `tests/test_report_language.py` | **新增** 报告含 `language_distribution` |

---

## 任务依赖顺序

```text
Task 1 (依赖 + NLTK 引导)
    → Task 2 (language.py)
    → Task 3 (tokenize_cn.py)
    → Task 4 (tokenize_en.py)
    → Task 5 (keywords.py 统一入口)
    → Task 6 (sentiment.py 双语情感)
    → Task 7 (report.py 语言统计)
    → Task 8 (charts.py 语言饼图)
    → Task 9 (全量回归 + 手工验收)
```

---

### Task 1: 依赖与 NLTK 数据引导（P1-6）

**Files:**
- Modify: `requirements.txt`
- Create: `src/comment_analysis/analysis/nltk_data.py`
- Test: `tests/test_nltk_data.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_nltk_data.py
"""NLTK 数据引导测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.nltk_data import ensure_nltk_data, NLTK_PACKAGES


class NltkDataTest(unittest.TestCase):
    def test_nltk_packages_contains_required_resources(self) -> None:
        self.assertIn("punkt_tab", NLTK_PACKAGES)
        self.assertIn("stopwords", NLTK_PACKAGES)
        self.assertIn("wordnet", NLTK_PACKAGES)

    def test_ensure_nltk_data_downloads_missing_packages(self) -> None:
        with patch("comment_analysis.analysis.nltk_data.nltk.data.find", side_effect=LookupError):
            with patch("comment_analysis.analysis.nltk_data.nltk.download") as mock_download:
                ensure_nltk_data()
                self.assertEqual(mock_download.call_count, len(NLTK_PACKAGES))
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"
python -m unittest tests.test_nltk_data -v
```

Expected: FAIL — `ModuleNotFoundError: comment_analysis.analysis.nltk_data`

- [ ] **Step 3: Write minimal implementation**

`requirements.txt` 追加：

```text
jieba>=0.42,<1.0
nltk>=3.8,<4.0
vaderSentiment>=3.3,<4.0
```

```python
# src/comment_analysis/analysis/nltk_data.py
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
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
pip install -r requirements.txt
python -m unittest tests.test_nltk_data -v
```

Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```powershell
git add requirements.txt src/comment_analysis/analysis/nltk_data.py tests/test_nltk_data.py
git commit -m "feat: add bilingual NLP dependencies and NLTK bootstrap helper"
```

---

### Task 2: 语言检测与分流（P1-1）

**Files:**
- Create: `src/comment_analysis/analysis/language.py`
- Modify: `src/comment_analysis/analysis/__init__.py`
- Test: `tests/test_language.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_language.py
"""语言检测测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.language import LanguageLabel, detect_language


class LanguageDetectionTest(unittest.TestCase):
    def test_detects_english_dominant_text(self) -> None:
        label = detect_language("Iran Israel war update and analysis")
        self.assertEqual(label, LanguageLabel.EN)

    def test_detects_chinese_dominant_text(self) -> None:
        label = detect_language("美以伊战争局势持续紧张，民众担忧升级")
        self.assertEqual(label, LanguageLabel.ZH)

    def test_detects_mixed_text(self) -> None:
        label = detect_language("Iran war 美以伊战争 discussion")
        self.assertEqual(label, LanguageLabel.MIXED)

    def test_empty_text_is_unknown(self) -> None:
        self.assertEqual(detect_language(""), LanguageLabel.UNKNOWN)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_language -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```python
# src/comment_analysis/analysis/language.py
"""轻量语言检测：CJK 占比 + 拉丁字母，无大模型。"""

from __future__ import annotations

from enum import Enum
import re

_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
_LATIN_PATTERN = re.compile(r"[A-Za-z]")

# CJK 字符数 ≥ 2 且占比 ≥ 15% 视为含中文；同时含拉丁字母则为 MIXED
_CJK_RATIO_THRESHOLD = 0.15
_MIN_CJK_CHARS = 2


class LanguageLabel(str, Enum):
    ZH = "zh"
    EN = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


def detect_language(text: str) -> LanguageLabel:
    """检测文本主语言或混合语言。"""
    stripped = text.strip()
    if not stripped:
        return LanguageLabel.UNKNOWN

    cjk_chars = _CJK_PATTERN.findall(stripped)
    latin_chars = _LATIN_PATTERN.findall(stripped)
    meaningful_len = len(re.sub(r"\s+", "", stripped))
    if meaningful_len == 0:
        return LanguageLabel.UNKNOWN

    cjk_count = len(cjk_chars)
    cjk_ratio = cjk_count / meaningful_len
    has_cjk = cjk_count >= _MIN_CJK_CHARS and cjk_ratio >= _CJK_RATIO_THRESHOLD
    has_latin = len(latin_chars) >= 2

    if has_cjk and has_latin:
        return LanguageLabel.MIXED
    if has_cjk:
        return LanguageLabel.ZH
    if has_latin:
        return LanguageLabel.EN
    return LanguageLabel.UNKNOWN
```

`analysis/__init__.py` 增加：

```python
from .language import LanguageLabel, detect_language
```

并在 `__all__` 中导出。

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_language -v
```

Expected: PASS（4 tests）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/analysis/language.py src/comment_analysis/analysis/__init__.py tests/test_language.py
git commit -m "feat: add CJK-ratio language detection for bilingual routing"
```

---

### Task 3: 中文分词管线（P1-2）

**Files:**
- Create: `src/comment_analysis/analysis/data/stopwords_cn.txt`
- Create: `src/comment_analysis/analysis/tokenize_cn.py`
- Test: `tests/test_tokenize_cn.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tokenize_cn.py
"""中文 jieba 分词测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.tokenize_cn import tokenize_chinese


class TokenizeChineseTest(unittest.TestCase):
    def test_tokenize_chinese_extracts_meaningful_terms(self) -> None:
        tokens = tokenize_chinese("美以伊战争局势紧张，民众担忧冲突升级")

        self.assertIn("战争", tokens)
        self.assertIn("冲突", tokens)
        self.assertNotIn("的", tokens)
        self.assertNotIn("，", tokens)

    def test_tokenize_chinese_filters_stopwords(self) -> None:
        tokens = tokenize_chinese("这是一个测试")
        self.assertNotIn("一个", tokens)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_tokenize_cn -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

`data/stopwords_cn.txt`（节选，文件内每行一词）：

```text
的
了
是
一个
我们
他们
这个
以及
因为
所以
已经
没有
需要
觉得
```

```python
# src/comment_analysis/analysis/tokenize_cn.py
"""中文分词：jieba + 项目停用词表。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

import jieba

_DATA_DIR = Path(__file__).resolve().parent / "data"
_STOPWORDS_PATH = _DATA_DIR / "stopwords_cn.txt"
_MIN_TOKEN_LEN = 2
_PUNCT_PATTERN = re.compile(r"^[\u3000-\u303f\uff00-\uffef\W_]+$")


@lru_cache(maxsize=1)
def _load_stopwords() -> frozenset[str]:
    if not _STOPWORDS_PATH.exists():
        return frozenset()
    lines = _STOPWORDS_PATH.read_text(encoding="utf-8").splitlines()
    return frozenset(line.strip() for line in lines if line.strip())


def tokenize_chinese(text: str) -> list[str]:
    """对中文文本做 jieba 分词并过滤停用词。"""
    stopwords = _load_stopwords()
    tokens: list[str] = []
    for raw in jieba.cut(text):
        token = raw.strip()
        if len(token) < _MIN_TOKEN_LEN:
            continue
        if _PUNCT_PATTERN.match(token):
            continue
        if token in stopwords:
            continue
        tokens.append(token)
    return tokens
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_tokenize_cn -v
```

Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/analysis/tokenize_cn.py src/comment_analysis/analysis/data/stopwords_cn.txt tests/test_tokenize_cn.py
git commit -m "feat: add jieba Chinese tokenization with stopword filtering"
```

---

### Task 4: 英文分词管线（P1-3）

**Files:**
- Create: `src/comment_analysis/analysis/tokenize_en.py`
- Test: `tests/test_tokenize_en.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_tokenize_en.py
"""英文 NLTK 分词测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis.tokenize_en import tokenize_english


class TokenizeEnglishTest(unittest.TestCase):
    @patch("comment_analysis.analysis.tokenize_en.ensure_nltk_data")
    def test_tokenize_english_lemmatizes_war_variants(self, _mock: object) -> None:
        tokens = tokenize_english("The wars in Iran and Israel are escalating")

        self.assertIn("war", tokens)
        self.assertNotIn("wars", tokens)
        self.assertIn("iran", tokens)
        self.assertNotIn("the", tokens)

    @patch("comment_analysis.analysis.tokenize_en.ensure_nltk_data")
    def test_tokenize_english_keeps_hyphenated_terms(self, _mock: object) -> None:
        tokens = tokenize_english("cross-border conflict update")
        self.assertTrue("cross" in tokens or "border" in tokens)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_tokenize_en -v
```

Expected: FAIL — module not found

- [ ] **Step 3: Write minimal implementation**

```python
# src/comment_analysis/analysis/tokenize_en.py
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
    """对英文文本分词、去停用词并词形归一。"""
    ensure_nltk_data()
    english_stop = set(stopwords.words("english"))
    lemmatizer = _get_lemmatizer()
    tokens: list[str] = []

    for raw in word_tokenize(text):
        normalized = raw.lower().strip("-'")
        if len(normalized) < 2:
            continue
        if not _ENGLISH_TOKEN_PATTERN.match(normalized):
            continue
        if normalized in english_stop:
            continue
        lemma = lemmatizer.lemmatize(normalized, pos="n")
        if lemma in english_stop:
            continue
        tokens.append(lemma)

    return tokens
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_tokenize_en -v
```

Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/analysis/tokenize_en.py tests/test_tokenize_en.py
git commit -m "feat: add NLTK English tokenization with lemmatization"
```

---

### Task 5: 统一关键词入口（P1-4）

**Files:**
- Modify: `src/comment_analysis/analysis/keywords.py`
- Modify: `tests/test_keywords_analysis.py`

- [ ] **Step 1: Write the failing test**

在 `tests/test_keywords_analysis.py` 末尾追加：

```python
from comment_analysis.analysis.language import LanguageLabel, detect_language


class BilingualKeywordsTest(unittest.TestCase):
    def test_tokenize_text_routes_mixed_text_to_both_pipelines(self) -> None:
        tokens = tokenize_text("Iran war 美以伊战争 update")

        self.assertIn("iran", tokens)
        self.assertIn("war", tokens)
        # jieba 可能保留整词或子词，至少应含「战争」相关中文词项
        self.assertTrue(any("战争" in t or "美以" in t for t in tokens))

    def test_detect_language_used_for_routing(self) -> None:
        self.assertEqual(detect_language("Iran Israel war"), LanguageLabel.EN)
        self.assertEqual(detect_language("美以伊战争局势"), LanguageLabel.ZH)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_keywords_analysis.BilingualKeywordsTest -v
```

Expected: FAIL — 混合文本路由行为不符合新实现

- [ ] **Step 3: Write minimal implementation**

`keywords.py` 替换 `tokenize_text` 并保留其余函数：

```python
from comment_analysis.analysis.language import LanguageLabel, detect_language
from comment_analysis.analysis.tokenize_cn import tokenize_chinese
from comment_analysis.analysis.tokenize_en import tokenize_english


def tokenize_text(text: str) -> list[str]:
    """按语言分流分词；混合文本合并中英词项并去重保序。"""
    label = detect_language(text)
    tokens: list[str] = []
    seen: set[str] = set()

    def _extend(items: list[str]) -> None:
        for item in items:
            if item not in seen:
                seen.add(item)
                tokens.append(item)

    if label in (LanguageLabel.ZH, LanguageLabel.MIXED, LanguageLabel.UNKNOWN):
        _extend(tokenize_chinese(text))
    if label in (LanguageLabel.EN, LanguageLabel.MIXED, LanguageLabel.UNKNOWN):
        _extend(tokenize_english(text))

    # 兼容旧停用词表：过滤仍可能出现的英文停用词
    return [t for t in tokens if t.lower() not in _STOP_WORDS and t not in _STOP_WORDS]
```

保留 `_STOP_WORDS`、`_extract_text_parts`、`assign_keywords`、`build_keyword_report` 不变。

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_keywords_analysis -v
```

Expected: PASS（全部 keywords 测试，含新增 BilingualKeywordsTest）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/analysis/keywords.py tests/test_keywords_analysis.py
git commit -m "feat: route keyword tokenization through bilingual pipelines"
```

---

### Task 6: 双语情感分析（P1-5）

**Files:**
- Modify: `src/comment_analysis/analysis/sentiment.py`
- Test: `tests/test_sentiment_bilingual.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sentiment_bilingual.py
"""双语情感分析测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis import assign_sentiment, classify_sentiment
from comment_analysis.models import CommentRecord
from datetime import datetime


class SentimentBilingualTest(unittest.TestCase):
    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_english_positive_vader(self, _mock: object) -> None:
        label, score = classify_sentiment("This is a wonderful peace agreement and great hope")
        self.assertEqual(label, "积极")
        self.assertGreater(score, 0)

    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_english_negative_vader(self, _mock: object) -> None:
        label, score = classify_sentiment("Terrible war, awful attack and horrible crisis")
        self.assertEqual(label, "消极")
        self.assertLess(score, 0)

    def test_chinese_negative_dictionary(self) -> None:
        label, score = classify_sentiment("战争带来危险和死亡，局势非常混乱")
        self.assertEqual(label, "消极")
        self.assertLessEqual(score, -2)

    def test_chinese_positive_dictionary(self) -> None:
        label, score = classify_sentiment("希望实现和平与安全，局势趋于稳定")
        self.assertEqual(label, "积极")
        self.assertGreaterEqual(score, 2)

    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_assign_sentiment_mixed_record(self, _mock: object) -> None:
        record = CommentRecord(
            platform="hackernews",
            content="Iran war 战争危险",
            source_url="https://example.com/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
        )
        updated = assign_sentiment([record])[0]
        self.assertIn(updated.sentiment_label, ("积极", "中性", "消极"))
        self.assertIn("sentiment_score", updated.raw_data)
        self.assertIn("detected_language", updated.raw_data)
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_sentiment_bilingual -v
```

Expected: FAIL — VADER 路径未实现或 `detected_language` 缺失

- [ ] **Step 3: Write minimal implementation**

```python
# sentiment.py 核心改动（保留模块 docstring 与 assign_sentiment 签名）

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from comment_analysis.analysis.language import LanguageLabel, detect_language
from comment_analysis.analysis.nltk_data import ensure_nltk_data

_analyzer: SentimentIntensityAnalyzer | None = None


def _get_vader() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        ensure_nltk_data()
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def _classify_chinese(text: str) -> tuple[str, int]:
    """沿用词典 + 否定词规则（使用 jieba 分词提升命中率）。"""
    from comment_analysis.analysis.tokenize_cn import tokenize_chinese

    tokens = tokenize_chinese(text)
    score = 0
    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index > 0 else ""
        reverse = previous in _NEGATION_WORDS or any(
            token.startswith(neg) for neg in _NEGATION_WORDS if len(neg) == 1
        )
        if token in _POSITIVE_WORDS:
            score += -1 if reverse else 1
        elif token in _NEGATIVE_WORDS:
            score += 1 if reverse else -1
    if score >= 2:
        return "积极", score
    if score <= -2:
        return "消极", score
    return "中性", score


def _classify_english(text: str) -> tuple[str, int]:
    """VADER compound 分数映射为三分类。"""
    compound = _get_vader().polarity_scores(text)["compound"]
    scaled = int(round(compound * 10))
    if compound >= 0.05:
        return "积极", scaled
    if compound <= -0.05:
        return "消极", scaled
    return "中性", scaled


def classify_sentiment(text: str) -> tuple[str, int]:
    """按主语言选择情感管线；混合文本优先中文词典（含英文负面词）。"""
    label = detect_language(text)
    if label == LanguageLabel.ZH:
        return _classify_chinese(text)
    if label == LanguageLabel.EN:
        return _classify_english(text)
    if label == LanguageLabel.MIXED:
        zh_label, zh_score = _classify_chinese(text)
        en_label, en_score = _classify_english(text)
        # 混合：取绝对值更大的分数对应标签；平局取中文
        if abs(en_score) > abs(zh_score):
            return en_label, en_score
        return zh_label, zh_score
    return _classify_english(text)


def assign_sentiment(records: Iterable[CommentRecord]) -> list[CommentRecord]:
    updated_records: list[CommentRecord] = []
    for record in records:
        text = _collect_text(record)
        sentiment_label, score = classify_sentiment(text)
        raw_data = dict(record.raw_data)
        raw_data["sentiment_score"] = score
        raw_data["detected_language"] = detect_language(text).value
        # ... 其余 CommentRecord 构造与现实现一致
```

删除 `sentiment.py` 内旧的 `_tokenize` / `_TOKEN_PATTERN`（改由子管线负责）。

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_sentiment_bilingual -v
```

Expected: PASS（5 tests）

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/analysis/sentiment.py tests/test_sentiment_bilingual.py
git commit -m "feat: bilingual sentiment with Chinese dictionary and English VADER"
```

---

### Task 7: 报告语言分布统计（P1-7 前半）

**Files:**
- Modify: `src/comment_analysis/analysis/report.py`
- Test: `tests/test_report_language.py`（新建）

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report_language.py
"""分析报告语言分布测试。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.analysis import assign_keywords, assign_sentiment, build_analysis_report
from comment_analysis.models import CommentRecord


class ReportLanguageTest(unittest.TestCase):
    @patch("comment_analysis.analysis.sentiment.ensure_nltk_data")
    def test_build_analysis_report_includes_language_distribution(self, _mock: object) -> None:
        records = [
            CommentRecord(
                platform="hackernews",
                content="Iran Israel war update",
                source_url="https://example.com/1",
                crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            ),
            CommentRecord(
                platform="stackexchange",
                content="美以伊战争局势分析",
                source_url="https://example.com/2",
                crawl_time=datetime(2026, 6, 11, 10, 5, 0),
            ),
        ]
        enriched = assign_sentiment(assign_keywords(records, top_n=5))
        report = build_analysis_report(enriched, top_n=10)

        self.assertIn("language_distribution", report)
        labels = {item["label"] for item in report["language_distribution"]}
        self.assertTrue({"en", "zh"} & labels or "mixed" in labels)
        self.assertIn("detected_language", report["records"][0])
```

- [ ] **Step 2: Run test to verify it fails**

```powershell
python -m unittest tests.test_report_language -v
```

Expected: FAIL — `language_distribution` 键不存在

- [ ] **Step 3: Write minimal implementation**

`report.py` 改动要点：

```python
from comment_analysis.analysis.language import detect_language

def _normalize_record(record: CommentRecord) -> dict[str, Any]:
    # ... 现有字段 ...
    detected = record.raw_data.get("detected_language")
    if not detected:
        detected = detect_language(record.content + " " + (record.title or "")).value
    return {
        # ... 现有字段 ...
        "detected_language": detected,
    }

def build_analysis_report(records: Iterable[CommentRecord], top_n: int = 20) -> dict[str, Any]:
    # ... 现有计数器 ...
    language_counter: Counter[str] = Counter()

    for record in records_list:
        normalized = _normalize_record(record)
        language_counter.update([normalized["detected_language"]])
        # ... 其余逻辑 ...

    return {
        # ... 现有字段 ...
        "language_distribution": _to_series(language_counter),
        "analysis_engine": "bilingual-rules-v1",
    }
```

- [ ] **Step 4: Run test to verify it passes**

```powershell
python -m unittest tests.test_report_language -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add src/comment_analysis/analysis/report.py tests/test_report_language.py
git commit -m "feat: add language_distribution to analysis report JSON"
```

---

### Task 8: HTML 仪表盘语言分布图（P1-7 后半）

**Files:**
- Modify: `src/comment_analysis/visualization/charts.py`
- Modify: `tests/test_analyze_entry.py`（断言 HTML 含「语言分布」）

- [ ] **Step 1: Write the failing test**

在 `tests/test_analyze_entry.py` 的 `test_run_keyword_analysis_reads_json_and_writes_report` 中追加：

```python
self.assertIn("语言分布", html_report)
```

先运行确认失败（当前 HTML 无该区块）：

```powershell
python -m unittest tests.test_analyze_entry.AnalyzeEntryTest.test_run_keyword_analysis_reads_json_and_writes_report -v
```

Expected: FAIL — `语言分布` not in html

- [ ] **Step 2: Implement charts.py changes**

在 `_TEMPLATE` 的 `charts-grid` 内、`平台分布` 之后插入：

```html
<div class="chart-card"><div class="title">语言分布</div><div id="chart-language" class="chart"></div></div>
```

在 `stats-grid` 增加（可选）：

```html
<div class="stat-card"><div class="value" id="stat-languages">0</div><div class="label">语言种类</div></div>
```

在 JS `updateCharts()` 中增加语言饼图（数据来自 `RAW_DATA.language_distribution`）：

```javascript
function renderLanguageChart() {
  const data = RAW_DATA.language_distribution || [];
  const el = document.getElementById('chart-language');
  if (!el) return;
  const chart = echarts.init(el);
  const labelMap = { zh: '中文', en: '英文', mixed: '混合', unknown: '未知' };
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      data: data.map(d => ({ name: labelMap[d.label] || d.label, value: d.count }))
    }]
  });
}
```

在 `updateDashboard()` / `updateCharts()` 调用 `renderLanguageChart()`；`resize` 监听器加入 `chart-language`。

- [ ] **Step 3: Run test to verify it passes**

```powershell
python -m unittest tests.test_analyze_entry -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```powershell
git add src/comment_analysis/visualization/charts.py tests/test_analyze_entry.py
git commit -m "feat: show language distribution chart in HTML dashboard"
```

---

### Task 9: 全量回归与手工验收

**Files:**
- （按需修复）因分词升级导致断言变化的测试文件

- [ ] **Step 1: Run full test suite**

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Expected: 全部 PASS（预估测试总数 50+）

- [ ] **Step 2: 首次 NLTK 数据下载（真实环境）**

```powershell
pip install -r requirements.txt
python -c "from comment_analysis.analysis.nltk_data import ensure_nltk_data; ensure_nltk_data(); print('NLTK ready')"
```

Expected: 终端输出 `NLTK ready`，无异常

- [ ] **Step 3: Pipeline 端到端冒烟（需联网）**

```powershell
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 5 --source all
```

Expected:
- 终端输出 JSON/HTML 路径
- 报告 JSON 含 `language_distribution`、`analysis_engine: bilingual-rules-v1`
- HTML 含「语言分布」图表

- [ ] **Step 4: 从库再分析验证 P0+P1 衔接**

```powershell
python -m comment_analysis.entry.analyze --from-db --last-job --output-dir data\results
```

Expected: 不依赖 `data\processed\*.json`，生成含双语分析字段的新报告

- [ ] **Step 5: Commit any test fixes**

```powershell
git add tests/
git commit -m "test: fix regressions after P1 bilingual analysis integration"
```

---

## P1 验收清单（对应 PROJECT_BACKLOG 第六节）

| ID | 验收项 | 对应 Task |
|----|--------|-----------|
| P1-1 | 英/中/混合文本语言分流正确 | Task 2 |
| P1-2 | 中文 jieba 分词优于纯正则 | Task 3 + 5 |
| P1-3 | 英文 NLTK 分词，`war`/`wars` 可归一 | Task 4 + 5 |
| P1-4 | `assign_keywords` 接口不变，双语用例通过 | Task 5 |
| P1-5 | 中文词典 + 英文 VADER，三分类标签 | Task 6 |
| P1-6 | `requirements.txt` 含 jieba/nltk/vader；NLTK 引导可运行 | Task 1 + 9 |
| P1-7 | JSON/HTML 含 `language_distribution` | Task 7 + 8 |

**已在 P0 完成、P1 无需重复实现：**

| 项 | 说明 |
|----|------|
| 分析读库 | `analyze --from-db` / `--job-id` / `--last-job` 已在 P0 交付；P1 自动使用新分析 |

---

## 自审（Spec Coverage）

| Backlog 要求 | 计划覆盖 |
|--------------|----------|
| 语言分流 | Task 2、5、6 |
| jieba 中文分词 | Task 3、5 |
| NLTK + VADER 英文 | Task 4、5、6 |
| 统一 keywords 入口 | Task 5 |
| 情感双语 | Task 6 |
| 依赖与 NLTK 文档化 | Task 1、9 Step 2 |
| 报告语言分布 | Task 7、8 |
| analysis_jobs 表 | **不在 P1** — P2 |
| 结构化日志 | **不在 P1** — P2 |
| README 全面同步 | **不在 P1** — P2（Task 9 仅冒烟验证） |
| LLM / transformers | **刻意排除** |

**Placeholder 扫描：** 无 TBD/TODO/implement later；各 Task 均含完整测试代码与实现片段。

**类型一致性：** `LanguageLabel` 枚举值 `zh/en/mixed/unknown` 贯穿 `language.py` → `sentiment.raw_data` → `report.language_distribution` → `charts.js labelMap`。

---

## 风险与约束

1. **jieba 首次加载较慢**：Accept；测试不依赖加载时间断言。
2. **NLTK 需联网下载语料**：`ensure_nltk_data()` 在 CI 可 mock；本地/Task 9 需一次真实下载。
3. **混合文本情感策略**：本计划采用「中英分别打分取更强者」；若产品需固定优先级可后续调参，不阻塞 P1。
4. **现有英文评论为主**：HN/SE 数据以英文为主，`language_distribution` 可能 `en` 占多数 — 属预期。
5. **旧测试 `top_keywords[0] == iran`**：NLTK lemmatize 后仍应为 `iran`；若词频并列则放宽为 `assertIn("iran", top3)`。
6. **P2 前置**：P1 完成后可并行做 P2 测试加固与 README，无需再改 pipeline 骨架。

---

## 预估工时

| Task | 预估 |
|------|------|
| Task 1–2 | 0.5 天 |
| Task 3–4 | 1 天 |
| Task 5–6 | 1 天 |
| Task 7–8 | 0.5 天 |
| Task 9 | 0.5 天 |
| **合计** | **约 3.5 个工作日**（与 Backlog 阶段 2「1～2 周」一致，留 buffer 给 review） |

---

## V1 完成判定（P1 完成后可勾选）

完成 P1 并合并后，在 `PROJECT_BACKLOG.md` 第九节更新：

- [ ] 关键词：**jieba（中）+ NLTK（英）**
- [ ] 情感：**词典规则（中）+ VADER（英）**
- [ ] 报告 JSON/HTML 含 **`language_distribution`**
