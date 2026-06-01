"""SQLite 数据库操作：论文去重 + 摘要缓存。"""
import json
import sqlite3
import os
from pulse.models import Paper

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "pulse.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """创建 papers 和 summaries 表（如不存在）。"""
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            arxiv_id      TEXT PRIMARY KEY,
            title         TEXT,
            abstract      TEXT,
            arxiv_url     TEXT,
            published_date TEXT,
            authors_json  TEXT,
            processed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS summaries (
            arxiv_id     TEXT PRIMARY KEY,
            summary_text TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def is_paper_processed(arxiv_id: str) -> bool:
    """检查某篇论文是否已经处理过。"""
    conn = _connect()
    row = conn.execute("SELECT 1 FROM papers WHERE arxiv_id = ?", (arxiv_id,)).fetchone()
    conn.close()
    return row is not None


def mark_paper_processed(paper: Paper) -> None:
    """将论文标记为已处理（去重依据）。"""
    conn = _connect()
    conn.execute(
        "INSERT OR IGNORE INTO papers (arxiv_id, title, abstract, arxiv_url, published_date, authors_json) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (paper.arxiv_id, paper.title, paper.abstract, paper.arxiv_url,
         paper.published_date, json.dumps(paper.authors, ensure_ascii=False))
    )
    conn.commit()
    conn.close()


def get_cached_summary(arxiv_id: str) -> str | None:
    """查询某篇论文的 LLM 摘要缓存，未命中返回 None。"""
    conn = _connect()
    row = conn.execute("SELECT summary_text FROM summaries WHERE arxiv_id = ?", (arxiv_id,)).fetchone()
    conn.close()
    return row[0] if row else None


def cache_summary(arxiv_id: str, summary: str) -> None:
    """缓存一篇论文的 LLM 摘要。"""
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO summaries (arxiv_id, summary_text) VALUES (?, ?)",
        (arxiv_id, summary)
    )
    conn.commit()
    conn.close()
