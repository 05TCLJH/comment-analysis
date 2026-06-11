# MediaCrawler Bridge 接入指南

> 文档版本：2026-06-11  
> 适用：comment-analysis 通过 Git Submodule + 子进程调用 [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) 抓取贴吧、知乎、微博评论。

## 合规说明

- MediaCrawler 使用 **NON-COMMERCIAL LEARNING LICENSE 1.1**，仅限非商业学习与研究。
- 请遵守各平台服务条款，合理控制抓取频率，勿大规模干扰平台运营。
- 本 Bridge **不复制** MediaCrawler 源码进主仓，通过 **Git Submodule**（`vendor/MediaCrawler`）引用上游，子进程调用其 CLI 并读取 JSONL 输出。

## 克隆与子模块

**推荐（一次拉齐主仓 + MediaCrawler）：**

```powershell
git clone --recurse-submodules https://github.com/<your-org>/comment-analysis.git
cd comment-analysis
```

**已 clone 主仓但子模块为空：**

```powershell
git submodule update --init --recursive
```

或执行 bootstrap：

```powershell
.\scripts\bootstrap_mediacrawler.ps1
```

## 前置环境

1. **子模块已 init**：`vendor/MediaCrawler/main.py` 存在（见上节）
2. comment-analysis 已安装依赖：`pip install -r requirements.txt`
3. **首次跑中文源**会自动在子模块目录执行 `uv sync`（也可先跑 bootstrap）
4. **Playwright 浏览器**（手动一次）：

   ```powershell
   cd vendor\MediaCrawler
   uv run playwright install
   ```

5. **Chrome CDP**（可选，默认开启）：远程调试端口 9222，见下文「首次登录」

可选：在 `.env` 用 `MEDIACRAWLER_HOME` 指向外部 MediaCrawler 目录（如 `D:/MediaCrawler`），跳过 submodule。

## 环境变量（`.env`）

```env
# 默认 vendor/MediaCrawler 子模块；外部安装时可覆盖：
# MEDIACRAWLER_HOME=D:/MediaCrawler
MEDIACRAWLER_LOGIN_TYPE=qrcode
# 跑批时可改为 cookie 并填写对应平台 Cookie：
# MEDIACRAWLER_COOKIES_TIEBA=
# MEDIACRAWLER_COOKIES_ZHIHU=
# MEDIACRAWLER_COOKIES_WEIBO=
MEDIACRAWLER_ENABLE_SUB_COMMENTS=false
MEDIACRAWLER_MAX_SLEEP_SEC=2
MEDIACRAWLER_MAX_COMMENTS_PER_NOTE=10
# cn_all 等中文多源并行子进程数（默认 3；设为 1 恢复串行）
MEDIACRAWLER_PARALLEL_WORKERS=3
```

## 并行采集

`cn_all` / `global_all` 中的**贴吧、知乎、微博**默认 **并行** 抓取（各平台独立子进程与落盘目录）。英文 API 源仍串行。

| `MEDIACRAWLER_PARALLEL_WORKERS` | 行为 |
|--------------------------------|------|
| `3`（默认） | 三中文平台同时跑，总耗时约等于最慢平台 |
| `2` | 最多 2 路并行 |
| `1` | 恢复串行（省资源、降低风控风险） |

并行时每个平台仍使用各自的 Cookie（`MEDIACRAWLER_COOKIES_*`）与 `browser_data/{platform}` 目录。

## `--source` 别名

| 值 | 平台 |
|----|------|
| `tieba` / `zhihu` / `weibo` | 单源（Bridge） |
| `hackernews` / `stackexchange` | 单源（公开 API） |
| **`cn_all`** | tieba + zihu + weibo |
| **`en_all`** / **`all`** | hackernews + stackexchange（默认 `all` 行为不变） |
| **`global_all`** | 上述五源（2 国外 + 3 国内） |

中文关键词（如「美以伊战争」）原样传给 MediaCrawler；英文源仍会做查询词映射。

## 首次登录

各中文平台首次运行需扫码登录或配置 Cookie。MediaCrawler 会把登录态缓存在 `vendor/MediaCrawler/browser_data/`（或你配置的 `MEDIACRAWLER_HOME` 下）。

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"

python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 5 --source tieba
```

浏览器弹出后完成扫码即可。

## 常用命令

```powershell
# 国内三平台
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 15 --source cn_all

# 国外双平台（与历史 all 相同）
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 20 --source all

# 五源全量
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 15 --source global_all
```

## 数据落盘

Bridge 原始 JSONL 目录：

```text
data/raw/mediacrawler/{job_id}/{platform}/jsonl/search_comments_*.jsonl
```

解析后仍写入 SQLite 与 `data/results/` 分析报告。

## 故障排查

| 现象 | 处理 |
|------|------|
| `MediaCrawler 子模块未初始化` / 目录为空 | `git submodule update --init --recursive` 或 bootstrap 脚本 |
| `MediaCrawler 目录不存在` | 检查 `MEDIACRAWLER_HOME` 或确认 submodule 路径 |
| `uv sync` 失败 | 安装 [uv](https://docs.astral.sh/uv/)，手动 `cd vendor/MediaCrawler && uv sync` |
| 子进程 `login failed` | 重新扫码或配置 `MEDIACRAWLER_COOKIES_*` |
| 无 jsonl 输出 | 确认 `--get_comment` 已开启（Bridge 默认开启）；检查关键词是否有结果 |
| 微博频繁风控 | 降低 `--limit`、增大 `MEDIACRAWLER_MAX_SLEEP_SEC` |

## 架构简述

```text
pipeline → collect_with_raw（中文源 ThreadPoolExecutor 并行）
         → MediaCrawler*Crawler → ensure_mediacrawler_ready (submodule + uv sync)
         → MediaCrawlerRunner (subprocess)
         → scripts/run_mediacrawler.py → MediaCrawler main.py
         → JSONL → Parser → CommentRecord → 现有清洗/分析链路
```
