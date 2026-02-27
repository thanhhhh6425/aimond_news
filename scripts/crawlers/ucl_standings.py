"""
scripts/crawlers/ucl_standings.py
Cào bảng xếp hạng Champions League từ FotMob.

UCL 2024/25 dùng format League Phase (36 đội, 1 bảng duy nhất — không có group).
Mỗi đội đá 8 trận trong League Phase với 8 đội khác nhau.

FotMob JSON structure:
  data["table"][0]["data"]["table"]["all"]  -> 36 đội League Phase
  Mỗi row:
    id, name, shortName, played, wins, draws, losses,
    scoresStr ("10:5"), goalConDiff, pts, idx (vị trí),
    qualColor:
      - "#17A2B8" / "Champions" -> Top 8: vào thẳng Round of 16
      - "#FFA500" / "Playoff"   -> Top 9-24: vào Knockout Playoffs
      - "#DC3545" / "Eliminated"-> Bottom 12: bị loại
    form: [{result:"W/D/L", against:"Team Name"}]
    deduction: số điểm bị trừ (nếu có)
    nextMatch: thông tin trận tiếp theo
"""
from typing import Dict, List
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging

logger = logging.getLogger(__name__)

# Map qualColor/qualId FotMob UCL -> DB status
# UCL League Phase qualifications:
#   Top 8    -> Round of 16 (trực tiếp)
#   9th-24th -> Knockout Playoffs
#   25th-36th -> Eliminated
UCL_QUAL_MAP = {
    # Màu xanh dương đậm / Champions direct
    "direct":     "champions_league",   # Top 8 -> R16 direct
    "knockout":   "europa",             # 9-24 -> Knockout Playoffs
    "eliminated": "relegation",         # 25-36 -> Eliminated
}


class UCLStandingsCrawler(BaseFotMobCrawler):
    LEAGUE = "UCL"

    def parse(self, data: Dict) -> List[Dict]:
        results = []
        try:
            table_sections = data.get("table", [])
            if not table_sections:
                logger.warning("[UCLStandings] No table data - season may not have started yet")
                return []

            for section in table_sections:
                # FotMob UCL: section co the la dict hoac co key "data"
                if isinstance(section, dict):
                    section_data = section.get("data", section)
                else:
                    continue

                table_obj = section_data.get("table", {})
                if not table_obj:
                    logger.warning("[UCLStandings] Table section is empty - League Phase not started yet")
                    continue

                # ── League Phase (format 2024/25+) ───────────────────
                if "all" in table_obj and table_obj["all"]:
                    rows = table_obj["all"]
                    for row in rows:
                        record = self._parse_row(row, group_name="League Phase")
                        if record:
                            results.append(record)

                # ── Group Stage (format cu) ──────────────────────────
                elif "groups" in table_obj:
                    for grp in table_obj["groups"]:
                        group_name = grp.get("name", "Group")
                        for row in grp.get("rows", []):
                            record = self._parse_row(row, group_name=group_name)
                            if record:
                                results.append(record)

                else:
                    logger.info(f"[UCLStandings] Table keys: {list(table_obj.keys())} - no rows found")

        except Exception as e:
            logger.error(f"[UCLStandings] Parse error: {e}", exc_info=True)

        if not results:
            logger.info("[UCLStandings] No standings yet - UCL season may not have started")
        else:
            logger.info(f"[UCLStandings] Parsed {len(results)} teams")
        return results

    def _parse_row(self, row: Dict, group_name: str = "League Phase") -> dict:
        try:
            gf, ga = self._parse_score_str(row.get("scoresStr", "0:0"))
            position = self.safe_int(row.get("idx", 0))

            # Xác định qualification status theo vị trí UCL League Phase
            qual_color = self.clean(row.get("qualColor", ""))
            status = self._map_ucl_qual(qual_color, position)

            # Điểm bị trừ (nếu bị phạt)
            deduction = self.safe_int(row.get("deduction", 0))

            # Form 8 trận gần nhất
            form_str = self._parse_form(row.get("form", []))

            return {
                "league":          "UCL",
                "season":          self.SEASON,
                "source_id":       str(row.get("id", "")),
                "team_name":       self.clean(row.get("name", "")),
                "team_short":      self.clean(row.get("shortName", "")),
                "group_name":      group_name,
                "position":        position,
                "played":          self.safe_int(row.get("played", 0)),
                "won":             self.safe_int(row.get("wins", 0)),
                "drawn":           self.safe_int(row.get("draws", 0)),
                "lost":            self.safe_int(row.get("losses", 0)),
                "goals_for":       gf,
                "goals_against":   ga,
                "goal_difference": self.safe_int(row.get("goalConDiff", 0)),
                "points":          self.safe_int(row.get("pts", 0)),
                "deduction":       deduction,
                "form":            form_str,
                "status":          status,
                "badge_url": (
                    f"https://images.fotmob.com/image_resources/logo/teamlogo/"
                    f"{row.get('id')}_small.png"
                ),
                # Qual label để hiển thị tooltip
                "qual_label":      self._qual_label(status, position),
            }
        except Exception as e:
            logger.debug(f"[UCLStandings] Skip row {row.get('id')}: {e}")
            return {}

    def _parse_score_str(self, score_str: str):
        """Parse "10-5" hoac "10:5" -> (10, 5)"""
        try:
            s = str(score_str).strip()
            sep = "-" if "-" in s else ":"
            parts = s.split(sep)
            return self.safe_int(parts[0]), self.safe_int(parts[1])
        except Exception:
            return 0, 0

    def _parse_form(self, form_list) -> str:
        """
        Parse form list -> string "WWDLW".
        FotMob form: [{"result": "W", "against": "Arsenal"}, ...]
        """
        if not form_list or not isinstance(form_list, list):
            return ""
        result = []
        for item in form_list[-8:]:  # UCL có tối đa 8 trận League Phase
            if isinstance(item, dict):
                outcome = str(
                    item.get("result", item.get("outcome", item.get("gameResult", "")))
                ).upper()
                result.append(outcome[:1] if outcome[:1] in ("W", "D", "L") else "")
            else:
                r = str(item).upper()
                result.append(r[:1] if r[:1] in ("W", "D", "L") else "")
        return "".join(r for r in result if r)

    def _map_ucl_qual(self, qual_color: str, position: int) -> str:
        """
        Map qualColor từ FotMob sang DB status.
        UCL 2024/25 League Phase:
          - Top 8 (1-8):   vào thẳng R16  -> champions_league
          - 9th-24th:      Knockout Playoff -> europa
          - 25th-36th:     Bị loại         -> relegation
        """
        color_lower = qual_color.lower()

        # Theo màu FotMob
        if any(c in color_lower for c in ["#17a2b8", "cyan", "teal", "direct", "r16"]):
            return "champions_league"
        if any(c in color_lower for c in ["#ffa500", "orange", "amber", "playoff"]):
            return "europa"
        if any(c in color_lower for c in ["#dc3545", "red", "eliminat"]):
            return "relegation"

        # Fallback theo vị trí nếu không có qualColor
        if position > 0:
            if position <= 8:
                return "champions_league"
            elif position <= 24:
                return "europa"
            else:
                return "relegation"

        return "normal"

    def _qual_label(self, status: str, position: int) -> str:
        """Label hiển thị tooltip cho từng zone."""
        if status == "champions_league":
            return "Advance to Round of 16"
        if status == "europa":
            return "Knockout Playoffs"
        if status == "relegation":
            return "Eliminated"
        return ""