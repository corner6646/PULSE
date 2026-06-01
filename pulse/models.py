"""共享数据模型，供所有模块 import。"""
from dataclasses import dataclass, field


@dataclass
class Paper:
    arxiv_id: str
    title: str
    abstract: str
    arxiv_url: str
    published_date: str
    authors: list[str] = field(default_factory=list)
