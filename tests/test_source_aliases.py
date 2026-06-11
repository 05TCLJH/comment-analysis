"""数据源别名测试。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.crawlers.bridge.sources import resolve_platforms
from comment_analysis.entry.crawl import _build_crawlers


class SourceAliasesTest(unittest.TestCase):
    def test_all_equals_en_all(self) -> None:
        self.assertEqual(
            resolve_platforms("all"),
            ["hackernews", "stackexchange"],
        )
        self.assertEqual(resolve_platforms("all"), resolve_platforms("en_all"))

    def test_cn_all(self) -> None:
        self.assertEqual(
            resolve_platforms("cn_all"),
            ["tieba", "zhihu", "weibo"],
        )

    def test_global_all(self) -> None:
        self.assertEqual(
            resolve_platforms("global_all"),
            [
                "hackernews",
                "stackexchange",
                "tieba",
                "zhihu",
                "weibo",
            ],
        )

    def test_build_crawlers_global_all_count(self) -> None:
        crawlers = _build_crawlers(
            keyword="test",
            max_records=5,
            source="global_all",
            job_id="job-test",
        )
        self.assertEqual(len(crawlers), 5)
        self.assertEqual(
            [crawler.platform_name for crawler in crawlers],
            [
                "hackernews",
                "stackexchange",
                "tieba",
                "zhihu",
                "weibo",
            ],
        )

    def test_invalid_source(self) -> None:
        with self.assertRaises(ValueError):
            resolve_platforms("unknown")


if __name__ == "__main__":
    unittest.main()
