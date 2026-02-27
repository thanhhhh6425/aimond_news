"""
scripts/crawlers/pl_clubs.py
Cao thong tin cac cau lac bo PL va UCL tu FotMob team API.

FotMob /api/teams?id=<id>:
  details: {id, name, shortName, country}
  overview: {venue, topPlayers, teamForm, nextMatch, lastMatch, teamColors, squad}
  squad.squad: [{title, members:[{id,name,role,shirtNumber,ccode,height,dateOfBirth}]}]
"""
from typing import Dict, List, Optional
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging

logger = logging.getLogger(__name__)


class PLClubsCrawler(BaseFotMobCrawler):
    LEAGUE = "PL"

    def parse(self, data: Dict) -> List[Dict]:
        """Lay club IDs tu standings, fetch tung club."""
        results = []
        club_ids = set()

        # Lay tu table
        for section in data.get("table", []):
            rows = section.get("data", {}).get("table", {}).get("all", [])
            for row in rows:
                cid = row.get("id")
                if cid:
                    club_ids.add((str(cid), self.clean(row.get("name","")), self.clean(row.get("shortName",""))))

        logger.info(f"[PLClubs] Fetching {len(club_ids)} clubs...")
        for cid, name, short in club_ids:
            record = self._fetch_club(cid, name, short)
            if record:
                results.append(record)

        logger.info(f"[PLClubs] Parsed {len(results)} clubs")
        return results

    def _fetch_club(self, team_id: str, name: str, short: str) -> Optional[Dict]:
        try:
            data = self._get(f"https://www.fotmob.com/api/teams?id={team_id}")
            if not data:
                return None

            details = data.get("details", {})
            overview = data.get("overview", {})

            # ── Venue/Stadium ─────────────────────────────────────────
            # FotMob structure: overview.venue.widget.{name, city}
            #                   overview.venue.statPairs: [["Capacity", 61276], ...]
            venue = overview.get("venue", {})
            stadium_name = stadium_city = ""
            stadium_capacity = 0
            if isinstance(venue, dict):
                widget = venue.get("widget", {})
                stadium_name     = self.clean(widget.get("name", ""))
                stadium_city     = self.clean(widget.get("city", ""))
                # Capacity tu statPairs
                for pair in venue.get("statPairs", []):
                    if isinstance(pair, list) and len(pair) == 2:
                        if str(pair[0]).lower() == "capacity":
                            stadium_capacity = self.safe_int(pair[1])

            # ── Manager hien tai ──────────────────────────────────────
            # coachHistory sap xep tu cu -> moi, lay entry moi nhat
            # Loc theo season moi nhat (format "2025/2026" > "2024/2025")
            manager = ""
            manager_id = None
            coach_history = overview.get("coachHistory", [])
            if coach_history and isinstance(coach_history, list):
                # Sap xep giam dan theo season -> lay dau tien
                def season_sort(c):
                    s = c.get("season", "0000/0000")
                    try:
                        return int(s.split("/")[0])
                    except:
                        return 0
                sorted_coaches = sorted(coach_history, key=season_sort, reverse=True)
                current = sorted_coaches[0]
                manager = self.clean(current.get("name", ""))
                manager_id = current.get("id")

            # Kiem tra squad section "coach" de co ten HLV chinh xac nhat
            squad_sections = data.get("squad", {}).get("squad", [])
            for sec in squad_sections:
                if sec.get("title", "").lower() in ("coach", "coaches"):
                    members = sec.get("members", [])
                    if members:
                        manager = self.clean(members[0].get("name", manager))
                    break

            # ── Team colors ───────────────────────────────────────────
            colors = overview.get("teamColors", {})
            primary_color = self.clean(colors.get("color", colors.get("primary", "")))

            # ── Badge URLs ────────────────────────────────────────────
            badge_url = f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}_small.png"
            big_badge  = f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}.png"

            return {
                "league":           self.LEAGUE,
                "season":           self.SEASON,
                "source_id":        team_id,
                "name":             self.clean(details.get("name", name)),
                "short_name":       self.clean(details.get("shortName", short)),
                "country":          self.clean(details.get("country", "")),
                "badge_url":        badge_url,
                "badge_url_big":    big_badge,
                "stadium_name":     stadium_name,
                "stadium_city":     stadium_city,
                "stadium_capacity": stadium_capacity,
                "manager":          "",  # Nhap tay - khong tu dong cap nhat
                "primary_color":    primary_color,
            }
        except Exception as e:
            logger.debug(f"[PLClubs] Club {team_id} error: {e}")
            return None


class UCLClubsCrawler(PLClubsCrawler):
    LEAGUE = "UCL"

    def parse(self, data: Dict) -> List[Dict]:
        """Lay club IDs tu fixtures UCL."""
        results = []
        club_ids = set()

        fixtures = data.get("fixtures", {})
        for m in fixtures.get("allMatches", []):
            h = m.get("home", {})
            a = m.get("away", {})
            if h.get("id"): club_ids.add((str(h["id"]), h.get("name",""), h.get("shortName","")))
            if a.get("id"): club_ids.add((str(a["id"]), a.get("name",""), a.get("shortName","")))

        logger.info(f"[UCLClubs] Fetching {len(club_ids)} clubs...")
        for cid, name, short in list(club_ids)[:40]:
            record = self._fetch_club(cid, name, short)
            if record:
                record["league"] = "UCL"
                results.append(record)

        logger.info(f"[UCLClubs] Parsed {len(results)} clubs")
        return results