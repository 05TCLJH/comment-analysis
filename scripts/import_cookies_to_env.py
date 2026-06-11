#!/usr/bin/env python3
"""将 Netscape cookie 文件写入 .env（本地使用，勿提交）。"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def netscape_to_cookie_string(path: Path) -> str:
    pairs: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        name, value = parts[5], parts[6]
        pairs.append(f"{name}={value}")
    return "; ".join(pairs)


def _validate(label: str, cookie: str, keys: tuple[str, ...]) -> None:
    missing = [k for k in keys if f"{k}=" not in cookie]
    if missing:
        print(f"WARN {label}: missing keys {missing}")
    else:
        print(f"OK {label}: {len(cookie)} chars")


def main() -> None:
    if len(sys.argv) not in (3, 4):
        print(
            "Usage: import_cookies_to_env.py <tieba.txt> <weibo.txt> [zhihu.txt]"
        )
        sys.exit(1)

    tieba_path = Path(sys.argv[1])
    weibo_path = Path(sys.argv[2])
    tieba = netscape_to_cookie_string(tieba_path)
    weibo = netscape_to_cookie_string(weibo_path)

    _validate("tieba", tieba, ("BDUSS", "STOKEN"))
    _validate("weibo", weibo, ("SUB", "SUBP"))

    zhihu_line = ""
    if len(sys.argv) == 4:
        zhihu = netscape_to_cookie_string(Path(sys.argv[3]))
        _validate("zhihu", zhihu, ("z_c0",))
        zhihu_line = f"MEDIACRAWLER_COOKIES_ZHIHU={zhihu}"

    env_path = PROJECT_ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.is_file() else []
    keep = [line for line in lines if not line.strip().startswith("MEDIACRAWLER_")]
    block = [
        "",
        "# MediaCrawler Bridge（Cookie 登录，勿提交 Git）",
        "MEDIACRAWLER_LOGIN_TYPE=cookie",
        "MEDIACRAWLER_ENABLE_CDP_MODE=false",
        "MEDIACRAWLER_CDP_CONNECT_EXISTING=false",
        "MEDIACRAWLER_MAX_SLEEP_SEC=3",
        "MEDIACRAWLER_MAX_COMMENTS_PER_NOTE=10",
        f"MEDIACRAWLER_COOKIES_TIEBA={tieba}",
        f"MEDIACRAWLER_COOKIES_WEIBO={weibo}",
    ]
    if zhihu_line:
        block.append(zhihu_line)
    env_path.write_text("\n".join(keep + block) + "\n", encoding="utf-8")
    print(f"Updated {env_path}")


if __name__ == "__main__":
    main()
