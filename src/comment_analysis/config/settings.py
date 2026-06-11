"""配置模块：集中管理项目路径、环境变量和全局运行参数。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# MediaCrawler 子模块默认路径（可通过 MEDIACRAWLER_HOME 覆盖）
DEFAULT_MEDIACRAWLER_HOME = PROJECT_ROOT / "vendor" / "MediaCrawler"

load_dotenv(PROJECT_ROOT / ".env")

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
    database_url: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(DATA_DIR / 'comment_analysis.db').as_posix()}",
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    storage_backend: str = os.getenv("STORAGE_BACKEND", "sqlite")

    # MediaCrawler Bridge
    mediacrawler_home: Path = Path(
        os.getenv("MEDIACRAWLER_HOME", str(DEFAULT_MEDIACRAWLER_HOME))
    ).resolve()
    mediacrawler_uv: str = os.getenv("MEDIACRAWLER_UV", "uv")
    mediacrawler_launcher: Path = Path(
        os.getenv(
            "MEDIACRAWLER_LAUNCHER",
            str(PROJECT_ROOT / "scripts" / "run_mediacrawler.py"),
        )
    )
    mediacrawler_login_type: str = os.getenv("MEDIACRAWLER_LOGIN_TYPE", "qrcode")
    mediacrawler_cookies_tieba: str = os.getenv("MEDIACRAWLER_COOKIES_TIEBA", "")
    mediacrawler_cookies_zhihu: str = os.getenv("MEDIACRAWLER_COOKIES_ZHIHU", "")
    mediacrawler_cookies_weibo: str = os.getenv("MEDIACRAWLER_COOKIES_WEIBO", "")
    mediacrawler_enable_sub_comments: bool = os.getenv(
        "MEDIACRAWLER_ENABLE_SUB_COMMENTS", "false"
    ).strip().lower() in {"1", "true", "yes", "y", "t", "on"}
    mediacrawler_max_sleep_sec: int = int(os.getenv("MEDIACRAWLER_MAX_SLEEP_SEC", "2"))
    mediacrawler_timeout_seconds: int = int(
        os.getenv("MEDIACRAWLER_TIMEOUT_SECONDS", "3600")
    )
    mediacrawler_max_comments_per_note: int = int(
        os.getenv("MEDIACRAWLER_MAX_COMMENTS_PER_NOTE", "10")
    )
    mediacrawler_enable_cdp_mode: bool = os.getenv(
        "MEDIACRAWLER_ENABLE_CDP_MODE", "true"
    ).strip().lower() in {"1", "true", "yes", "y", "t", "on"}
    mediacrawler_cdp_connect_existing: bool = os.getenv(
        "MEDIACRAWLER_CDP_CONNECT_EXISTING", "true"
    ).strip().lower() in {"1", "true", "yes", "y", "t", "on"}

    # 常用路径
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    raw_dir: Path = RAW_DIR
    processed_dir: Path = PROCESSED_DIR
    results_dir: Path = RESULTS_DIR
    log_dir: Path = LOG_DIR


# 全局配置实例，其他模块直接导入使用
settings = Settings()
