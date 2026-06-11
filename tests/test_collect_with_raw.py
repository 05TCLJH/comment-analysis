"""collect_with_raw 测试：mock 采集器返回 raw + records。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.entry.crawl import collect_with_raw
from comment_analysis.models import CommentRecord


class CollectWithRawTest(unittest.TestCase):
    def test_collect_with_raw_returns_platform_payloads(self) -> None:
        fake_record = CommentRecord(
            platform="hackernews",
            content="war update",
            source_url="https://example.com/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            comment_id="hn-1",
        )
        fake_crawler = MagicMock()
        fake_crawler.platform_name = "hackernews"
        fake_crawler.crawl_with_raw.return_value = (
            {"hits": [{"objectID": "hn-1"}]},
            [fake_record],
        )

        with patch("comment_analysis.entry.crawl._build_crawlers", return_value=[fake_crawler]):
            bundles = collect_with_raw(keyword="test", max_records=5, source="hackernews")

        self.assertEqual(len(bundles), 1)
        self.assertEqual(bundles[0]["platform"], "hackernews")
        self.assertIn("hits", bundles[0]["raw_payload"])
        self.assertEqual(bundles[0]["records"][0].comment_id, "hn-1")
        fake_crawler.close.assert_called_once()

    def test_collect_with_raw_cn_all(self) -> None:
        fake_record = CommentRecord(
            platform="tieba",
            content="中文评论",
            source_url="https://tieba.baidu.com/p/1",
            crawl_time=datetime(2026, 6, 11, 10, 0, 0),
            comment_id="tb-1",
        )
        crawlers = []
        for platform in ("tieba", "zhihu", "weibo"):
            crawler = MagicMock()
            crawler.platform_name = platform
            crawler.crawl_with_raw.return_value = (
                {"line_count": 1},
                [fake_record] if platform == "tieba" else [],
            )
            crawlers.append(crawler)

        with patch("comment_analysis.entry.crawl._build_crawlers", return_value=crawlers):
            bundles = collect_with_raw(
                keyword="美以伊战争",
                max_records=5,
                source="cn_all",
                job_id="job-cn",
            )

        self.assertEqual(len(bundles), 3)
        self.assertEqual(bundles[0]["platform"], "tieba")
        self.assertEqual(len(bundles[0]["records"]), 1)


if __name__ == "__main__":
    unittest.main()
