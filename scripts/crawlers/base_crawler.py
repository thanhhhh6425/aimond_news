"""
scripts/crawlers/base_crawler.py
Base class cho tất cả FotMob crawlers.
Dung requests (dong bo) thay vi aiohttp de tranh loi DNS tren Windows.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import requests
import urllib3

# Tat canh bao SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

FOTMOB_BASE = "https://www.fotmob.com/api"
FOTMOB_LEAGUE_IDS = {"PL": 47, "UCL": 42}

FOTMOB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.fotmob.com/",
    "Origin": "https://www.fotmob.com",
    "Connection": "keep-alive",
}

SEASON = "2025"


class BaseFotMobCrawler(ABC):
    LEAGUE: str = ""
    SEASON: str = SEASON

    def __init__(self, retry: int = 3, delay: float = 2.0):
        self.retry = retry
        self.delay = delay
        self.league_id = FOTMOB_LEAGUE_IDS.get(self.LEAGUE, 47)
        self._session = requests.Session()
        self._session.headers.update(FOTMOB_HEADERS)
        self._session.verify = False

    def run_sync(self) -> List[Dict]:
        """Chay dong bo - dung trong scheduler va run_all.py."""
        for attempt in range(1, self.retry + 1):
            try:
                data = self._fetch_league()
                if data:
                    results = self.parse(data)
                    logger.info(f"[{self.__class__.__name__}] Crawled {len(results)} records")
                    return results
            except Exception as e:
                logger.warning(f"[{self.__class__.__name__}] Attempt {attempt}/{self.retry} failed: {e}")
                if attempt < self.retry:
                    import time
                    time.sleep(self.delay * attempt)
        logger.error(f"[{self.__class__.__name__}] All retries exhausted")
        return []

    async def run(self) -> List[Dict]:
        """Async wrapper - goi run_sync trong executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run_sync)

    @abstractmethod
    def parse(self, data: Dict) -> List[Dict]:
        ...

    def _fetch_league(self) -> Optional[Dict]:
        url = f"{FOTMOB_BASE}/leagues?id={self.league_id}"
        return self._get(url)

    def _fetch_matches_day(self, date_str: str) -> Optional[Dict]:
        url = f"{FOTMOB_BASE}/matches?date={date_str}"
        return self._get(url)

    def _fetch_match_detail(self, match_id: int) -> Optional[Dict]:
        url = f"{FOTMOB_BASE}/matchDetails?matchId={match_id}"
        return self._get(url)

    def _get(self, url: str) -> Optional[Dict]:
        try:
            resp = self._session.get(url, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} for {url}")
                return None
            return resp.json()
        except Exception as e:
            raise Exception(f"GET {url} failed: {e}")

    @staticmethod
    def safe_int(val: Any, default: int = 0) -> int:
        try:
            if val in (None, "", "-", "?"):
                return default
            return int(str(val).strip().replace(",", ""))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_float(val: Any, default: float = 0.0) -> float:
        try:
            if val in (None, "", "-"):
                return default
            return float(str(val).strip())
        except (ValueError, TypeError):
            return default

    @staticmethod
    def clean(val: Any) -> str:
        return str(val).strip() if val is not None else ""

    @staticmethod
    def map_status(raw: str) -> str:
        raw = str(raw).lower().strip()
        if raw in ("ft", "finished", "fulltime", "full time", "aet", "after et"):
            return "FT"
        if raw in ("ht", "halftime", "half time"):
            return "HT"
        if raw in ("live", "inprogress", "in progress", "1h", "2h", "et", "pen"):
            return "LIVE"
        if raw in ("postponed",):
            return "POSTPONED"
        if raw in ("cancelled", "canceled", "abandoned"):
            return "CANCELLED"
        return "SCHEDULED"

    @staticmethod
    def map_position(raw: str) -> str:
        """Map FotMob role keys -> position codes."""
        r = str(raw).strip().lower()
        # FotMob role keys: keeper_long, defender, midfielder, forward, attacker
        if r in ("g", "gk", "goalkeeper", "keeper", "keeper_long", "keeper_short"):
            return "GK"
        if r in ("d", "df", "defender", "back", "center_back", "full_back",
                 "right_back", "left_back", "wing_back"):
            return "DEF"
        if r in ("m", "mf", "midfielder", "mid", "central_midfielder",
                 "defensive_midfielder", "attacking_midfielder", "right_midfielder",
                 "left_midfielder", "wide_midfielder"):
            return "MID"
        if r in ("f", "fw", "forward", "attacker", "striker", "right_winger",
                 "left_winger", "center_forward", "second_striker", "wing_forward"):
            return "FWD"
        # Fallback: kiem tra cac tu khoa
        if "keep" in r or "goal" in r:
            return "GK"
        if "def" in r or "back" in r:
            return "DEF"
        if "mid" in r:
            return "MID"
        return "FWD"