"""测试 ArXiv 数据拉取模块的纯逻辑（不依赖网络）。"""
import xml.etree.ElementTree as ET
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pulse.ingestion.arxiv_fetcher import _matches_keywords, _parse_entry

# 测试用的 ATOM entry 片段（模拟 ArXiv 返回）
SAMPLE_ENTRY_XML = """<entry xmlns="http://www.w3.org/2005/Atom">
  <id>http://arxiv.org/abs/2301.00001v2</id>
  <title>Test Paper Title: A Novel Approach</title>
  <summary>This paper proposes a new method for reasoning over knowledge graphs.</summary>
  <published>2023-01-01T00:00:00Z</published>
  <author><name>Alice Wang</name></author>
  <author><name>Bob Li</name></author>
</entry>"""


class TestKeywordFilter:
    def test_match_in_title(self, monkeypatch):
        monkeypatch.setattr("pulse.ingestion.arxiv_fetcher.settings.KEYWORDS", ["reasoning"])
        assert _matches_keywords("reasoning model test abstract text")
        assert not _matches_keywords("classification model test abstract text")

    def test_match_in_abstract(self, monkeypatch):
        monkeypatch.setattr("pulse.ingestion.arxiv_fetcher.settings.KEYWORDS", ["graph"])
        assert _matches_keywords("title here. knowledge graphs are useful.")

    def test_case_insensitive(self, monkeypatch):
        monkeypatch.setattr("pulse.ingestion.arxiv_fetcher.settings.KEYWORDS", ["RAG"])
        assert _matches_keywords("title: Investigating RAG systems")
        assert _matches_keywords("title: investigating rag systems")

    def test_empty_keywords_passes_all(self, monkeypatch):
        monkeypatch.setattr("pulse.ingestion.arxiv_fetcher.settings.KEYWORDS", [])
        assert _matches_keywords("any text at all")

    def test_no_match(self, monkeypatch):
        monkeypatch.setattr("pulse.ingestion.arxiv_fetcher.settings.KEYWORDS",
                            ["transformer", "RLHF"])
        assert not _matches_keywords("This paper is about CNN architectures.")


class TestParseEntry:
    def test_parse_basic_fields(self):
        entry = ET.fromstring(SAMPLE_ENTRY_XML)
        paper = _parse_entry(entry)

        assert paper.arxiv_id == "2301.00001"  # version stripped
        assert "Test Paper Title" in paper.title
        assert paper.arxiv_url == "https://arxiv.org/abs/2301.00001"
        assert paper.published_date == "2023-01-01T00:00:00Z"

    def test_parse_authors(self):
        entry = ET.fromstring(SAMPLE_ENTRY_XML)
        paper = _parse_entry(entry)

        assert len(paper.authors) == 2
        assert paper.authors[0] == "Alice Wang"
        assert paper.authors[1] == "Bob Li"

    def test_parse_abstract(self):
        entry = ET.fromstring(SAMPLE_ENTRY_XML)
        paper = _parse_entry(entry)

        assert "reasoning over knowledge graphs" in paper.abstract
