"""测试推送模块的消息格式化。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pulse.delivery.notifier import _format_card, _format_dingtalk


def test_card_structure():
    blocks = ["**1. Paper Title**\n\nsummary content here"]
    card = _format_card(blocks)

    assert card["msg_type"] == "interactive"
    assert "card" in card
    assert card["card"]["header"]["title"]["content"] == "PULSE 每日论文速递"
    assert card["card"]["header"]["template"] == "blue"
    assert card["card"]["config"]["wide_screen_mode"] is True

    elements = card["card"]["elements"]
    assert len(elements) >= 3  # 1 markdown + 1 hr + 1 note
    assert elements[0]["tag"] == "markdown"
    assert "Paper Title" in elements[0]["content"]
    assert elements[-1]["tag"] == "note"


def test_card_multiple_blocks():
    blocks = ["**1. Paper A**\n\nsummary A", "**2. Paper B**\n\nsummary B"]
    card = _format_card(blocks)

    elements = card["card"]["elements"]
    # markdown, hr, markdown, hr, note = 5 elements
    assert len(elements) == 5
    assert elements[0]["tag"] == "markdown"
    assert elements[1]["tag"] == "hr"
    assert elements[2]["tag"] == "markdown"


def test_dingtalk_format():
    blocks = ["**1. Test**\n\ncontent"]
    msg = _format_dingtalk(blocks)

    assert msg["msgtype"] == "markdown"
    assert "PULSE 每日论文速递" in msg["markdown"]["text"]
    assert "**1. Test**" in msg["markdown"]["text"]
