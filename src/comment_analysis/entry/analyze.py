"""分析入口：读取本地文件并输出关键词统计结果。"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from comment_analysis.analysis import assign_keywords, build_keyword_report
from comment_analysis.config.settings import settings
from comment_analysis.models import CommentRecord


def _parse_csv_cell(value: str) -> Any:
    """把 CSV 单元格中的 JSON 字符串还原为结构化数据。"""
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
    """从 JSON 或 CSV 文件中读取评论列表。"""
    suffix = input_path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("JSON 输入文件格式不正确，必须是评论列表")
        return [CommentRecord.from_dict(item) for item in payload if isinstance(item, dict)]

    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        parsed_rows = []
        for row in rows:
            parsed_row = {key: _parse_csv_cell(value) for key, value in row.items()}
            parsed_rows.append(parsed_row)
        return [CommentRecord.from_dict(item) for item in parsed_rows]

    raise ValueError(f"不支持的输入格式：{input_path.suffix}")


def _build_output_path(output_dir: Path, input_path: Path) -> Path:
    """生成分析结果输出路径。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{input_path.stem}_keywords_{timestamp}.json"


def run_keyword_analysis(
    input_path: Path,
    output_dir: Path | None = None,
    top_n: int = 20,
    per_record_top_n: int = 5,
) -> dict[str, object]:
    """执行关键词统计并把结果保存为 JSON 文件。"""
    target_dir = output_dir or settings.results_dir
    records = load_records(input_path)
    records_with_keywords = assign_keywords(records, top_n=per_record_top_n)
    report = build_keyword_report(records_with_keywords, top_n=top_n)

    output_path = _build_output_path(target_dir, input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "input_path": input_path,
        "output_path": output_path,
        "total_records": report["total_records"],
        "unique_keywords": report["unique_keywords"],
        "top_keywords": report["top_keywords"],
    }


def main() -> None:
    """解析命令行参数并执行关键词统计。"""
    parser = argparse.ArgumentParser(description="读取本地评论文件并执行关键词统计")
    parser.add_argument("input_path", help="待分析的 JSON 或 CSV 文件路径")
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
    result = run_keyword_analysis(
        input_path=Path(args.input_path).resolve(),
        output_dir=output_dir,
        top_n=args.top_n,
        per_record_top_n=args.per_record_top_n,
    )

    print("关键词统计完成")
    print(f"输入文件：{result['input_path']}")
    print(f"评论数量：{result['total_records']}")
    print(f"关键词种类：{result['unique_keywords']}")
    print(f"输出文件：{result['output_path']}")


if __name__ == "__main__":
    main()
