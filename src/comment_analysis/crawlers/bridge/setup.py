"""MediaCrawler 子模块就绪检测与依赖安装。"""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

from comment_analysis.config.settings import DATA_DIR
from comment_analysis.crawlers.bridge.exceptions import MediaCrawlerError

UV_SYNC_TIMEOUT_SECONDS = 600
DEPS_MARKER = DATA_DIR / ".mediacrawler_uv_synced"
_uv_sync_lock = threading.Lock()


def resolve_mediacrawler_home(home: Path | str) -> Path:
    """解析并规范化 MediaCrawler 根目录。"""
    return Path(home).resolve()


def submodule_init_hint() -> str:
    """返回子模块未初始化时的修复指引。"""
    return (
        "MediaCrawler 子模块未初始化。请任选其一：\n"
        "  1) 克隆时拉取子模块：git clone --recurse-submodules <repo-url>\n"
        "  2) 已克隆主仓后：git submodule update --init --recursive\n"
        "  3) 或执行：scripts/bootstrap_mediacrawler.ps1（Windows）/"
        "scripts/bootstrap_mediacrawler.sh（Linux/macOS）"
    )


def is_submodule_initialized(home: Path) -> bool:
    """子模块目录存在且包含 MediaCrawler 入口 main.py。"""
    return home.is_dir() and (home / "main.py").is_file()


def _marker_is_stale(home: Path) -> bool:
    """uv.lock 比 marker 新时视为需要重新 sync。"""
    if not DEPS_MARKER.is_file():
        return True
    uv_lock = home / "uv.lock"
    if not uv_lock.is_file():
        return False
    return uv_lock.stat().st_mtime > DEPS_MARKER.stat().st_mtime


def _run_uv_sync(home: Path, uv_executable: str) -> None:
    uv_cmd = uv_executable.strip() or "uv"
    try:
        completed = subprocess.run(
            [uv_cmd, "sync"],
            cwd=str(home),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=UV_SYNC_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise MediaCrawlerError(
            f"MediaCrawler 依赖安装超时（>{UV_SYNC_TIMEOUT_SECONDS}s）。"
            f"请手动执行：cd {home} && {uv_cmd} sync"
        ) from exc
    except FileNotFoundError as exc:
        raise MediaCrawlerError(
            f"未找到 `{uv_cmd}`。请安装 uv 或将 MEDIACRAWLER_UV 设为空以使用当前 Python。"
        ) from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if len(detail) > 1500:
            detail = detail[-1500:]
        raise MediaCrawlerError(
            f"MediaCrawler 依赖安装失败（{uv_cmd} sync，code={completed.returncode}）：{detail}"
        )

    DEPS_MARKER.parent.mkdir(parents=True, exist_ok=True)
    DEPS_MARKER.touch()


def ensure_mediacrawler_deps(home: Path, uv_executable: str) -> None:
    """首次或 lock 变更时在子模块目录执行 uv sync（并行安全）。"""
    if not (home / "pyproject.toml").is_file():
        return
    with _uv_sync_lock:
        if not _marker_is_stale(home):
            return
        _run_uv_sync(home, uv_executable)


def ensure_mediacrawler_ready(home: Path | str, uv_executable: str) -> Path:
    """校验子模块已 init，并在需要时安装 MediaCrawler 依赖。"""
    resolved = resolve_mediacrawler_home(home)

    if not resolved.is_dir():
        raise MediaCrawlerError(
            f"MediaCrawler 目录不存在：{resolved}\n{submodule_init_hint()}"
        )
    if not is_submodule_initialized(resolved):
        raise MediaCrawlerError(
            f"MediaCrawler 子模块目录为空或不完整：{resolved}\n{submodule_init_hint()}"
        )

    ensure_mediacrawler_deps(resolved, uv_executable)
    return resolved
