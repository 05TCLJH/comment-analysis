# 美以伊战争多源网络评论分析

一个用于采集、清洗、存储和分析网络评论的 Python 项目。  
当前项目已经具备一条最小可运行链路：

- 单一数据源评论采集
- 原始数据解析为统一结构
- 基础清洗规则处理
- 本地 `JSON` / `CSV` 存储
- 关键词统计分析

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

### 5. 基础分析功能

当前优先实现了关键词统计，支持：

- 每条评论关键词提取
- 全量评论高频词统计
- 输出关键词统计结果到 `JSON`

对应模块：

- `src/comment_analysis/analysis/keywords.py`
- `src/comment_analysis/entry/analyze.py`

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

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

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

## 使用方式

### 1. 运行采集、清洗、存储最小流程

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
python -m unittest tests.test_storage_local tests.test_run_all tests.test_clean_rules tests.test_hackernews_parser tests.test_hackernews_crawler tests.test_comment_record tests.test_keywords_analysis tests.test_analyze_entry
```

## 当前输出目录说明

- `data/processed/`：清洗后的评论数据
- `data/results/`：分析结果文件

这两个目录已加入 `.gitignore`，默认不会提交到仓库。

## 后续可继续扩展的方向

- 接入第二个真实数据源
- 补基础情感分析
- 增加图表输出
- 增加数据库存储
- 完善可视化结果展示
