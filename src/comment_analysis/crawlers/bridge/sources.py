"""数据源别名解析。"""

from __future__ import annotations

SOURCE_ALIASES: dict[str, list[str]] = {
    "all": ["hackernews", "stackexchange"],
    "en_all": ["hackernews", "stackexchange"],
    "cn_all": ["tieba", "zhihu", "weibo"],
    "global_all": [
        "hackernews",
        "stackexchange",
        "tieba",
        "zhihu",
        "weibo",
    ],
}

SINGLE_SOURCES = frozenset(
    {
        "hackernews",
        "stackexchange",
        "tieba",
        "zhihu",
        "weibo",
    }
)

CN_PLATFORMS = frozenset({"tieba", "zhihu", "weibo"})


def resolve_platforms(source: str) -> list[str]:
    """把 --source 别名展开为平台列表。"""
    normalized = source.strip().lower()
    if normalized in SOURCE_ALIASES:
        return list(SOURCE_ALIASES[normalized])
    if normalized in SINGLE_SOURCES:
        return [normalized]
    supported = sorted(SINGLE_SOURCES | set(SOURCE_ALIASES))
    raise ValueError(f"不支持的数据源：{source}。可选：{', '.join(supported)}")


def uses_english_search_query(platforms: list[str]) -> bool:
    """是否至少包含一个需要英译查询的英文源。"""
    return any(platform in {"hackernews", "stackexchange"} for platform in platforms)
