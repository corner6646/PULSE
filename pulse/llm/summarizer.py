"""大模型摘要生成：调用阿里云百炼 Qwen-Plus 提炼论文核心创新点。"""
import logging

import dashscope
from dashscope import Generation

from config import settings
from pulse.models import Paper
from pulse.storage import db

logger = logging.getLogger(__name__)

dashscope.api_key = settings.DASHSCOPE_API_KEY

SYSTEM_PROMPT = """你是一位资深的 AI 研究助理，擅长快速提炼学术论文的核心价值。你的输出将直接推送到团队协作群，要求内容精准、简洁、可读性强。"""

USER_PROMPT_TEMPLATE = """请阅读以下学术论文的标题和摘要，用中文提炼出核心信息。

【论文标题】
{title}

【论文摘要】
{abstract}

请严格按以下格式输出：

【一句话核心创新点】
用一句话概括这篇论文最核心的创新之处。

【3个关键突破点】
1. 第一点
2. 第二点
3. 第三点

【原文链接】
{arxiv_url}
"""


def _call_qwen(prompt: str) -> str | None:
    """调用 Qwen-Plus API，成功返回文本，失败返回 None。"""
    try:
        resp = Generation.call(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            result_format="message",
        )
        if resp.status_code == 200:
            return resp.output.choices[0].message.content
        logger.error("Qwen API error [%s]: %s", resp.status_code, resp.message)
        return None
    except Exception as e:
        logger.error("Qwen API call failed: %s", e)
        return None


def summarize(paper: Paper) -> str | None:
    """为单篇论文生成中文摘要（含缓存逻辑）。

    Returns:
        str on success, None on failure.
    """
    # 1. 查缓存
    cached = db.get_cached_summary(paper.arxiv_id)
    if cached is not None:
        logger.info("Cache hit: %s", paper.arxiv_id)
        return cached

    # 2. 构造 prompt
    prompt = USER_PROMPT_TEMPLATE.format(
        title=paper.title,
        abstract=paper.abstract,
        arxiv_url=paper.arxiv_url,
    )

    # 3. 调用 LLM
    logger.info("Calling Qwen-Plus for: %s", paper.arxiv_id)
    result = _call_qwen(prompt)
    if result is None:
        return None

    # 4. 写缓存
    db.cache_summary(paper.arxiv_id, result)
    return result


def batch_summarize(papers: list[Paper]) -> list[tuple[Paper, str]]:
    """批量处理论文摘要，单篇失败不影响其他。

    Returns:
        List of (Paper, summary) for successfully processed papers.
    """
    results: list[tuple[Paper, str]] = []
    for i, paper in enumerate(papers, 1):
        logger.info("[%d/%d] Processing: %s", i, len(papers), paper.title[:60])
        summary = summarize(paper)
        if summary is not None:
            results.append((paper, summary))
        else:
            logger.warning("Skipped (LLM failed): %s", paper.arxiv_id)
    return results
