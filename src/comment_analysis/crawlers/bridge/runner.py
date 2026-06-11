"""MediaCrawler 子进程运行器。"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from comment_analysis.config.settings import settings
from comment_analysis.crawlers.bridge.exceptions import MediaCrawlerError
from comment_analysis.crawlers.bridge.setup import ensure_mediacrawler_ready

MEDIACRAWLER_PLATFORM_MAP = {
    "tieba": "tieba",
    "zhihu": "zhihu",
    "weibo": "wb",
}


@dataclass(slots=True)
class MediaCrawlerRunResult:
    """子进程执行结果摘要。"""

    returncode: int
    stdout: str
    stderr: str
    save_path: Path


class MediaCrawlerRunner:
    """通过子进程调用 MediaCrawler 完成关键词搜索与评论抓取。"""

    def __init__(
        self,
        *,
        mediacrawler_home: Path | None = None,
        launcher_path: Path | None = None,
        uv_executable: str | None = None,
        login_type: str | None = None,
        timeout_seconds: int = 3600,
    ) -> None:
        self.mediacrawler_home = Path(
            mediacrawler_home or settings.mediacrawler_home
        ).resolve()
        self.launcher_path = Path(
            launcher_path or settings.mediacrawler_launcher
        ).resolve()
        self.uv_executable = uv_executable or settings.mediacrawler_uv
        self.login_type = login_type or settings.mediacrawler_login_type
        self.timeout_seconds = timeout_seconds

    def _resolve_cookies(self, platform: str) -> str:
        mapping = {
            "tieba": settings.mediacrawler_cookies_tieba,
            "zhihu": settings.mediacrawler_cookies_zhihu,
            "weibo": settings.mediacrawler_cookies_weibo,
        }
        return mapping.get(platform, "").strip()

    def _build_command(self) -> list[str]:
        launcher = str(self.launcher_path)
        if self.uv_executable:
            return [self.uv_executable, "run", "python", launcher]
        return [sys.executable, launcher]

    def run(
        self,
        *,
        platform: str,
        keyword: str,
        save_path: Path,
        max_notes: int,
        max_comments_per_note: int = 10,
    ) -> MediaCrawlerRunResult:
        """执行 MediaCrawler 并写入 save_path。"""
        normalized_platform = platform.strip().lower()
        mc_platform = MEDIACRAWLER_PLATFORM_MAP.get(normalized_platform)
        if not mc_platform:
            raise MediaCrawlerError(f"Bridge 不支持的平台：{platform}")

        self.mediacrawler_home = ensure_mediacrawler_ready(
            self.mediacrawler_home,
            self.uv_executable,
        )
        if not self.launcher_path.is_file():
            raise MediaCrawlerError(
                f"MediaCrawler 启动脚本不存在：{self.launcher_path}"
            )

        save_path = Path(save_path).resolve()
        save_path.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["MEDIACRAWLER_HOME"] = str(self.mediacrawler_home)
        env["MC_PLATFORM"] = mc_platform
        env["MC_KEYWORDS"] = keyword.strip()
        env["MC_SAVE_DATA_PATH"] = str(save_path)
        env["MC_CRAWLER_MAX_NOTES_COUNT"] = str(max(1, max_notes))
        env["MC_MAX_COMMENTS_COUNT_SINGLENOTES"] = str(max(1, max_comments_per_note))
        env["MC_LOGIN_TYPE"] = self.login_type
        env["MC_ENABLE_SUB_COMMENTS"] = (
            "true" if settings.mediacrawler_enable_sub_comments else "false"
        )
        env["MC_CRAWLER_MAX_SLEEP_SEC"] = str(settings.mediacrawler_max_sleep_sec)
        env["MC_ENABLE_CDP_MODE"] = (
            "true" if settings.mediacrawler_enable_cdp_mode else "false"
        )
        env["MC_CDP_CONNECT_EXISTING"] = (
            "true" if settings.mediacrawler_cdp_connect_existing else "false"
        )
        env["MC_HEADLESS"] = "false"
        env["PYTHONUNBUFFERED"] = "1"
        cookies = self._resolve_cookies(normalized_platform)
        if cookies:
            env["MC_COOKIES"] = cookies

        completed = subprocess.run(
            self._build_command(),
            cwd=str(self.mediacrawler_home),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_seconds,
            check=False,
        )

        result = MediaCrawlerRunResult(
            returncode=completed.returncode,
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            save_path=save_path,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            if len(detail) > 2000:
                detail = detail[-2000:]
            raise MediaCrawlerError(
                f"MediaCrawler 子进程失败（platform={normalized_platform}, "
                f"code={completed.returncode}）：{detail}"
            )
        return result
