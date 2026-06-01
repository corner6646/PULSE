"""消息推送：飞书交互式卡片 + 钉钉 Markdown。"""
import json
import logging
from datetime import date

import requests

from config import settings

logger = logging.getLogger(__name__)


def _post(webhook: str, payload: dict) -> bool:
    """发送 POST 请求到 Webhook，成功返回 True。"""
    try:
        resp = requests.post(webhook, json=payload, timeout=15)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code", -1) != 0:
            logger.error("Webhook rejected: %s", body)
            return False
        return True
    except requests.RequestException as e:
        logger.error("Webhook POST failed: %s", e)
        return False


def _format_card(content_blocks: list[str]) -> dict:
    """将多篇论文摘要拼接为一张飞书交互式卡片。"""
    elements: list[dict] = []
    for block in content_blocks:
        if elements:
            elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": block})

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": "PULSE · 全自动论文追踪 · " + str(date.today())}],
    })

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "PULSE 每日论文速递"},
                "template": "blue",
            },
            "elements": elements,
        },
    }


def _format_dingtalk(content_blocks: list[str]) -> dict:
    """将多篇论文摘要拼接为钉钉 Markdown 消息。"""
    text = "## PULSE 每日论文速递\n\n" + "\n\n---\n\n".join(content_blocks)
    return {"msgtype": "markdown", "markdown": {"title": "PULSE 论文速递", "text": text}}


def send_papers(results: list[tuple]) -> None:
    """将 (Paper, summary) 列表格式化并推送至配置的渠道。

    Args:
        results: List of (Paper, summary_string) tuples.
    """
    if not results:
        logger.info("No papers to send, skipping push")
        return

    blocks = []
    for i, (paper, summary) in enumerate(results, 1):
        # 提取摘要中已生成的内容直接使用
        block = f"**{i}. {paper.title}**\n\n{summary}"
        blocks.append(block)

    # 飞书
    if settings.FEISHU_WEBHOOK_URL:
        payload = _format_card(blocks)
        ok = _post(settings.FEISHU_WEBHOOK_URL, payload)
        logger.info("Feishu push %s", "OK" if ok else "FAILED")

    # 钉钉（可选）
    if settings.DINGTALK_WEBHOOK_URL:
        payload = _format_dingtalk(blocks)
        ok = _post(settings.DINGTALK_WEBHOOK_URL, payload)
        logger.info("DingTalk push %s", "OK" if ok else "FAILED")
