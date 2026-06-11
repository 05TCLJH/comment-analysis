"""分析入口：读取本地文件并输出多维分析结果与展示页面。"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from comment_analysis.analysis import assign_keywords, assign_sentiment, build_analysis_report
from comment_analysis.config.settings import settings
from comment_analysis.models import CommentRecord
from comment_analysis.storage.sqlite import SqliteCommentRepository
from comment_analysis.visualization import write_analysis_report


def _parse_csv_cell(value: str) -> Any:
    """将 CSV 中像 JSON 的单元格还原为结构化数据。"""
    text = value.strip()
    if not text:
        return ""
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def load_records(input_path: Path) -> list[CommentRecord]:
    """从 JSON 或 CSV 文件中读取评论数据。"""
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("JSON 输入文件格式不正确，必须是评论列表")
        return [CommentRecord.from_dict(item) for item in payload if isinstance(item, dict)]

    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        return [
            CommentRecord.from_dict({key: _parse_csv_cell(value) for key, value in row.items()})
            for row in rows
        ]

    raise ValueError(f"不支持的输入格式：{input_path.suffix}")


def _build_output_path(output_dir: Path, input_path: Path) -> Path:
    """生成 JSON 报告的输出路径。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{input_path.stem}_analysis_{timestamp}.json"


def run_analysis_from_db(
    *,
    database_url: str,
    job_id: str | None = None,
    last_job: bool = False,
    output_dir: Path | None = None,
    top_n: int = 20,
    per_record_top_n: int = 5,
) -> dict[str, object]:
    """从 SQLite 读取评论并执行多维分析。"""
    repo = SqliteCommentRepository(database_url)
    try:
        resolved_job_id = job_id
        if last_job and not resolved_job_id:
            resolved_job_id = repo.get_last_crawl_job_id()
        if not resolved_job_id:
            raise ValueError("需要 --job-id 或 --last-job")

        records = repo.fetch_comments(job_id=resolved_job_id)
        if not records:
            raise ValueError(f"job {resolved_job_id} 下没有评论数据")

        records_with_keywords = assign_keywords(records, top_n=per_record_top_n)
        enriched_records = assign_sentiment(records_with_keywords)
        report = build_analysis_report(enriched_records, top_n=top_n)

        target_dir = output_dir or settings.results_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = target_dir / f"job_{resolved_job_id}_analysis_{timestamp}.json"
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report_path = write_analysis_report(report, target_dir, output_path.stem)

        return {
            "job_id": resolved_job_id,
            "database_url": database_url,
            "output_path": output_path,
            "report_path": report_path,
            "total_records": report["total_records"],
        }
    finally:
        repo.close()


def run_keyword_analysis(
    input_path: Path,
    output_dir: Path | None = None,
    top_n: int = 20,
    per_record_top_n: int = 5,
) -> dict[str, object]:
    """执行关键词、情感和多维统计分析。"""
    target_dir = output_dir or settings.results_dir
    records = load_records(input_path)
    records_with_keywords = assign_keywords(records, top_n=per_record_top_n)
    enriched_records = assign_sentiment(records_with_keywords)
    report = build_analysis_report(enriched_records, top_n=top_n)

    output_path = _build_output_path(target_dir, input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    report_path = write_analysis_report(report, target_dir, output_path.stem)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "report_path": report_path,
        "total_records": report["total_records"],
        "unique_keywords": report["unique_keywords"],
        "top_keywords": report["top_keywords"],
        "daily_trend": report["daily_trend"],
        "platform_distribution": report["platform_distribution"],
        "sentiment_distribution": report["sentiment_distribution"],
        "platform_sentiment_breakdown": report["platform_sentiment_breakdown"],
    }


def main() -> None:
    """解析命令行参数并运行分析流程。"""
    parser = argparse.ArgumentParser(description="读取本地评论文件或 SQLite 并执行多维分析")
    parser.add_argument("input_path", nargs="?", default="", help="待分析的 JSON 或 CSV 文件路径")
    parser.add_argument("--from-db", action="store_true", help="从 SQLite 读取")
    parser.add_argument("--job-id", default="", help="指定 crawl job_id")
    parser.add_argument("--last-job", action="store_true", help="使用最近一次 crawl job")
    parser.add_argument("--database-url", default="", help="覆盖 DATABASE_URL")
    parser.add_argument("--top-n", type=int, default=20, help="输出前多少个高频关键词")
    parser.add_argument(
        "--per-record-top-n",
        type=int,
        default=5,
        help="每条评论最多提取多少个关键词",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="结果输出目录，默认写入 data/results",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None

    if args.from_db:
        database_url = args.database_url or settings.database_url
        result = run_analysis_from_db(
            database_url=database_url,
            job_id=args.job_id or None,
            last_job=args.last_job,
            output_dir=output_dir,
            top_n=args.top_n,
            per_record_top_n=args.per_record_top_n,
        )
        print("分析完成（SQLite）")
        print(f"任务 ID：{result['job_id']}")
        print(f"评论数量：{result['total_records']}")
        print(f"JSON 报告：{result['output_path']}")
        print(f"HTML 仪表盘：{result['report_path']}")
        return

    if not args.input_path:
        parser.error("请提供 input_path，或使用 --from-db")

    result = run_keyword_analysis(
        input_path=Path(args.input_path).resolve(),
        output_dir=output_dir,
        top_n=args.top_n,
        per_record_top_n=args.per_record_top_n,
    )

    print("分析完成")
    print(f"输入文件：{result['input_path']}")
    print(f"评论数量：{result['total_records']}")
    print(f"关键词种类：{result['unique_keywords']}")
    print(f"JSON 报告：{result['output_path']}")
    print(f"HTML 仪表盘：{result['report_path']}")


if __name__ == "__main__":
    main()
