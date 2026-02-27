"""
scripts/crawlers/pl_matches.py
Cào lịch thi đấu + kết quả + live score Premier League từ FotMob.

FotMob JSON structure (leagues?id=47):
  data["matches"]["allMatches"]  -> list of match objects
  Each match:
    id, home{id,name,shortName}, away{id,name,shortName},
    status{utcTime, started, finished, cancelled,
           scoreStr ("2:1"), liveTime{short, long, addedTime},
           reason{short ("FT","HT"), long}},
    round, roundId, pageUrl
"""
from typing import Dict, List, Optional
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PLMatchesCrawler(BaseFotMobCrawler):
    LEAGUE = "PL"

    def parse(self, data: Dict) -> List[Dict]:
        results = []
        try:
            # FotMob PL: matches nam trong fixtures.allMatches
            fixtures = data.get("fixtures", {})
            all_matches = fixtures.get("allMatches", [])
            # Fallback
            if not all_matches:
                all_matches = data.get("matches", {}).get("allMatches", [])
            if not all_matches:
                logger.warning("[PLMatches] No matches found in response")
                return []

            for m in all_matches:
                record = self._parse_match(m)
                if record:
                    results.append(record)

        except Exception as e:
            logger.error(f"[PLMatches] Parse error: {e}", exc_info=True)

        logger.info(f"[PLMatches] Parsed {len(results)} matches")
        return results

    def _parse_match(self, m: Dict) -> Optional[Dict]:
        try:
            status_obj = m.get("status", {})
            home = m.get("home", {})
            away = m.get("away", {})

            # ── Status & Score ──────────────────────────────────────
            started   = status_obj.get("started", False)
            finished  = status_obj.get("finished", False)
            cancelled = status_obj.get("cancelled", False)

            reason_short = self.clean(status_obj.get("reason", {}).get("short", ""))

            if cancelled:
                status = "CANCELLED"
            elif finished:
                status = "FT"
            elif started:
                # Kiểm tra HT
                status = "HT" if reason_short == "HT" else "LIVE"
            else:
                status = "SCHEDULED"

            # ── Score ───────────────────────────────────────────────
            home_score = None
            away_score = None
            score_str = self.clean(status_obj.get("scoreStr", ""))
            if score_str:
                # FotMob dung "4 - 2" (co khoang trang) hoac "4:2" hoac "4-2"
                score_norm = score_str.replace(" ", "")
                # Thu tach bang "-" truoc (bo qua neu chi co 1 ki tu "-")
                if "-" in score_norm:
                    parts = score_norm.split("-")
                elif ":" in score_norm:
                    parts = score_norm.split(":")
                else:
                    parts = []
                if len(parts) == 2:
                    try:
                        home_score = int(parts[0])
                        away_score = int(parts[1])
                    except ValueError:
                        pass

            # ── Thời gian live ──────────────────────────────────────
            live_time = status_obj.get("liveTime", {})
            minute = None
            if live_time and status == "LIVE":
                short_time = self.clean(live_time.get("short", ""))
                # short có thể là "45+2" hoặc "67"
                if short_time and short_time.isdigit():
                    minute = int(short_time)
                elif "+" in short_time:
                    base, added = short_time.split("+", 1)
                    try:
                        minute = int(base) + int(added)
                    except ValueError:
                        minute = self.safe_int(base)
                added_time = live_time.get("addedTime", 0)
            else:
                added_time = 0

            # ── Kickoff time ────────────────────────────────────────
            kickoff_at = None
            utc_time = status_obj.get("utcTime", "")
            if utc_time:
                try:
                    kickoff_at = datetime.fromisoformat(
                        str(utc_time).replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            # ── Round / Matchweek ───────────────────────────────────
            round_info = self.clean(m.get("round", ""))
            matchweek = None
            if round_info.isdigit():
                matchweek = int(round_info)
            elif "round" in round_info.lower():
                parts = round_info.lower().replace("round", "").strip()
                matchweek = self.safe_int(parts) if parts.isdigit() else None

            return {
                "league": "PL",
                "season": self.SEASON,
                "source_id": str(m.get("id", "")),
                "home_team_name": self.clean(home.get("name", "")),
                "home_team_short": self.clean(home.get("shortName", "")),
                "home_source_id": str(home.get("id", "")),
                "home_score": home_score,
                "away_team_name": self.clean(away.get("name", "")),
                "away_team_short": self.clean(away.get("shortName", "")),
                "away_source_id": str(away.get("id", "")),
                "away_score": away_score,
                "status": status,
                "minute": minute,
                "added_time": added_time,
                "kickoff_at": kickoff_at,
                "matchweek": matchweek,
                "home_badge": f"https://images.fotmob.com/image_resources/logo/teamlogo/{home.get('id')}_small.png",
                "away_badge": f"https://images.fotmob.com/image_resources/logo/teamlogo/{away.get('id')}_small.png",
            }
        except Exception as e:
            logger.debug(f"[PLMatches] Skip match {m.get('id')}: {e}")
            return None