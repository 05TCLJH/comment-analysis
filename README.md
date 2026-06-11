# 美以伊战争多源网络评论分析

一个用于采集、清洗、存储和分析网络评论的 Python 项目。  
当前已具备**完整可运行链路**（P0 + P1）：

- Hacker News + Stack Exchange 双源采集
- **MediaCrawler Bridge**：贴吧、知乎、微博（关键词搜索 + 评论，见 [docs/MEDIACRAWLER_BRIDGE.md](docs/MEDIACRAWLER_BRIDGE.md)）
- 原始 API 响应落盘（`data/raw/`）
- 清洗、去重与统一 `CommentRecord` 模型
- **SQLite 主存储**（默认 `data/comment_analysis.db`）
- **双语规则化分析**（中文 jieba + 词典；英文 NLTK + VADER，无大模型）
- 交互式 HTML 仪表盘 + JSON 分析报告

## 当前已实现功能

### 1. 最小真实爬虫

当前接入了一个真实数据源：

- `Hacker News` 公开评论搜索接口

对应模块：

- `src/comment_analysis/crawlers/sources/hackernews.py`
- `src/comment_analysis/parsers/hackernews.py`

### 2. 统一评论数据结构

项目内统一使用 `CommentRecord` 作为评论标准模型，字段包括：

- 平台
- 评论内容
- 来源链接
- 抓取时间
- 标题
- 作者
- 评论编号
- 发布时间
- 点赞数
- 回复数
- 关键词
- 原始数据

对应模块：

- `src/comment_analysis/models/comment_record.py`

### 3. 基础清洗规则

当前已实现这些清洗逻辑：

- 去重
- 去空值
- 时间格式统一
- 乱码修复
- 无效字符过滤
- 空白标准化

对应模块：

- `src/comment_analysis/entry/clean.py`
- `src/comment_analysis/utils/text.py`

### 4. 本地存储

清洗后的评论结果支持保存为：

- `JSON`
- `CSV`

对应模块：

- `src/comment_analysis/storage/repository.py`

### 5. 双语分析功能

分析模块按语言自动分流，**不调用大模型**：

| 语言 | 分词 | 情感 |
|------|------|------|
| 中文 | jieba + 停用词表 | 词典 + 否定词规则 |
| 英文 | NLTK + 词形归一 | VADER |

支持能力：

- 每条评论关键词提取与情感三分类（积极 / 中性 / 消极）
- 全量高频词、平台/情感/语言分布、时间趋势
- JSON 报告含 `language_distribution`；HTML 仪表盘可筛选联动

对应模块：

- `src/comment_analysis/analysis/language.py`
- `src/comment_analysis/analysis/tokenize_cn.py`
- `src/comment_analysis/analysis/tokenize_en.py`
- `src/comment_analysis/analysis/keywords.py`
- `src/comment_analysis/analysis/sentiment.py`
- `src/comment_analysis/analysis/report.py`
- `src/comment_analysis/entry/analyze.py`
- `src/comment_analysis/entry/pipeline.py`

## 项目目录

```text
src/comment_analysis/
├─ analysis/        # 分析模块
├─ config/          # 配置模块
├─ crawlers/        # 采集模块
├─ entry/           # 入口脚本
├─ models/          # 数据模型
├─ parsers/         # 解析模块
├─ pipeline/        # 流程编排
├─ storage/         # 存储模块
├─ utils/           # 通用工具
└─ visualization/   # 可视化模块
```

## 本地环境

建议使用 Python 3.10 及以上版本。

### 克隆仓库（含 MediaCrawler 子模块）

使用贴吧 / 知乎 / 微博等中文源时，需拉取 `vendor/MediaCrawler` 子模块：

```powershell
git clone --recurse-submodules https://github.com/<your-org>/comment-analysis.git
cd comment-analysis
```

若已 clone 主仓但 `vendor/MediaCrawler` 为空：

```powershell
git submodule update --init --recursive
```

也可运行 `scripts/bootstrap_mediacrawler.ps1`（Windows）或 `scripts/bootstrap_mediacrawler.sh`（Linux/macOS）完成子模块 init 与 `uv sync`。

**仅使用 Hacker News / Stack Exchange 时**，普通 `git clone` 即可，无需子模块。

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 双语分析依赖（首次运行必做）

安装 Python 包后，**首次运行前**需预热 NLTK 语料（英文分词与 VADER 依赖）。项目会在运行时自动调用 `ensure_nltk_data()`，也可手动执行：

```powershell
$env:PYTHONPATH = "src"
python -c "from comment_analysis.analysis.nltk_data import ensure_nltk_data; ensure_nltk_data(); print('NLTK ready')"
```

说明：

| 依赖 | 首次运行行为 |
|------|----------------|
| **jieba** | 首次分词时自动下载词典到用户缓存目录，无需额外命令 |
| **nltk** | 需下载 `punkt_tab`、`stopwords`、`wordnet`、`omw-1.4`（上式命令或 pipeline 首次分析时自动完成） |
| **vaderSentiment** | 纯 Python 包，无额外数据文件 |

若 NLTK 下载超时，可重试上述命令，或配置 pip/网络镜像后再次执行。离线环境需提前在有网机器执行一次，将 `nltk_data` 目录复制到本机。

运行模块命令前，建议先设置源码路径：

```powershell
$env:PYTHONPATH = "src"
```

## 配置说明

环境变量示例在 `.env.example` 中，当前可用配置包括：

- `USER_AGENT`
- `PROXY`
- `DATABASE_URL`
- `LOG_LEVEL`
- `MEDIACRAWLER_HOME` 等 Bridge 配置（默认 `vendor/MediaCrawler` 子模块，见 `.env.example` 与 [docs/MEDIACRAWLER_BRIDGE.md](docs/MEDIACRAWLER_BRIDGE.md)）

## 使用方式

### 0. 推荐：一条命令跑完全链路

```powershell
copy .env.example .env
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 20 --source all
```

执行后终端会输出：任务 ID、SQLite 路径、JSON 报告、HTML 仪表盘路径。

仅从数据库对最近一次采集任务重新生成报告：

```powershell
python -m comment_analysis.entry.analyze --from-db --last-job --output-dir data\results
```

### 1. 运行采集、清洗、存储最小流程（分步 / 文件存储）

保存为 `JSON`：

```powershell
python -m comment_analysis.entry.run_all --keyword 美以伊战争 --limit 5 --output-format json --output-dir data\processed
```

保存为 `CSV`：

```powershell
python -m comment_analysis.entry.run_all --keyword 美以伊战争 --limit 5 --output-format csv --output-dir data\processed
```

运行完成后，结果会写到：

- `data/processed/`

### 2. 对本地结果做关键词统计

直接分析指定文件：

```powershell
python -m comment_analysis.entry.analyze data\processed\comments_20260609_221420.json --top-n 10 --per-record-top-n 3 --output-dir data\results
```

如果你不想手动输入文件名，可以先取最新文件：

```powershell
$latest = Get-ChildItem data\processed\comments_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
python -m comment_analysis.entry.analyze $latest --top-n 10 --per-record-top-n 3 --output-dir data\results
```

分析结果会写到：

- `data/results/`

## 当前测试

当前已经包含这些测试方向：

- 数据模型测试
- 解析器测试
- 真实爬虫测试
- 清洗规则测试
- 本地存储测试
- 总入口测试
- 关键词分析测试
- 分析入口测试

运行全部测试：

```powershell
python -m unittest discover -s tests -v
```

## 当前输出目录说明

- `data/comment_analysis.db`：SQLite 主库（评论 + 采集任务）
- `data/raw/`：各平台原始 API JSON
- `data/processed/`：可选 JSON/CSV 导出
- `data/results/`：分析 JSON + HTML 仪表盘

`data/` 下运行时产物已加入 `.gitignore`，默认不提交到仓库。

## 结果展示

运行 `pipeline` 或 `analyze` 后，除 JSON 报告外会生成 HTML 仪表盘，包含：

- 评论总数、平台数、关键词种类、语言种类等概览
- 情感 / 平台 / **语言**分布（筛选后图表联动更新）
- 时间趋势、热词榜、平台×情感交叉统计
- 可筛选评论明细表

## 数据源

### 单源

- `hackernews` / `stackexchange`：公开 API
- `tieba` / `zhihu` / `weibo`：MediaCrawler Bridge（默认 `vendor/MediaCrawler` 子模块 + Chrome 登录）

### 组合别名

| `--source` | 平台 |
|------------|------|
| `cn_all` | 贴吧 + 知乎 + 微博 |
| `en_all` / `all` | Hacker News + Stack Exchange（**默认 `all` 仍为国外双源**） |
| `global_all` | 上述五源（2 国外 + 3 国内） |

```powershell
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 10 --source cn_all
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 20 --source global_all
```

Bridge 详细说明：[docs/MEDIACRAWLER_BRIDGE.md](docs/MEDIACRAWLER_BRIDGE.md)
