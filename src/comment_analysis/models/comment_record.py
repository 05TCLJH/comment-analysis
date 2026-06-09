"""数据模型模块：描述单条评论记录的字段规范与后续扩展位置。"""

from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field , asdict
from typing import Any

import dataclasses


@dataclasses(slots=True)
class CommentRecord:
    """
    单条评论的标准数据结构
    """

    # 基础标识字段：用于区分数据来自哪个平台，以及从哪里抓到的
    platform: str
    content: str
    source_url: str
    crawl_time: datetime

    # 评论内容的补充信息：有的平台有标题，有的平台没有，所以设为可选
    title: str | None = None

    # 作者信息：不同平台字段名可能不同，统一收敛到这里
    author: str | None = None
    author_id: str | None = None

    # 时间信息：抓取时间一定有，发布时间尽量保留
    publish_time: datetime | None = None

    # 互动信息：有些平台会有点赞、回复数，没有就先留空
    like_count: int | None = None
    reply_count: int | None = None

    # 分析结果字段：后续情感分析、关键词提取时再回填
    sentiment_label: str | None = None
    keywords: list[str] = field(default_factory=list)

    # 原始数据备份：保留爬虫抓回来的原始结构，方便后面排查问题
    raw_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """把对象转换成字典，方便后续存储到 CSV、JSON 或数据库。"""
        data = asdict(self)

        # 时间字段转成字符串，避免直接存储 datetime 时报错
        data["crawl_time"] = self.crawl_time.isoformat()
        if self.publish_time is not None:
            data["publish_time"] = self.publish_time.isoformat()

        return data
