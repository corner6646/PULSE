"""配置中心。从 .env 文件读取所有配置项并做类型转换。"""
import os
from dotenv import load_dotenv

load_dotenv()


def _list(value: str | None, default: str = "") -> list[str]:
    """将逗号分隔的字符串转为列表，去除空白项。"""
    if not value:
        value = default
    return [item.strip() for item in value.split(",") if item.strip()]


# ── 阿里云百炼 ──
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# ── 飞书 ──
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

# ── 钉钉（可选） ──
DINGTALK_WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")

# ── ArXiv ──
ARXIV_CATEGORIES = _list(os.getenv("ARXIV_CATEGORIES"), "cs.AI,cs.CL,cs.CV")
KEYWORDS = _list(os.getenv("KEYWORDS"), "")
MAX_PAPERS = int(os.getenv("MAX_PAPERS", "10"))

# ── 调度 ──
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:00")

# ── 日志 ──
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
