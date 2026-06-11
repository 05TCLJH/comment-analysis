"""可视化模块测试：验证 HTML 仪表盘渲染关键结构。"""

from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from comment_analysis.visualization.charts import render_analysis_report


class VisualizationTest(unittest.TestCase):
    def test_render_analysis_report_includes_v2_dashboard_markers(self) -> None:
        report = {
            "generated_at": "2026-06-11T18:00:00",
            "date_range": {"start": "2026-01-01", "end": "2026-06-11"},
            "records": [],
            "insights": [
                {
                    "id": "sample",
                    "title": "样本洞察",
                    "body": "测试正文",
                    "kind": "keyword",
                    "priority": 1,
                }
            ],
            "word_cloud": [{"name": "war", "value": 3, "dominant_sentiment": "消极"}],
            "sentiment_score_summary": {"histogram": [], "by_platform": []},
        }

        html = render_analysis_report(report)

        self.assertIn("chart-wordcloud", html)
        self.assertIn("chart-keyword-sentiment", html)
        self.assertIn("chart-sentiment-score", html)
        self.assertIn("insight-strip", html)
        self.assertIn("echarts-wordcloud", html)
        self.assertIn("舆情监测编辑室", html)


if __name__ == "__main__":
    unittest.main()
