"""ArXiv 论文数据拉取与解析。"""
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

from config import settings
from pulse.models import Paper
from pulse.storage.db import is_paper_processed

logger = logging.getLogger(__name__)

_ARXIV_API = "http://export.arxiv.org/api/query"
_NAMESPACE = "{http://www.w3.org/2005/Atom}"


def _build_url() -> str:
    """构造 ArXiv API 查询 URL。"""
    cats = "+OR+".join(f"cat:{c}" for c in settings.ARXIV_CATEGORIES)
    max_fetch = min(settings.MAX_PAPERS * 4, 50)
    return (
        f"{_ARXIV_API}?search_query={cats}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_fetch}"
    )


def _matches_keywords(text: str) -> bool:
    """关键词过滤：标题或摘要包含任一关键词即通过。空关键词列表则全通过。"""
    if not settings.KEYWORDS:
        return True
    lower = text.lower()
    return any(kw.lower() in lower for kw in settings.KEYWORDS)


def _parse_entry(entry: ET.Element) -> Paper:
    """从单个 ATOM entry 中提取 Paper 字段。"""
    def _text(tag: str) -> str:
        el = entry.find(f"{_NAMESPACE}{tag}")
        return el.text.strip() if el is not None and el.text else ""

    def _all_text(tag: str) -> list[str]:
        return [el.text.strip() for el in entry.findall(f"{_NAMESPACE}{tag}")
                if el is not None and el.text]

    raw_id = _text("id")  # e.g. http://arxiv.org/abs/2301.00001v2
    arxiv_id = raw_id.rstrip("/").rsplit("/", 1)[-1]  # "2301.00001v2"
    # Strip version suffix if present
    arxiv_id = re.sub(r"v\d+$", "", arxiv_id)  # "2301.00001"

    return Paper(
        arxiv_id=arxiv_id,
        title=_text("title").replace("\n", " ").strip(),
        abstract=_text("summary").replace("\n", " ").strip(),
        arxiv_url=f"https://arxiv.org/abs/{arxiv_id}",
        published_date=_text("published"),
        authors=_all_text("author/{http://www.w3.org/2005/Atom}name"),
    )


def fetch() -> list[Paper]:
    """从 ArXiv 拉取最新论文，经关键词过滤和去重后返回。"""
    url = _build_url()
    logger.info("Fetching ArXiv papers: %s", url)

    # 1. HTTP 请求（含重试）
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            break
        except requests.RequestException as e:
            logger.warning("ArXiv API attempt %d failed: %s", attempt + 1, e)
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                logger.error("ArXiv API unreachable after 3 attempts")
                return []

    # 2. 解析 XML
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as e:
        logger.error("Failed to parse ArXiv XML: %s", e)
        return []

    entries = root.findall(f"{_NAMESPACE}entry")
    logger.info("ArXiv returned %d papers (before filtering)", len(entries))

    # 3. 过滤 & 去重
    papers: list[Paper] = []
    for entry in entries:
        paper = _parse_entry(entry)
        if not _matches_keywords(f"{paper.title} {paper.abstract}"):
            continue
        if is_paper_processed(paper.arxiv_id):
            continue
        papers.append(paper)
        if len(papers) >= settings.MAX_PAPERS:
            break

    logger.info("After filter/dedup: %d new papers to process", len(papers))
    return papers
