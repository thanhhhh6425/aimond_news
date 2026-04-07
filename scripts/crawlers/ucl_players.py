"""
scripts/crawlers/ucl_players.py
Cao cu thu Champions League - UCL 2025/26 (season 28184).
"""
from typing import Dict, List
from scripts.crawlers.pl_players import PLPlayersCrawler
import logging

logger = logging.getLogger(__name__)

UCL_SEASON_ID = 28184
UCL_LEAGUE_ID = 42

STAT_URLS_UCL = [
    ("goals",        f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/goals.json"),
    ("assists",      f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/goal_assist.json"),
    ("rating",       f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/rating.json"),
    ("mins_played",  f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/mins_played.json"),
    ("clean_sheets", f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/clean_sheet.json"),
    ("saves",        f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/saves.json"),
    ("yellow_cards", f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/yellow_card.json"),
    ("red_cards",    f"https://data.fotmob.com/stats/{UCL_LEAGUE_ID}/season/{UCL_SEASON_ID}/red_card.json"),
]


def _ucl_base(pid: str, season: str, name: str = "", team_id: str = "", team_name: str = "") -> Dict:
    """Tao base player dict voi league=UCL."""
    return {
        "league":         "UCL",
        "season":         season,
        "source_id":      pid,
        "name":           name,
        "team_source_id": team_id,
        "team_name":      team_name,
        "position":       "FWD",
        "nationality":    "",
        "photo_url":      f"https://images.fotmob.com/image_resources/playerimages/{pid}.png",
        "goals": 0, "assists": 0, "saves": 0, "clean_sheets": 0,
        "yellow_cards": 0, "red_cards": 0, "appearances": 0,
        "minutes_played": 0, "average_rating": 0.0, "expected_goals": 0.0,
        "shirt_number": None, "date_of_birth": "", "height_cm": None,
    }


class UCLPlayersCrawler(PLPlayersCrawler):
    LEAGUE = "UCL"

    def parse(self, data: Dict) -> List[Dict]:
        players: Dict[str, Dict] = {}

        # ── 1. Stats URLs ────────────────────────────────────────────
        for stat_key, url in STAT_URLS_UCL:
            try:
                stat_data = self._get(url)
                if not stat_data:
                    continue
                for top_list in stat_data.get("TopLists", []):
                    for entry in top_list.get("StatList", []):
                        pid = str(entry.get("ParticiantId", entry.get("ParticipantId", "")))
                        if not pid:
                            continue

                        if pid not in players:
                            players[pid] = _ucl_base(
                                pid, self.SEASON,
                                name=self.clean(entry.get("ParticipantName", "")),
                                team_id=str(entry.get("TeamId", "")),
                                team_name=self.clean(entry.get("TeamName", "")),
                            )
                        else:
                            if not players[pid].get("name"):
                                players[pid]["name"] = self.clean(entry.get("ParticipantName", ""))
                            if not players[pid].get("team_source_id"):
                                players[pid]["team_source_id"] = str(entry.get("TeamId", ""))
                                players[pid]["team_name"] = self.clean(entry.get("TeamName", ""))

                        # Position tu Positions array
                        positions = entry.get("Positions", [])
                        if positions and not players[pid].get("_positions"):
                            players[pid]["_positions"] = positions
                            pos_id = positions[0] if positions else 0
                            if pos_id == 11:
                                players[pid]["position"] = "GK"
                            elif pos_id in range(32, 64):
                                players[pid]["position"] = "DEF"
                            elif pos_id in range(64, 83):
                                players[pid]["position"] = "MID"
                            elif pos_id in list(range(83, 108)) + [115]:
                                players[pid]["position"] = "FWD"

                        val = entry.get("StatValue", 0)
                        if stat_key == "goals":
                            players[pid]["goals"]          = self.safe_int(val)
                            players[pid]["appearances"]    = self.safe_int(entry.get("MatchesPlayed", 0))
                            players[pid]["minutes_played"] = self.safe_int(entry.get("MinutesPlayed", 0))
                        elif stat_key == "assists":
                            players[pid]["assists"]        = self.safe_int(val)
                        elif stat_key == "rating":
                            players[pid]["average_rating"] = self.safe_float(val)
                        elif stat_key == "mins_played":
                            if not players[pid].get("minutes_played"):
                                players[pid]["minutes_played"] = self.safe_int(val)
                        elif stat_key == "clean_sheets":
                            if players[pid].get("position") in ("GK", ""):
                                players[pid]["clean_sheets"] = self.safe_int(val)
                                players[pid]["position"]     = "GK"
                        elif stat_key == "saves":
                            players[pid]["saves"]    = self.safe_int(val)
                            players[pid]["position"] = "GK"
                        elif stat_key == "yellow_cards":
                            players[pid]["yellow_cards"] = self.safe_int(val)
                        elif stat_key == "red_cards":
                            players[pid]["red_cards"] = self.safe_int(val)
            except Exception as e:
                logger.debug(f"[UCLPlayers] Stat {stat_key} error: {e}")

        # ── 2. TopPlayers bo sung neu chua co ────────────────────────
        overview = data.get("overview", {})
        for category, cat_data in overview.get("topPlayers", {}).items():
            if category == "seeAllUrl":
                continue
            for p in cat_data.get("players", []):
                pid = str(p.get("id", ""))
                if not pid:
                    continue
                if pid not in players:
                    players[pid] = _ucl_base(pid, self.SEASON, name=self.clean(p.get("name", "")))
                if category == "byGoals" and not players[pid].get("goals"):
                    players[pid]["goals"] = self.safe_int(p.get("goals", p.get("value", 0)))
                elif category == "byAssists" and not players[pid].get("assists"):
                    players[pid]["assists"] = self.safe_int(p.get("assists", p.get("value", 0)))
                elif category == "byRating" and not players[pid].get("average_rating"):
                    players[pid]["average_rating"] = self.safe_float(p.get("rating", p.get("value", 0)))

        # ── 3. Squad tu fixtures clubs ───────────────────────────────
        club_ids = set()
        for m in data.get("fixtures", {}).get("allMatches", []):
            h = m.get("home", {}).get("id")
            a = m.get("away", {}).get("id")
            if h: club_ids.add(str(h))
            if a: club_ids.add(str(a))

        for cid in list(club_ids)[:36]:
            self._fetch_squad_ucl(cid, players)

        results = list(players.values())
        logger.info(f"[UCLPlayers] Total {len(results)} players")
        return results

    def _fetch_squad_ucl(self, team_id: str, players: dict):
        try:
            data = self._get(f"https://www.fotmob.com/api/data/teams?id={team_id}")
            if not data:
                return
            squad_sections = data.get("squad", {}).get("squad", [])
            team_name = data.get("details", {}).get("name", "")

            for section in squad_sections:
                if section.get("title", "").lower() in ("coach", "coaches"):
                    continue
                for member in section.get("members", []):
                    pid = str(member.get("id", ""))
                    if not pid:
                        continue

                    # Tao moi neu chua co – dam bao league=UCL
                    if pid not in players:
                        players[pid] = _ucl_base(
                            pid, self.SEASON,
                            name=self.clean(member.get("name", "")),
                            team_id=team_id,
                            team_name=team_name,
                        )

                    # Cap nhat thong tin ca nhan
                    players[pid].update({
                        "league":        "UCL",  # dam bao luon dung
                        "name":          self.clean(member.get("name", players[pid].get("name", ""))),
                        "shirt_number":  self.safe_int(member.get("shirtNumber", 0)) or None,
                        "position":      self.map_position(member.get("role", {}).get("key", "")),
                        "nationality":   self.clean(member.get("ccode", "")),
                        "date_of_birth": self.clean(member.get("dateOfBirth", "")),
                        "height_cm":     self.safe_int(member.get("height", 0)) or None,
                        "team_source_id": team_id,
                        "team_name":     team_name,
                        "photo_url":     f"https://images.fotmob.com/image_resources/playerimages/{pid}.png",
                    })

                    # Cap nhat stats tu squad (lay tat ca, uu tien gia tri lon hon)
                    squad_goals   = self.safe_int(member.get("goals", 0))
                    squad_assists = self.safe_int(member.get("assists", 0))
                    squad_ycards  = self.safe_int(member.get("ycards", 0))
                    squad_rcards  = self.safe_int(member.get("rcards", 0))
                    squad_rating  = self.safe_float(member.get("rating") or 0.0)

                    if squad_goals > players[pid].get("goals", 0):
                        players[pid]["goals"] = squad_goals
                    if squad_assists > players[pid].get("assists", 0):
                        players[pid]["assists"] = squad_assists
                    if squad_ycards > players[pid].get("yellow_cards", 0):
                        players[pid]["yellow_cards"] = squad_ycards
                    if squad_rcards > players[pid].get("red_cards", 0):
                        players[pid]["red_cards"] = squad_rcards
                    if squad_rating and not players[pid].get("average_rating"):
                        players[pid]["average_rating"] = squad_rating

        except Exception as e:
            logger.debug(f"[UCLPlayers] Squad team {team_id}: {e}")