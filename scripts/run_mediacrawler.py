#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""comment-analysis 调用 MediaCrawler 的启动器。

在 MediaCrawler 项目目录下运行，通过 MC_* 环境变量覆盖 config 后执行 main。
仅供非商业学习用途，遵守 MediaCrawler LICENSE 与各平台 ToS。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "y", "t", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _apply_config_overrides() -> None:
    import config

    config.PLATFORM = os.environ.get("MC_PLATFORM", config.PLATFORM)
    config.KEYWORDS = os.environ.get("MC_KEYWORDS", config.KEYWORDS)
    config.CRAWLER_TYPE = "search"
    config.LOGIN_TYPE = os.environ.get("MC_LOGIN_TYPE", config.LOGIN_TYPE)
    config.SAVE_DATA_OPTION = "jsonl"
    config.SAVE_DATA_PATH = os.environ.get("MC_SAVE_DATA_PATH", config.SAVE_DATA_PATH)
    config.ENABLE_GET_MEIDAS = False
    config.ENABLE_GET_COMMENTS = True
    config.ENABLE_GET_SUB_COMMENTS = _env_bool("MC_ENABLE_SUB_COMMENTS", False)
    config.ENABLE_GET_WORDCLOUD = False
    config.CRAWLER_MAX_NOTES_COUNT = _env_int(
        "MC_CRAWLER_MAX_NOTES_COUNT",
        config.CRAWLER_MAX_NOTES_COUNT,
    )
    config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = _env_int(
        "MC_MAX_COMMENTS_COUNT_SINGLENOTES",
        config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES,
    )
    config.CRAWLER_MAX_SLEEP_SEC = _env_int(
        "MC_CRAWLER_MAX_SLEEP_SEC",
        config.CRAWLER_MAX_SLEEP_SEC,
    )
    config.ENABLE_CDP_MODE = _env_bool("MC_ENABLE_CDP_MODE", False)
    config.CDP_CONNECT_EXISTING = _env_bool("MC_CDP_CONNECT_EXISTING", False)
    config.HEADLESS = _env_bool("MC_HEADLESS", False)
    config.CDP_HEADLESS = config.HEADLESS
    cookies = os.environ.get("MC_COOKIES", "").strip()
    if cookies:
        config.COOKIES = cookies
        config.LOGIN_TYPE = "cookie"


def main() -> None:
    mc_home = Path(os.environ.get("MEDIACRAWLER_HOME", os.getcwd())).resolve()
    os.chdir(mc_home)
    if str(mc_home) not in sys.path:
        sys.path.insert(0, str(mc_home))

    _apply_config_overrides()

    import main as mediacrawler_main
    from tools.app_runner import run

    def _force_stop() -> None:
        current = mediacrawler_main.crawler
        if not current:
            return
        cdp_manager = getattr(current, "cdp_manager", None)
        launcher = getattr(cdp_manager, "launcher", None)
        if not launcher:
            return
        try:
            launcher.cleanup()
        except Exception:
            pass

    run(
        mediacrawler_main.main,
        mediacrawler_main.async_cleanup,
        cleanup_timeout_seconds=15.0,
        on_first_interrupt=_force_stop,
    )


if __name__ == "__main__":
    main()
