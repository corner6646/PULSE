"""测试 LLM 摘要模块（Prompt 模板 + 缓存逻辑，不调真实 API）。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pulse.llm.summarizer import USER_PROMPT_TEMPLATE
from pulse.models import Paper


class TestPromptTemplate:
    def test_format_contains_required_sections(self):
        paper = Paper(
            arxiv_id="2301.00001",
            title="Test Paper",
            abstract="Test abstract content.",
            arxiv_url="https://arxiv.org/abs/2301.00001",
            published_date="2023-01-01",
            authors=["Alice"],
        )
        prompt = USER_PROMPT_TEMPLATE.format(
            title=paper.title,
            abstract=paper.abstract,
            arxiv_url=paper.arxiv_url,
        )

        assert "【论文标题】" in prompt
        assert "Test Paper" in prompt
        assert "【论文摘要】" in prompt
        assert "Test abstract content." in prompt
        assert "【一句话核心创新点】" in prompt
        assert "【3个关键突破点】" in prompt
        assert "【原文链接】" in prompt
        assert "https://arxiv.org/abs/2301.00001" in prompt

    def test_format_no_english_section(self):
        """确认已移除英文原文部分。"""
        paper = Paper(
            arxiv_id="2301.00001",
            title="Test Paper",
            abstract="Test abstract.",
            arxiv_url="https://arxiv.org/abs/2301.00001",
            published_date="2023-01-01",
            authors=[],
        )
        prompt = USER_PROMPT_TEMPLATE.format(
            title=paper.title,
            abstract=paper.abstract,
            arxiv_url=paper.arxiv_url,
        )
        assert "【英文原文】" not in prompt
