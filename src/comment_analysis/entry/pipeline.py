"""全链路入口：采集 → raw → 清洗 → SQLite → 分析 → HTML。"""

from __future__ import annotations

import argparse
from pathlib import Path

from comment_analysis.config.settings import settings
from comment_analysis.pipeline.orchestrator import FullPipeline


def run_full_pipeline(
    keyword: str = "美以伊战争",
    limit: int = 20,
    source: str = "all",
    top_n: int = 20,
    per_record_top_n: int = 5,
    results_dir: Path | None = None,
) -> dict[str, object]:
    pipeline = FullPipeline(
        keyword=keyword,
        max_records=limit,
        source=source,
        storage_backend="sqlite",
        results_dir=results_dir,
    )
    try:
        return pipeline.run(top_n=top_n, per_record_top_n=per_record_top_n)
    finally:
        pipeline.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="运行评论分析全链路（SQLite 主存储）")
    parser.add_argument("--keyword", default="美以伊战争")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--source",
        default="all",
        choices=(
            "hackernews",
            "stackexchange",
            "tieba",
            "zhihu",
            "weibo",
            "cn_all",
            "en_all",
            "global_all",
            "all",
        ),
        help="数据源：单源、cn_all（国内三平台）、en_all/all（国外双平台）、global_all（六源）",
    )
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--per-record-top-n", type=int, default=5)
    parser.add_argument("--output-dir", default="", help="结果目录，默认 data/results")
    args = parser.parse_args()

    results_dir = Path(args.output_dir).resolve() if args.output_dir else None
    result = run_full_pipeline(
        keyword=args.keyword,
        limit=args.limit,
        source=args.source,
        top_n=args.top_n,
        per_record_top_n=args.per_record_top_n,
        results_dir=results_dir,
    )

    print("全链路执行完成")
    print(f"任务 ID：{result['job_id']}")
    print(f"数据库：{result['database_url']}")
    print(f"采集/清洗：{result['raw_count']} / {result['cleaned_count']}")
    print(f"新入库：{result['inserted_count']}")
    print(f"JSON 报告：{result['report_json_path']}")
    print(f"HTML 仪表盘：{result['report_html_path']}")


if __name__ == "__main__":
    main()
