#!/usr/bin/env bash
# MediaCrawler 子模块与依赖初始化（Linux / macOS）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> 初始化 Git 子模块 vendor/MediaCrawler ..."
git submodule update --init --recursive

MC_HOME="$ROOT/vendor/MediaCrawler"
if [[ ! -f "$MC_HOME/main.py" ]]; then
  echo "子模块不完整：未找到 $MC_HOME/main.py" >&2
  echo "请使用: git clone --recurse-submodules <repo-url>" >&2
  exit 1
fi

echo "==> uv sync（MediaCrawler 依赖）..."
(cd "$MC_HOME" && uv sync)

echo ""
echo "完成。首次跑中文源前请安装 Playwright 浏览器驱动："
echo "  cd vendor/MediaCrawler"
echo "  uv run playwright install"
echo ""
echo "Bridge 配置与登录说明见 docs/MEDIACRAWLER_BRIDGE.md"
