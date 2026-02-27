"""
scripts/utils/helpers.py
Các hàm tiện ích dùng chung trong crawlers và db_writer
"""
import re
import logging
from datetime import datetime, timezone
from typing import Optional, Any

logger = logging.getLogger(__name__)


def safe_int(val: Any, default: int = 0) -> int:
    """Chuyển đổi an toàn sang int."""
    try:
        return int(str(val).strip().replace(",", "").replace(".", ""))
    except (ValueError, TypeError):
        return default


def safe_float(val: Any, default: float = 0.0) -> float:
    """Chuyển đổi an toàn sang float."""
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default


def clean_text(val: Any) -> str:
    """Xóa khoảng trắng thừa."""
    if val is None:
        return ""
    return re.sub(r"\s+", " ", str(val)).strip()


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parse nhiều định dạng datetime khác nhau."""
    if not val:
        return None
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val / 1000, tz=timezone.utc)
        s = str(val).strip().replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def make_slug(text: str) -> str:
    """Tạo URL slug từ text."""
    slug = clean_text(text).lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def truncate(text: str, max_len: int = 500) -> str:
    """Cắt ngắn text nếu quá dài."""
    if not text:
        return ""
    text = clean_text(text)
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def map_position(raw: str) -> str:
    """Map position code sang chuẩn GK/DEF/MID/FWD."""
    mapping = {
        "G": "GK", "GK": "GK", "GOALKEEPER": "GK",
        "D": "DEF", "DF": "DEF", "DEFENDER": "DEF", "CB": "DEF", "LB": "DEF", "RB": "DEF",
        "M": "MID", "MF": "MID", "MIDFIELDER": "MID", "CM": "MID", "AM": "MID", "DM": "MID",
        "F": "FWD", "FW": "FWD", "FORWARD": "FWD", "ST": "FWD", "CF": "FWD", "LW": "FWD", "RW": "FWD",
        "A": "FWD", "ATT": "FWD", "ATTACKER": "FWD",
    }
    return mapping.get(str(raw).upper().strip(), "FWD")


def map_match_status(raw: str) -> str:
    """Map trạng thái trận đấu sang chuẩn."""
    mapping = {
        "U": "SCHEDULED", "UPCOMING": "SCHEDULED", "SCHEDULED": "SCHEDULED", "PRE": "SCHEDULED",
        "L": "LIVE", "LIVE": "LIVE", "INPROGRESS": "LIVE", "IN_PROGRESS": "LIVE",
        "HT": "HT", "HALFTIME": "HT", "HALF_TIME": "HT",
        "C": "FT", "COMPLETED": "FT", "FINISHED": "FT", "ENDED": "FT", "FT": "FT",
        "P": "POSTPONED", "POSTPONED": "POSTPONED",
        "X": "CANCELLED", "CANCELLED": "CANCELLED", "CANCELED": "CANCELLED",
    }
    return mapping.get(str(raw).upper().strip(), "SCHEDULED")
