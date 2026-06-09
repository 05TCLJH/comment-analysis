# 美以伊战争多源网络评论分析

一个用于抓取、清洗、存储、分析和可视化多源网络评论的 Python 项目。  
当前仓库还处于基础架构整理阶段，后续会逐步补齐各平台采集、数据处理和结果展示能力。

## 项目目标

- 统一管理多平台评论采集入口
- 建立评论清洗、去重、标准化流程
- 预留情感分析、关键词提取、主题分析等能力
- 支持将结果落地保存并进行可视化展示
- 方便多人协作持续完善

## 目录结构

- `src/comment_analysis/analysis/`：情感分析、关键词分析等逻辑
- `src/comment_analysis/crawlers/`：各平台爬虫适配器
- `src/comment_analysis/parsers/`：网页内容解析逻辑
- `src/comment_analysis/pipeline/`：数据流编排与任务组织
- `src/comment_analysis/storage/`：数据存储与持久化
- `src/comment_analysis/visualization/`：图表与结果展示
- `src/comment_analysis/entry/`：各阶段入口脚本
- `src/comment_analysis/utils/`：通用工具函数
- `src/comment_analysis/config/`：配置与路径管理
- `src/comment_analysis/models/`：数据模型定义

## 本地环境

建议使用 Python 3.10 或更高版本。

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> 提示：`requirements.txt` 里目前保留了一些注释形式的依赖清单，后续可以根据实际实现逐步取消注释和补全版本号。

## 配置说明

- `.env.example` 用于提供环境变量示例
- `data/` 用于保存原始数据、处理中间数据和分析结果
- `logs/` 用于保存运行日志

## 协作方式

如果你和朋友一起开发，建议按下面的方式进行：

1. 先在 `main` 上保持稳定
2. 每个人从 `main` 拉出自己的功能分支，例如 `feature/crawl-tiktok`
3. 单独完成一个功能后提交并推送分支
4. 在 GitHub 上发起 Pull Request，互相检查后再合并

这样可以尽量避免多人同时改同一份代码带来的冲突。

## 后续计划

- 先确认第一个爬虫数据源
- 统一评论字段结构
- 把“采集入口”和“分析入口”拆开
- 逐步补齐清洗、分析和展示模块

