"""总入口：一键执行采集、清洗和本地存储。"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from comment_analysis.config.settings import settings
from comment_analysis.entry.clean import clean_records
from comment_analysis.entry.crawl import collect_records
from comment_analysis.storage import build_local_repository


def _build_output_path(target_dir: Path, output_format: str) -> Path:
    """按照输出格式生成本地文件路径。"""
    normalized_format = output_format.strip().lower()
    suffix_mapping = {
        "json": ".json",
        "csv": ".csv",
    }
    if normalized_format not in suffix_mapping:
        raise ValueError(f"不支持的输出格式：{output_format}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return target_dir / f"comments_{timestamp}{suffix_mapping[normalized_format]}"


def run_minimal_pipeline(
    keyword: str = "美以伊战争",
    output_dir: Path | None = None,
    max_records: int = 20,
    output_format: str = "json",
    source: str = "hackernews",
) -> dict[str, object]:
    """执行最小闭环流程，并返回运行结果摘要。"""
    target_dir = output_dir or settings.processed_dir
    output_path = _build_output_path(target_dir, output_format)

    raw_records = collect_records(keyword=keyword, max_records=max_records, source=source)
    cleaned_records = clean_records(raw_records)

    repository = build_local_repository(output_path, output_format)
    repository.save_many(cleaned_records)

    return {
        "keyword": keyword,
        "source": source,
        "raw_count": len(raw_records),
        "cleaned_count": len(cleaned_records),
        "output_format": output_format.lower(),
        "output_path": output_path,
    }


def main() -> None:
    """解析命令行参数并启动最小闭环流程。"""
    parser = argparse.ArgumentParser(description="运行评论采集、清洗、存储最小流程")
    parser.add_argument("--keyword", default="美以伊战争", help="采集时使用的关键词")
    parser.add_argument("--limit", type=int, default=20, help="最多抓取多少条评论")
    parser.add_argument(
        "--output-format",
        default="json",
        choices=("json", "csv"),
        help="结果保存格式，支持 json 或 csv",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="结果输出目录，默认写入 data/processed",
    )
    parser.add_argument(
        "--source",
        default="hackernews",
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
        help="采集数据源；all/en_all=国外双源，cn_all=国内三源，global_all=六源",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    result = run_minimal_pipeline(
        keyword=args.keyword,
        output_dir=output_dir,
        max_records=args.limit,
        output_format=args.output_format,
        source=args.source,
    )

    print("最小流程执行完成")
    print(f"关键词：{result['keyword']}")
    print(f"数据源：{result['source']}")
    print(f"采集数量：{result['raw_count']}")
    print(f"清洗后数量：{result['cleaned_count']}")
    print(f"输出格式：{result['output_format']}")
    print(f"输出文件：{result['output_path']}")


if __name__ == "__main__":
    main()
