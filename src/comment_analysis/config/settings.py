"""配置模块：集中管理项目路径、环境变量和全局运行参数。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"


@dataclass(slots=True)
class Settings:
    """项目运行配置。

    后续所有模块都可以直接从这里读取统一配置。
    """

    # 运行环境变量
    user_agent: str = os.getenv("USER_AGENT", "")
    proxy: str = os.getenv("PROXY", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # 常用路径
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    raw_dir: Path = RAW_DIR
    processed_dir: Path = PROCESSED_DIR
    results_dir: Path = RESULTS_DIR
    log_dir: Path = LOG_DIR


# 全局配置实例，其他模块直接导入使用
settings = Settings()

