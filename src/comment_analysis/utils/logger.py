"""日志工具模块：统一管理项目运行日志和异常排查信息。"""

from __future__ import annotations

import logging
from pathlib import Path


def get_logger(name: str, log_dir: Path | None = None, level: str = "INFO") -> logging.Logger:
    """创建一个基础日志对象。

    参数：
        name: 日志名称，通常使用当前模块名。
        log_dir: 日志目录，不传则只输出到控制台。
        level: 日志级别。

    返回：
        配置好的日志对象。
    """
    logger = logging.getLogger(name)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    logger.setLevel(level.upper())
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # 控制台输出
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 文件输出
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
