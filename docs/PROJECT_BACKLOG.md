# 美以伊战争多源网络评论分析 — 项目待办与模块清单

> 文档版本：2026-06-11（P0 已合并 main · PR #1；P1 双语分析已完成 · `feat/p1-bilingual-analysis`）  
> 策略调整：**先打通完整链路（落盘 → 存储 → 分析 → HTML）**，分析侧实现**中英文双语**（分词 + 词典 + 规则，**不调用大模型**）；**信息源扩展优先级下调**。

---

## 〇、当前迭代策略（必读）

| 维度 | 本阶段选择 | 说明 |
|------|------------|------|
| **主线** | 完整链路打通 | 一条命令：采集 → 清洗 → 落盘 → SQLite → 双语分析 → HTML 报告 |
| **存储** | **SQLite 为主** | 默认 `data/comment_analysis.db`；JSON/CSV 作为可选导出 |
| **分析** | **双语 · 无大模型** | 中文 jieba + 词典规则；英文 NLTK + VADER（规则/词典类） |
| **数据源** | **维持现有 2 源** | Hacker News + Stack Exchange 已可真实跑通，暂不扩第三源 |
| **暂缓** | 新平台、LLM API、云 NLP、复杂主题模型 | 链路稳定后再评估 |

---

## 一、项目整体目标与预期效果

### 1.1 核心目标

构建一条**可扩展、可复现**的网络评论分析流水线，围绕「美以伊战争」及相关议题，完成：

| 阶段 | 目标 |
|------|------|
| **采集** | 从已接入公开 API 获取评论（当前 2 个英文社区） |
| **标准化** | 异构原始数据 → `CommentRecord` |
| **清洗** | 去重、去噪、时间统一、文本修复 |
| **落盘** | 原始 JSON 快照 + SQLite 结构化存储 |
| **分析** | **中英文双语**关键词、情感、趋势、平台对比（规则化 NLP） |
| **展示** | 交互式 HTML 仪表盘 + 结构化 JSON 报告 |
| **运维** | 可配置、可重复跑批、任务可追溯 |

### 1.2 完整链路预期效果（V1 目标态）

```text
关键词 / 主题配置
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│  采集（现有双源：HN · Stack Exchange）                     │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│  原始落盘 data/raw/{platform}/{job_id}.json                │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│  解析 → 清洗 → CommentRecord                               │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│  SQLite（评论表 · 任务表 · 去重）+ 可选导出 JSON/CSV       │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│  双语分析（语言检测 → 中文/英文分词管线 → 词典情感）       │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│  data/results：分析 JSON + 交互式 HTML 仪表盘              │
└───────────────────────────────────────────────────────────┘
```

**V1 交付物：**

| 路径 | 内容 |
|------|------|
| `data/raw/` | 各平台原始 API 响应 JSON |
| `data/comment_analysis.db` | SQLite 主库（评论、采集任务、分析任务） |
| `data/processed/` | 可选单次导出快照（JSON/CSV） |
| `data/results/*_analysis_*.json` | 多维统计结果 |
| `data/results/*_dashboard.html` | ECharts 可筛选报告 |

**一条命令预期体验：**

```powershell
python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 20 --source all
# → 落盘 raw · 写入 SQLite · 双语分析 · 生成 HTML
```

---

## 二、双语分析技术方案（无大模型）

> **「NLP 处理」在本阶段指分词、停用词、词典与规则，不调用 LLM / BERT 等远程或大参数量模型。**

### 2.1 语言分流

| 步骤 | 方案 |
|------|------|
| 语言检测 | 轻量规则：CJK 字符占比 / `langdetect`（可选，非大模型） |
| 混合文本 | 分别走中文、英文管线，合并词项；或按主语言选一条管线 |

### 2.2 中文管线（规则化）

| 能力 | 技术选型 | 性质 |
|------|----------|------|
| 分词 | **jieba** | 分词库，本地、非 LLM |
| 停用词 | 项目内中文停用词表（可扩展） | 规则 |
| 关键词 | jieba 分词 + 词频 / 可选 TF 权重 | 统计 |
| 情感 | **扩展现有 `sentiment.py` 中文词典** + 否定词规则 | 词典 + 规则 |
| 不用 | SnowNLP、transformers、LLM API | 本阶段排除 |

### 2.3 英文管线（规则化）

| 能力 | 技术选型 | 性质 |
|------|----------|------|
| 分词 | **NLTK**：`word_tokenize`、停用词、可选词形还原 | 规则 + 小资源 |
| 关键词 | NLTK 分词 + 词频；可选 **YAKE**（算法，非神经网络） | 统计 / 算法 |
| 情感 | **VADER**（规则 + 社交文本词典）或扩展现有英文词典 | 词典 + 规则 |
| 不用 | spaCy `trf`、BERT、云 Comprehend、LLM | 本阶段排除 |

### 2.4 与历史实现的差异（P1 已达成 V1 目标）

| 项目 | P0 基线 | V1 现状（P1 后） |
|------|---------|------------------|
| 中文分词 | 正则抽连续汉字 | jieba + 停用词表 |
| 英文分词 | 正则抽单词 | NLTK + 停用词 + 词形归一 |
| 情感 | 中英混合小词典 + 简单否定 | 中文词典增强 + VADER（英） |
| 依赖 | sqlalchemy + dotenv | 另含 `jieba`、`nltk`、`vaderSentiment` |

### 2.5 建议新增模块

```text
src/comment_analysis/analysis/
├─ language.py      # 语言检测与分流
├─ tokenize_cn.py   # jieba 分词 + 中文停用词
├─ tokenize_en.py   # NLTK 英文分词
├─ keywords.py      # 统一入口，按语言调用子管线
├─ sentiment.py     # 中文词典 + VADER，统一 assign_sentiment
└─ report.py        # 保持不变，消费 enriched records
```

---

## 三、存储方案：SQLite 为主

### 3.1 选型说明

| 项 | 决定 |
|----|------|
| **主库** | **SQLite**（默认 `sqlite:///data/comment_analysis.db` 或 `DATABASE_URL`） |
| **访问层** | SQLAlchemy（或 sqlite3 + 轻量封装，二选一实现时定） |
| **JSON/CSV** | 保留为**导出/调试**，非主存储 |
| **PostgreSQL 等** | 后续通过同一 `DATABASE_URL` 扩展，非 V1 范围 |

### 3.2 建议表结构（示意）

| 表 | 用途 |
|----|------|
| `crawl_jobs` | 任务 ID、关键词、source、参数、开始/结束、条数、状态 |
| `comments` | `CommentRecord` 字段 + `job_id` + `unique(platform, comment_id)` 去重 |
| `analysis_jobs` | 分析任务 ID、关联 crawl_job 或时间范围、报告路径 |
| （可选）`raw_snapshots` | raw 文件路径与 job_id 关联 |

### 3.3 分析读数路径

- **目标**：`entry/analyze` 支持 `--from-db` / `--job-id`，从 SQLite 读取评论，而非仅依赖单个 JSON 文件。

---

## 四、当前已实现能力（基线）

### 4.1 采集（维持，不扩展）

| 数据源 | 方式 | 状态 |
|--------|------|------|
| Hacker News | Algolia API | ✅ 真实可跑 |
| Stack Exchange | 官方 API 2.3，`politics` | ✅ 真实可跑 |
| 采集入口 | `--source hackernews \| stackexchange \| all` | ✅ |

### 4.2 已实现

| 模块 | 状态 |
|------|------|
| `CommentRecord`、双源 Parser/Crawler | ✅ |
| 清洗（去重、乱码、时间统一） | ✅ |
| JSON / CSV 文件存储 | ✅ |
| 双语分词（jieba + NLTK）+ 情感（词典 + VADER） | ✅ |
| `build_analysis_report` + ECharts HTML | ✅ |
| `run_all`（采集+清洗+文件存储） | ✅ |
| `analyze`（读文件 → 分析 → HTML） | ✅ |
| `entry/pipeline`（一键全链路） | ✅ |
| SQLite Repository + `crawl_jobs` + 任务评论关联 | ✅ |
| `data/raw/` 落盘 | ✅ |
| `FullPipeline` 编排器 | ✅ |
| `analyze --from-db` / `--job-id` / `--last-job` | ✅ |
| `requirements.txt` + `python-dotenv` | ✅ |

### 4.3 未实现 / 未接入

| 模块 | 现状 |
|------|------|
| `analysis_jobs` 表（分析任务元数据） | ❌ P2 |
| 结构化全链路日志 | ❌ P2 |
| README 与本文档核心内容同步 | ✅ P1 命令、双语依赖、pipeline 主路径已同步（细节完善见 P2-5） |

---

## 五、当前欠缺功能（按新优先级归类）

### 5.1 P0 — 链路打通（✅ 已完成，2026-06-11 合并 main）

| 欠缺项 | 说明 | 状态 |
|--------|------|------|
| 一键全链路 | 采集 → raw → 清洗 → SQLite → 分析 → HTML | ✅ |
| SQLite 主存储 | 评论入库、去重、按任务查询 | ✅ |
| 原始数据落盘 | `data/raw/` 保存 API 响应，支持离线重跑解析 | ✅ |
| 编排统一 | `FullPipeline` 串联各阶段 | ✅ |
| 依赖与配置 | `requirements.txt` + `python-dotenv` | ✅ |

### 5.2 P1 — 双语规则化分析（✅ 已完成，2026-06-11）

| 欠缺项 | 说明 | 状态 |
|--------|------|------|
| 语言分流 | 中英混合评论走对应分词与情感管线 | ✅ |
| 中文 jieba | 替代正则抽汉字 | ✅ |
| 英文 NLTK + VADER | 替代纯正则 + 小词典 | ✅ |
| 分析读库 | 从 SQLite 拉取记录再分析（P0 已交付，P1 自动受益） | ✅ |
| 报告标注语言 | HTML/JSON 展示各语言占比；HTML 筛选联动 | ✅ |

### 5.3 P2 — 体验与工程加固

| 欠缺项 | 说明 |
|--------|------|
| 任务元数据 | crawl/analysis job 写入 DB |
| 日志 | 全链路 `get_logger` |
| 报告模板拆分 | `charts.py` 可维护性 |
| 联网冒烟测试 | 可选 `RUN_LIVE_TESTS=1` |
| README 与文档同步 | 与本文档一致（P1 核心已同步，P2 可继续细化） |

### 5.4 P3 — 延后（本阶段不做）

| 项 | 说明 |
|----|------|
| **第三数据源及中文社媒源** | Reddit、微博等 — **优先级已降低** |
| Stack Exchange API Key | 小规模测试可暂缓；跑批前再补 |
| HTTP 代理 / 限流 / 重试 | 链路稳定后加固 |
| SnowNLP / transformers / LLM | 明确不在本阶段 |
| 实体识别、LDA、云 NLP API | 进阶分析，V2+ |
| FastAPI Web 服务、定时调度 | 运维增强，V2+ |

---

## 六、待完成模块清单

### 6.1 P0 — 完整链路 + SQLite + 落盘（✅ 已完成）

| ID | 模块 | 待办内容 | 验收标准 | 状态 |
|----|------|----------|----------|------|
| P0-1 | **统一入口 `entry/pipeline.py`** | 一条命令跑完全链路；参数对齐现有 `run_all` + `analyze` | 终端输出 DB 路径、报告 JSON、HTML 路径 | ✅ |
| P0-2 | **SQLite Repository** | `SqliteCommentRepository`：表结构对齐 `CommentRecord`，`(platform, comment_id)` 去重插入 | 二次采集不重复入库；可 `SELECT` 按平台/时间 | ✅ |
| P0-3 | **任务表 `crawl_jobs`** | 每次采集写入 job 记录，评论带 `job_id` | 可追溯「哪次任务采了多少条」 | ✅ |
| P0-4 | **Raw 落盘** | `RawFileRepository`：`data/raw/{platform}/{job_id}.json` | 断网后可从 raw 重跑 parse/clean，无需再打 API | ✅ |
| P0-5 | **存储工厂** | `build_repository(backend="sqlite\|json\|csv")`；默认 sqlite | 配置切换后端，默认写 DB | ✅ |
| P0-6 | **编排器** | `FullPipeline`：crawl → raw → clean → save_db → analyze → html | 主入口只调编排器 | ✅ |
| P0-7 | **依赖与 `.env`** | `requirements.txt`：`sqlalchemy`、`python-dotenv` 等；启动加载 `.env` | `pip install -r requirements.txt` 后可跑 pipeline | ✅ |
| P0-8 | **分析接库** | `analyze` 支持 `--job-id` 或 `--from-db` 从 SQLite 读 | 不依赖手动找最新 JSON | ✅ |

### 6.2 P1 — 双语分析（分词 + 词典 + 规则，无大模型）（✅ 已完成）

| ID | 模块 | 待办内容 | 验收标准 | 状态 |
|----|------|----------|----------|------|
| P1-1 | **`analysis/language.py`** | 检测主语言或中英混合策略 | 英/中样本文本分流正确 | ✅ |
| P1-2 | **中文 `tokenize_cn.py`** | jieba 分词 + 中文停用词 | 中文评论关键词优于纯正则 | ✅ |
| P1-3 | **英文 `tokenize_en.py`** | NLTK 分词、停用词、可选 lemmatize | 英文热词 `war`/`wars` 可归一 | ✅ |
| P1-4 | **统一 `keywords.py`** | 按语言调用子管线，保留 `assign_keywords` 接口 | 现有测试可扩展双语用例 | ✅ |
| P1-5 | **情感 `sentiment.py`** | 中文：扩展词典+否定；英文：VADER；统一三分类标签 | 英/中 fixture 情感方向合理 | ✅ |
| P1-6 | **依赖** | `jieba`、`nltk`、`vaderSentiment`；NLTK 数据包文档化 | README 首次运行说明 | ✅ |
| P1-7 | **报告** | `report` / HTML 展示语言分布 | JSON 含全量 `language_distribution`；HTML 按 `currentRecords` 筛选联动 | ✅ |

### 6.3 P2 — 加固与文档

| ID | 模块 | 待办内容 | 验收标准 |
|----|------|----------|----------|
| P2-1 | **结构化日志** | crawl/clean/store/analyze 各阶段写 `logs/` | 单次 pipeline 一条日志文件 |
| P2-2 | **测试** | SQLite repo 测试、双语分词/情感测试、pipeline 集成测试（mock 采集） | unittest 全绿 |
| P2-3 | **联网冒烟** | `tests/test_live_pipeline.py`，`RUN_LIVE_TESTS=1` | 可选验证双源 API 仍可用 |
| P2-4 | **可视化** | 拆分 `charts.py` 模板；双语报告标题/说明 | 维护成本降低 |
| P2-5 | **README** | 与本文档、新命令、依赖安装一致 | 新人 30 分钟内跑通 pipeline |

### 6.4 P3 — 延后 backlog（不在当前迭代）

| ID | 模块 | 说明 |
|----|------|------|
| P3-1 | 第三数据源 | Reddit / GDELT / RSS 等 |
| P3-2 | 中文社媒源 | 微博、知乎等（合规与采集方式另议） |
| P3-3 | SE API Key | 日配额提升，跑批前实施 |
| P3-4 | HTTP 重试 / PROXY / 限流 | `utils/http.py` |
| P3-5 | 增量采集 | 按时间/ID 增量 |
| P3-6 | LLM / 云 NLP / 主题模型 | 摘要、细粒度立场、实体识别等 |
| P3-7 | FastAPI / 定时调度 / CI | 运维与产品化 |

---

## 七、模块与目录映射（V1 目标态）

```text
src/comment_analysis/
├─ config/           # settings + dotenv + DATABASE_URL 默认 SQLite 路径
├─ models/           # CommentRecord、CrawlJob、AnalysisJob
├─ crawlers/         # 现有 HN、SE（暂不新增源）
├─ parsers/          # 现有解析器
├─ entry/
│   ├─ crawl.py · clean.py · analyze.py
│   ├─ run_all.py    # 可保留为「仅采集+入库」快捷入口
│   └─ pipeline.py   # 【新增】全链路主入口
├─ pipeline/         # FullPipeline / Orchestrator
├─ storage/
│   ├─ repository.py   # Json / Csv / Memory（已有）
│   ├─ sqlite.py       # 【新增】SQLite + SQLAlchemy
│   └─ raw.py          # 【新增】raw JSON 落盘
├─ analysis/
│   ├─ language.py    # 【新增】
│   ├─ tokenize_cn.py # 【新增】
│   ├─ tokenize_en.py # 【新增】
│   ├─ keywords.py · sentiment.py · report.py
├─ visualization/    # charts.py → HTML
├─ utils/            # text · logger · （http 延后）
└─ tests/

data/
├─ comment_analysis.db   # SQLite 主库【新增默认】
├─ raw/                  # 原始 API JSON
├─ processed/            # 可选导出
├─ results/              # 分析 JSON + HTML
└─ logs/                 # 运行日志
```

---

## 八、建议实施路线图（修订）

| 阶段 | 周期（示意） | 目标 |
|------|--------------|------|
| **阶段 1** | ✅ 已完成 | **P0**：pipeline 一键跑通 + SQLite + raw 落盘 + analyze 读库 |
| **阶段 2** | ✅ 已完成 | **P1**：jieba + NLTK + VADER 双语管线接入报告与 HTML |
| **阶段 3** | 1 周 | **P2**：测试、日志、文档、HTML 小优化 |
| **阶段 4** | 按需 | **P3**：扩源、SE key、代理、LLM 等 — **仅链路稳定后** |

---

## 九、V1 完成判定标准（修订）

当以下检查项**全部满足**时，视为 V1 完整链路达成：

- [x] 一条命令：`pipeline` 完成采集 → raw 落盘 → 清洗 → **SQLite 入库** → **双语规则化分析** → **HTML 报告**
- [x] 现有 **HN + SE 双源** 可真实跑通（61 项 unittest + 联网冒烟）
- [x] 原始 JSON 可回溯，可离线重跑解析/清洗
- [x] 分析从 **SQLite 读数**，不强制依赖单个 JSON 文件
- [x] 关键词：**jieba（中）+ NLTK（英）**；情感：**词典规则（中）+ VADER（英）**
- [x] **未引入** LLM / transformers 推理
- [x] `requirements.txt` 与 `.env` 可用；README 已补充双语依赖与 pipeline 主路径
- [ ] （已移除）~~至少 3 个数据源~~ — V1 不要求扩源

---

## 十、参考命令

### 推荐（一步全链路，P0 主路径）

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"
pip install -r requirements.txt

python -m comment_analysis.entry.pipeline --keyword "美以伊战争" --limit 20 --source all

# 仅从库中最近一次任务再生成报告
python -m comment_analysis.entry.analyze --from-db --last-job --output-dir data\results
```

### 备选（分步，文件存储）

```powershell
cd D:\comment-analysis
$env:PYTHONPATH = "src"

python -m comment_analysis.entry.run_all --keyword "美以伊战争" --limit 5 --source all --output-dir data\processed

$latest = Get-ChildItem data\processed\comments_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
python -m comment_analysis.entry.analyze $latest --top-n 10 --output-dir data\results
```

### 双语分析依赖安装（P1 完成后示意）

```powershell
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## 十一、数据库与双语分析 FAQ（摘要）

| 问题 | 答案 |
|------|------|
| 数据库选型？ | V1 固定 **SQLite**；`DATABASE_URL` 预留换库 |
| JSON 还要吗？ | 作为**导出/调试**，主库为 SQLite |
| 英文数据用 jieba？ | **不用**；英文走 NLTK + VADER |
| 中文数据用 VADER？ | **不用**；中文走 jieba + 词典规则 |
| NLP = 调大模型？ | **本阶段否**；均为本地分词库与规则/词典类工具 |

---

*本文档随迭代更新；功能完成后请在对应条目标记 ✅ 并同步修改 README。*
