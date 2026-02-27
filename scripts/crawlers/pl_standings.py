"""
scripts/crawlers/pl_standings.py
Cào bảng xếp hạng Premier League từ FotMob API.

FotMob JSON structure (leagues?id=47):
  data["table"][0]["data"]["table"]["all"]  -> list of team rows
  Each row:
    id, name, shortName, played, wins, draws, losses,
    scoresStr ("62:26"), goalConDiff, pts, idx (position),
    qualColor (màu: Champions League, Europa, Relegation)
    deduction (điểm trừ nếu có)
"""
from typing import Dict, List
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging

logger = logging.getLogger(__name__)


class PLStandingsCrawler(BaseFotMobCrawler):
    LEAGUE = "PL"

    def parse(self, data: Dict) -> List[Dict]:
        results = []
        try:
            # FotMob: data["table"] là list, phần tử đầu là "All" table
            table_sections = data.get("table", [])
            if not table_sections:
                logger.error("[PLStandings] No table data found")
                return []

            # Lấy section "all" (toàn bộ mùa giải)
            all_table = None
            for section in table_sections:
                section_data = section.get("data", {})
                table_obj = section_data.get("table", {})
                if "all" in table_obj:
                    all_table = table_obj["all"]
                    break

            if not all_table:
                logger.error("[PLStandings] Cannot find table.all")
                return []

            for row in all_table:
                gf, ga = self._parse_score_str(row.get("scoresStr", "0:0"))
                status = self._map_qual_color(row.get("qualColor", ""), position=self.safe_int(row.get("idx", 0)))

                record = {
                    "league": "PL",
                    "season": self.SEASON,
                    "source_id": str(row.get("id", "")),
                    "team_name": self.clean(row.get("name", "")),
                    "team_short": self.clean(row.get("shortName", "")),
                    "position": self.safe_int(row.get("idx", 0)),
                    "played": self.safe_int(row.get("played", 0)),
                    "won": self.safe_int(row.get("wins", 0)),
                    "drawn": self.safe_int(row.get("draws", 0)),
                    "lost": self.safe_int(row.get("losses", 0)),
                    "goals_for": gf,
                    "goals_against": ga,
                    "goal_difference": self.safe_int(row.get("goalConDiff", 0)),
                    "points": self.safe_int(row.get("pts", 0)),
                    "form": "",  # FotMob PL khong tra ve form trong table
                    "status": status,
                    "badge_url": self._badge_url(row.get("id")),
                }
                results.append(record)
                logger.debug(f"  #{record['position']} {record['team_name']} — {record['points']}pts")

        except Exception as e:
            logger.error(f"[PLStandings] Parse error: {e}", exc_info=True)

        logger.info(f"[PLStandings] Parsed {len(results)} teams")
        return results

    def _parse_score_str(self, score_str: str):
        """Parse '56-21' hoac '62:26' -> (56, 21)"""
        try:
            s = str(score_str).strip()
            # FotMob dung ca "-" lan ":" tuy phien ban
            sep = "-" if "-" in s else ":"
            parts = s.split(sep)
            return self.safe_int(parts[0]), self.safe_int(parts[1])
        except Exception:
            return 0, 0

    def _parse_form(self, form_list) -> str:
        """Convert form list to string: ['W','D','L','W','W'] -> 'WDLWW'"""
        if not form_list or not isinstance(form_list, list):
            return ""
        result = []
        for item in form_list[-5:]:
            if isinstance(item, dict):
                result.append(str(item.get("result", item.get("outcome", ""))).upper()[:1])
            else:
                result.append(str(item).upper()[:1])
        return "".join(result)

    def _map_qual_color(self, color: str, position: int = 0) -> str:
        """
        Map FotMob qualColor to DB status.
        Cac mau FotMob PL 2024/25:
          #2AD572 (xanh la)  -> Top 4: Champions League
          #F5A623 (cam)      -> Europa League / Conference
          #E74C3C (do)       -> Relegation (Bottom 3)
        """
        c = str(color).upper().strip()
        # Xanh la (Champions League)
        if c in ("#2AD572", "#17A2B8", "#00FF85") or "2AD572" in c:
            return "champions_league"
        # Cam (Europa / Conference)
        if c in ("#F5A623", "#FFA500", "#FD7E14") or "F5A623" in c or "FFA500" in c:
            return "europa"
        # Do (Relegation)
        if c in ("#E74C3C", "#DC3545", "#FF0000") or "E74C3C" in c or "DC3545" in c:
            return "relegation"
        # Fallback theo vi tri
        if position > 0:
            if position <= 4:   return "champions_league"
            if position <= 7:   return "europa"
            if position >= 18:  return "relegation"
        return "normal"

    def _badge_url(self, team_id) -> str:
        if not team_id:
            return ""
        return f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}_small.png"