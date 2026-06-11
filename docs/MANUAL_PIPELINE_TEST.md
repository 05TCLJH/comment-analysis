# 手动完整链路测试与 HTML 预览指南

> 文档版本：2026-06-11  
> 适用分支：`main`（P0 全链路 + P1 双语分析已合并）  
> 环境：Windows PowerShell · Python 3.10+

本文说明如何在本机**手动跑通完整链路**（采集 → raw 落盘 → 清洗 → SQLite 入库 → 双语分析 → HTML 报告），并预览交互式仪表盘。

---

## 一、环境准备（首次做一次）

### 1. 进入项目目录

```powershell
cd D:\comment-analysis
```

### 2. 创建并激活虚拟环境（推荐）

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

若 PowerShell 禁止执行脚本，可先运行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3b. MediaCrawler 子模块（仅中文源需要）

```powershell
git submodule update --init --recursive
.\scripts\bootstrap_mediacrawler.ps1
cd vendor\MediaCrawler
uv run playwright install
```

Bridge 说明见 [MEDIACRAWLER_BRIDGE.md](./MEDIACRAWLER_BRIDGE.md)。国外 API 源可跳过本节。

### 4. 设置 Python 模块路径

**每个新开的终端都需要执行：**

```powershell
$env:PYTHONPATH = "src"
```

### 5. 复制环境配置

```powershell
copy .env.example .env
```

默认配置：

| 配置项 | 默认值 |
|--------|--------|
| `DATABASE_URL` | `sqlite:///data/comment_analysis.db` |
| `STORAGE_BACKEND` | `sqlite` |
| 报告输出目录 | `data/results`（由 settings 决定，可用 `--output-dir` 覆盖） |

### 6. 预热 NLTK 语料（首次必做）

英文分词与 VADER 情感依赖 NLTK 数据包。建议在跑 pipeline 前手动预热，避免首次分析中途长时间等待或超时：

```powershell
$env:PYTHONPATH = "src"
python -c "from comment_analysis.analysis.nltk_data import ensure_nltk_data; ensure_nltk_data(); print('NLTK ready')"
```

| 依赖 | 首次运行行为 |
|------|----------------|
| **jieba** | 首次分词时自动下载词典到用户缓存，无需额外命令 |
| **nltk** | 下载 `punkt_tab`、`stopwords`、`wordnet`、`omw-1.4` |
| **vaderSentiment** | 纯 Python 包，无额外数据文件 |

若 NLTK 下载超时，重试上述命令；离线环境需在有网机器预热后将 `nltk_data` 目录复制到本机。

### 7. 国内三平台登录凭证（贴吧 / 知乎 / 微博）

使用 `tieba`、`zhihu`、`weibo`、`cn_all` 或 `global_all` 时，MediaCrawler Bridge 需要各平台登录态。  
**推荐 Cookie 方式**（便于自动化冒烟、无需扫码）；也可改用二维码 + CDP，见 [MEDIACRAWLER_BRIDGE.md](./MEDIACRAWLER_BRIDGE.md)。

> **安全提示**：Cookie 等同账号密码。仅写入本地 `.env`（已在 `.gitignore` 中），**切勿**提交 Git、Issue 或聊天。

#### 7.1 环境变量说明

| 变量 | 说明 |
|------|------|
| `MEDIACRAWLER_LOGIN_TYPE` | 填 `cookie` 时使用下方 Cookie；填 `qrcode` 时走扫码（常配合 CDP） |
| `MEDIACRAWLER_COOKIES_TIEBA` | 百度贴吧 Cookie 字符串（一行） |
| `MEDIACRAWLER_COOKIES_ZHIHU` | 知乎 Cookie 字符串（一行） |
| `MEDIACRAWLER_COOKIES_WEIBO` | 微博 Cookie 字符串（一行） |
| `MEDIACRAWLER_ENABLE_CDP_MODE` | Cookie 模式建议 `false` |
| `MEDIACRAWLER_CDP_CONNECT_EXISTING` | Cookie 模式建议 `false` |

Bridge 按平台注入 Cookie：填写某平台变量后，子进程会自动将 `LOGIN_TYPE` 设为 `cookie`（见 `scripts/run_mediacrawler.py`）。

#### 7.2 从浏览器导出 Cookie

**方式 A：Netscape 格式文件（推荐）**

1. 使用浏览器扩展（如「Get cookies.txt LOCALLY」等）导出 **Netscape cookie 文件**。
2. 分别在**已登录**状态下访问并导出：
   - 贴吧：https://tieba.baidu.com
   - 知乎：https://www.zhihu.com
   - 微博：https://weibo.com（若失败可改 https://m.weibo.cn 再导出）

**方式 B：开发者工具手动复制**

1. `F12` → **Network（网络）** → 刷新页面。
2. 任选同域请求 → **Request Headers** → 复制 `Cookie:` 后的整段内容。
3. 写入 `.env` 对应变量（一行，不要换行、不要加引号）。

#### 7.3 各平台关键 Cookie 字段

MediaCrawler 用下列字段判断是否已登录（导出时尽量包含完整 Cookie 串）：

| 平台 | 关键字段 | 说明 |
|------|----------|------|
| **贴吧** | `BDUSS`、`STOKEN`（或 `PTOKEN`） | 需先登录百度账号并打开贴吧首页 |
| **知乎** | `z_c0`、`d_c0` | `z_c0` 为登录态；`d_c0` 用于搜索 API 签名 |
| **微博** | `SUB`、`SUBP` | 建议从已登录的 weibo.com / m.weibo.cn 导出 |

#### 7.4 写入 `.env`（一键导入脚本）

项目提供 [`scripts/import_cookies_to_env.py`](../scripts/import_cookies_to_env.py)，将 Netscape 文件转为 `.env` 中的 `MEDIACRAWLER_COOKIES_*`：

```powershell
cd D:\comment-analysis

# 贴吧 + 微博（必填路径按你本机下载位置修改）
python scripts\import_cookies_to_env.py `
  "C:\Users\你\Downloads\tieba.baidu.com_cookies.txt" `
  "C:\Users\你\Downloads\weibo.com_cookies.txt"

# 若已有知乎 cookie 文件，可追加第三个参数
python scripts\import_cookies_to_env.py `
  "C:\Users\你\Downloads\tieba.baidu.com_cookies.txt" `
  "C:\Users\你\Downloads\weibo.com_cookies.txt" `
  "C:\Users\你\Downloads\zhihu.com_cookies.txt"
```

脚本会写入/覆盖所有 `MEDIACRAWLER_*` 行，并设置：

```env
MEDIACRAWLER_LOGIN_TYPE=cookie
MEDIACRAWLER_ENABLE_CDP_MODE=false
MEDIACRAWLER_CDP_CONNECT_EXISTING=false
```

**手动配置示例**（在 `copy .env.example .env` 之后追加）：

```env
MEDIACRAWLER_LOGIN_TYPE=cookie
MEDIACRAWLER_ENABLE_CDP_MODE=false
MEDIACRAWLER_CDP_CONNECT_EXISTING=false
MEDIACRAWLER_MAX_SLEEP_SEC=3
MEDIACRAWLER_COOKIES_TIEBA=BAIDUID=...; BDUSS=...; STOKEN=...
MEDIACRAWLER_COOKIES_ZHIHU=d_c0=...; z_c0=...
MEDIACRAWLER_COOKIES_WEIBO=SUB=...; SUBP=...
```

#### 7.5 登录配置验收（单平台冒烟）

配置完成后，建议**分平台**小流量验证（每平台约数分钟）：

```powershell
$env:PYTHONPATH = "src"

python -m comment_analysis.entry.pipeline --keyword "测试" --limit 3 --source tieba
python -m comment_analysis.entry.pipeline --keyword "测试" --limit 3 --source zhihu
python -m comment_analysis.entry.pipeline --keyword "测试" --limit 3 --source weibo
```

**成功标志：**

- 终端输出 `全链路执行完成`，无 `login failed` / `MediaCrawler 子进程失败`
- 存在 `data\raw\mediacrawler\{job_id}\{平台}\...\search_comments_*.jsonl`
- `data\results\job_*_analysis_dashboard.html` 中对应平台有评论数据

三平台均通过后，再跑：

```powershell
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 10 --source cn_all
```

#### 7.6 登录相关故障排查

| 现象 | 处理 |
|------|------|
| `login failed` | Cookie 过期 → 重新登录网站并导出；确认关键字段存在 |
| 贴吧有 `BDUSS` 无 `STOKEN` | 打开 https://tieba.baidu.com 刷新后再导出 |
| 微博 Cookie 无效 | 改从 https://m.weibo.cn 导出；确认含 `SUB` |
| 知乎搜索/API 报错 | 确认含 `d_c0` 与 `z_c0`；重新导出完整 Cookie |
| 仍想用扫码 | `.env` 改 `MEDIACRAWLER_LOGIN_TYPE=qrcode`，CDP 见 [MEDIACRAWLER_BRIDGE.md](./MEDIACRAWLER_BRIDGE.md) |

Cookie 过期后，重新导出并再次运行 `import_cookies_to_env.py` 即可。

---

## 二、一条命令跑完整链路（推荐）

这是**手动完整链路测试**的主路径：

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 10 --source all
```

### 常用参数

| 参数 | 含义 | 示例 |
|------|------|------|
| `--keyword` | 搜索关键词 | `"Israel Iran war"` |
| `--limit` | 每源最多采集条数 | `5`（快速冒烟）/ `20`（常规） |
| `--source` | 数据源 | 见下方「数据源别名」 |
| `--top-n` | 报告全局热词数 | 默认 `20` |
| `--per-record-top-n` | 每条评论关键词数 | 默认 `5` |
| `--output-dir` | 报告输出目录 | 默认 `data\results` |

### 数据源别名

| `--source` | 包含平台 |
|------------|----------|
| `hackernews` / `stackexchange` | 单源（公开 API） |
| `tieba` / `zhihu` / `weibo` | 单源（MediaCrawler Bridge，默认 `vendor/MediaCrawler` 子模块） |
| **`cn_all`** | 贴吧 + 知乎 + 微博 |
| **`en_all`** / **`all`** | Hacker News + Stack Exchange（**默认 `all` 仍为国外双源**） |
| **`global_all`** | 上述六源 |

Bridge 详细说明见 [MEDIACRAWLER_BRIDGE.md](./MEDIACRAWLER_BRIDGE.md)。

### 快速冒烟（单源、少量数据）

```powershell
python -m comment_analysis.entry.pipeline --keyword "Israel Iran" --limit 5 --source hackernews
```

### 完整国外双源测试（与历史 `all` 相同）

```powershell
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 20 --source all
```

### 国内三平台（需子模块 + 登录凭证）

先完成上文 **§7 国内三平台登录凭证**，再执行：

```powershell
git submodule update --init --recursive
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 10 --source cn_all
```

首次跑中文源会自动 `uv sync`；Playwright 安装见 §3b。

### 六源全量

```powershell
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 15 --source global_all
```

---

## 三、终端成功输出示例

执行成功后，终端大致会输出：

```text
全链路执行完成
任务 ID：20260611_133830_e9614c99
数据库：sqlite:///D:/comment-analysis/data/comment_analysis.db
采集/清洗：10 / 10
新入库：8
JSON 报告：D:\comment-analysis\data\results\job_20260611_133830_e9614c99_analysis.json
HTML 仪表盘：D:\comment-analysis\data\results\job_20260611_133830_e9614c99_analysis_dashboard.html
```

请记下 **HTML 仪表盘** 的完整路径，用于后续预览。

---

## 四、各阶段落盘位置

| 阶段 | 路径 | 说明 |
|------|------|------|
| 原始 API 响应 | `data\raw\hackernews\{job_id}.json` | 支持离线重跑解析 |
| 原始 API 响应 | `data\raw\stackexchange\{job_id}.json` | `--source all` 时生成 |
| MediaCrawler JSONL | `data\raw\mediacrawler\{job_id}\{平台}\...\*.jsonl` | 中文三平台 Bridge 原始输出 |
| SQLite 主库 | `data\comment_analysis.db` | 评论 + `crawl_jobs` 任务元数据 |
| 分析 JSON | `data\results\job_{job_id}_analysis.json` | 含双语统计与 `language_distribution` |
| HTML 仪表盘 | `data\results\job_{job_id}_analysis_dashboard.html` | 交互式 ECharts 报告 |

> `data/` 下运行时产物已在 `.gitignore` 中，不会提交到 Git。

---

## 五、查看 HTML 预览

### 方法 1：资源管理器（最简单）

1. 打开 `D:\comment-analysis\data\results\`
2. 找到最新的 `*_dashboard.html`（按修改时间排序）
3. 双击用 Chrome / Edge 打开

### 方法 2：PowerShell 打开指定文件

将路径替换为终端实际输出的路径：

```powershell
Start-Process "D:\comment-analysis\data\results\job_20260611_133830_e9614c99_analysis_dashboard.html"
```

### 方法 3：自动打开最新 HTML

```powershell
$html = Get-ChildItem data\results\*_dashboard.html | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Start-Process $html.FullName
```

### 方法 4：在 Cursor / VS Code 中打开

在编辑器中打开 HTML 文件，使用「在默认浏览器中打开」或 Live Preview 扩展预览。

---

## 六、HTML 验收清单

打开仪表盘后，可逐项确认：

- [ ] **统计卡片**：总评论数、平台数、关键词种类、语言种类
- [ ] **情感分布** / **平台分布** / **语言分布** 饼图
- [ ] **时间趋势**、**热词榜**
- [ ] **平台 × 情感**、**每日情感趋势**
- [ ] **筛选器**：修改平台、日期、关键词、情感后，各图表（含语言图）联动更新
- [ ] **评论明细表**：平台、情感、关键词、内容摘要

打开同目录下的 `*_analysis.json`，确认包含：

- `"analysis_engine": "bilingual-rules-v1"`
- `"language_distribution": [...]`
- 每条 `records[]` 含 `"detected_language"`

---

## 七、不重新采集，仅重跑分析（可选）

若数据库中已有评论，只需重新生成报告：

```powershell
$env:PYTHONPATH = "src"
python -m comment_analysis.entry.analyze --from-db --last-job --output-dir data\results
```

基于**最近一次 crawl job** 生成带时间戳的新 JSON + HTML，无需再打采集 API。

指定某次任务：

```powershell
python -m comment_analysis.entry.analyze --from-db --job-id 20260611_133830_e9614c99 --output-dir data\results
```

---

## 八、推荐的一次性完整测试脚本

将以下命令依次执行，即可完成「预热 → 全链路 → 打开 HTML」：

```powershell
cd D:\comment-analysis
.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"

python -c "from comment_analysis.analysis.nltk_data import ensure_nltk_data; ensure_nltk_data(); print('NLTK ready')"

python -m comment_analysis.entry.pipeline --keyword "Israel Iran war" --limit 10 --source all

$html = Get-ChildItem data\results\*_dashboard.html | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Start-Process $html.FullName
```

---

## 九、常见问题

| 现象 | 处理 |
|------|------|
| `ModuleNotFoundError: comment_analysis` | 确认已执行 `$env:PYTHONPATH = "src"` |
| NLTK 下载超时或长时间无响应 | 单独运行第六节预热命令；检查网络 |
| 采集 0 条 | 尝试英文关键词如 `"Israel Iran war"`；确认可访问 HN / Stack Exchange API |
| 找不到 HTML | 查看终端 `HTML 仪表盘` 行；或运行「自动打开最新 HTML」命令 |
| 每次 pipeline 的 `job_id` 不同 | 正常，每次运行都会新建 crawl 任务 |
| 第二次采集同条评论未入库 | 正常，SQLite 按 `(platform, comment_id)` 去重 |
| 测试运行很慢（数分钟） | 首次 jieba / NLTK 加载较慢，后续会快一些 |
| 中文源 `login failed` | 见 **§7.6 登录相关故障排查**；更新 Cookie 后重试 |
| `MediaCrawler 子模块未初始化` | `git submodule update --init --recursive` |

---

## 十、相关文档

- [MEDIACRAWLER_BRIDGE.md](./MEDIACRAWLER_BRIDGE.md) — MediaCrawler Bridge 与子模块说明
- [PROJECT_BACKLOG.md](./PROJECT_BACKLOG.md) — 功能清单与 V1 验收标准
- [README.md](../README.md) — 项目概览与快速命令
- [superpowers/plans/2026-06-11-p1-bilingual-analysis.md](./superpowers/plans/2026-06-11-p1-bilingual-analysis.md) — P1 实施计划

---

*本文档随 pipeline / CLI 变更更新；若命令或路径有调整，请同步修改本节与 README。*
