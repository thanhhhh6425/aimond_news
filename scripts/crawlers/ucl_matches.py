"""
scripts/crawlers/ucl_matches.py
Cao lich thi dau + ket qua + live score Champions League tu FotMob.

UCL co cac dac diem rieng so voi PL:
  - Data nam trong fixtures.allMatches (khong phai matches.allMatches)
  - scoreStr dung "0 - 2" (co khoang trang)
  - Knockout rounds: R16, QF, SF, Final
  - Aggregate score (tong 2 luot)
  - Extra time, Penalty shootout
  - Leg 1 / Leg 2
"""
from typing import Dict, List, Optional
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

UCL_ROUND_NAMES = {
    "1": "League Phase", "2": "League Phase", "3": "League Phase",
    "4": "League Phase", "5": "League Phase", "6": "League Phase",
    "7": "League Phase", "8": "League Phase",
    "Knockout Playoffs": "Knockout Playoffs",
    "Round of 16": "Round of 16",
    "Quarter-finals": "Quarter-finals",
    "Semi-finals": "Semi-finals",
    "Final": "Final",
}


class UCLMatchesCrawler(BaseFotMobCrawler):
    LEAGUE = "UCL"

    def parse(self, data: Dict) -> List[Dict]:
        results = []
        try:
            # UCL dung fixtures.allMatches thay vi matches.allMatches
            fixtures = data.get("fixtures", {})
            all_matches = fixtures.get("allMatches", [])

            # Fallback: thu matches.allMatches
            if not all_matches:
                all_matches = data.get("matches", {}).get("allMatches", [])

            if not all_matches:
                logger.warning("[UCLMatches] No matches found")
                return []

            logger.info(f"[UCLMatches] Processing {len(all_matches)} raw matches...")

            for m in all_matches:
                record = self._parse_match(m)
                if record:
                    results.append(record)

        except Exception as e:
            logger.error(f"[UCLMatches] Parse error: {e}", exc_info=True)

        logger.info(f"[UCLMatches] Parsed {len(results)} matches")
        return results

    def _parse_match(self, m: Dict) -> Optional[Dict]:
        try:
            status_obj  = m.get("status", {})
            home        = m.get("home", {})
            away        = m.get("away", {})
            reason      = status_obj.get("reason", {})

            # ── Trang thai ───────────────────────────────────────────
            started   = status_obj.get("started", False)
            finished  = status_obj.get("finished", False)
            cancelled = status_obj.get("cancelled", False)
            reason_short = self.clean(reason.get("short", "")).upper()
            reason_long  = self.clean(reason.get("long", ""))

            if cancelled:
                status = "CANCELLED"
            elif finished:
                status = "FT"
            elif started:
                status = "HT" if reason_short == "HT" else "LIVE"
            else:
                status = "SCHEDULED"

            # Ket thuc dac biet
            ended_aet = reason_short in ("AET", "AP") or "extra time" in reason_long.lower()
            ended_pen = "penalt" in reason_long.lower() or reason_short in ("PEN", "P", "AP")

            # ── Ti so: "0 - 2" hoac "0:2" hoac "0-2" ───────────────
            home_score = None
            away_score = None
            score_str = self.clean(status_obj.get("scoreStr", ""))
            if score_str:
                # Chuan hoa: bo khoang trang, thay " - " bang "-"
                score_norm = score_str.replace(" ", "").replace("-", ":")
                if ":" in score_norm:
                    parts = score_norm.split(":")
                    if len(parts) == 2:
                        try:
                            home_score = int(parts[0])
                            away_score = int(parts[1])
                        except ValueError:
                            pass

            # ── Ti so tong 2 luot (aggregate) ───────────────────────
            agg_home, agg_away = None, None
            agg_str = self.clean(status_obj.get("aggregatedStr", ""))
            if agg_str:
                agg_norm = agg_str.replace(" ", "").replace("-", ":")
                if ":" in agg_norm:
                    parts = agg_norm.split(":")
                    try:
                        agg_home = int(parts[0])
                        agg_away = int(parts[1])
                    except ValueError:
                        pass

            # ── Ti so penalty ────────────────────────────────────────
            pen_home, pen_away = None, None
            pen_score = status_obj.get("penScore", {})
            if pen_score and ended_pen:
                pen_home = self.safe_int(pen_score.get("home"))
                pen_away = self.safe_int(pen_score.get("away"))

            # ── Phut thi dau (live) ──────────────────────────────────
            minute, added_time = None, 0
            if status == "LIVE":
                live_time = status_obj.get("liveTime", {})
                if live_time:
                    short_time = self.clean(live_time.get("short", ""))
                    if "+" in short_time:
                        base, added = short_time.split("+", 1)
                        try:
                            minute = int(base) + int(added)
                            added_time = int(added)
                        except ValueError:
                            minute = self.safe_int(base)
                    elif short_time.isdigit():
                        minute = int(short_time)

            # ── Kickoff time ─────────────────────────────────────────
            kickoff_at = None
            utc_time = status_obj.get("utcTime", "")
            if utc_time:
                try:
                    kickoff_at = datetime.fromisoformat(
                        str(utc_time).replace("Z", "+00:00")
                    )
                except Exception:
                    pass

            # ── Vong dau UCL ─────────────────────────────────────────
            round_str  = self.clean(m.get("round", ""))
            round_name_raw = self.clean(m.get("roundName", round_str))
            UCL_ROUND_MAP = {
                "1":"League Phase","2":"League Phase","3":"League Phase",
                "4":"League Phase","5":"League Phase","6":"League Phase",
                "7":"League Phase","8":"League Phase",
                "playoff":"Knockout Playoffs",
                "Round of 16":"Vòng 1/8","round_of_16":"Vòng 1/8",
                "Quarter-finals":"Tứ kết","quarterfinals":"Tứ kết",
                "Semi-finals":"Bán kết","semifinals":"Bán kết",
                "Final":"Chung kết",
            }
            round_name = UCL_ROUND_MAP.get(round_str, UCL_ROUND_MAP.get(round_name_raw, round_name_raw or "League Phase"))
            is_knockout = round_str not in ("1","2","3","4","5","6","7","8") and bool(round_str)
            leg = self.safe_int(m.get("leg", 0))

            # Matchweek: League Phase = 1-8, playoff = 9, R16 = 10, QF = 11, SF = 12, Final = 13
            matchweek = None
            ROUND_TO_WEEK = {
                "playoff": 9, "Knockout Playoffs": 9,
                "Round of 16": 10, "round_of_16": 10,
                "Quarter-finals": 11, "quarterfinals": 11,
                "Semi-finals": 12, "semifinals": 12,
                "Final": 13,
            }
            if round_str.isdigit():
                matchweek = int(round_str)
            elif round_str in ROUND_TO_WEEK:
                matchweek = ROUND_TO_WEEK[round_str]
            elif round_name_raw in ROUND_TO_WEEK:
                matchweek = ROUND_TO_WEEK[round_name_raw]

            return {
                "league":          "UCL",
                "season":          self.SEASON,
                "source_id":       str(m.get("id", "")),
                "home_team_name":  self.clean(home.get("name", "")),
                "home_team_short": self.clean(home.get("shortName", "")),
                "home_source_id":  str(home.get("id", "")),
                "away_team_name":  self.clean(away.get("name", "")),
                "away_team_short": self.clean(away.get("shortName", "")),
                "away_source_id":  str(away.get("id", "")),
                "home_badge": f"https://images.fotmob.com/image_resources/logo/teamlogo/{home.get('id')}_small.png",
                "away_badge": f"https://images.fotmob.com/image_resources/logo/teamlogo/{away.get('id')}_small.png",
                "home_score":      home_score,
                "away_score":      away_score,
                "agg_home":        agg_home,
                "agg_away":        agg_away,
                "home_score_pen":  pen_home,
                "away_score_pen":  pen_away,
                "status":          status,
                "ended_aet":       ended_aet,
                "ended_pen":       ended_pen,
                "minute":          minute,
                "added_time":      added_time,
                "kickoff_at":      kickoff_at,
                "matchweek":       matchweek,
                "round_name":      round_name,
                "is_knockout":     is_knockout,
                "leg":             leg,
            }
        except Exception as e:
            logger.debug(f"[UCLMatches] Skip match {m.get('id')}: {e}")
            return None