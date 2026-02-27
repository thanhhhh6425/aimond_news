"""
scripts/crawlers/ucl_players.py
Cao cu thu Champions League - UCL 2025/26 (season 28184) va 2024/25 (season 24110).
"""
from typing import Dict, List
from scripts.crawlers.pl_players import PLPlayersCrawler
import logging

logger = logging.getLogger(__name__)

UCL_SEASON_ID = 28184   # 2025/26
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
    # appearances bi 403
]


class UCLPlayersCrawler(PLPlayersCrawler):
    LEAGUE = "UCL"

    def parse(self, data: Dict) -> List[Dict]:
        players = {}

        # 1. TopPlayers (chi lam nguon du phong, stats URLs chinh xac hon)
        # Chay sau stats URLs nen move xuong duoi - giu lai de lay rating
        _top_cache = {}
        overview = data.get("overview", {})
        top = overview.get("topPlayers", {})
        for category, cat_data in top.items():
            if category == "seeAllUrl":
                continue
            for p in cat_data.get("players", []):
                pid = str(p.get("id", ""))
                if pid:
                    _top_cache[pid] = (category, p)

        # 2. Stats URLs UCL
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
                            players[pid] = self._base_player_from_stat(pid, entry)
                        # Cap nhat name/team neu chua co
                        if not players[pid].get("name"):
                            players[pid]["name"] = self.clean(entry.get("ParticipantName",""))
                        if not players[pid].get("team_source_id"):
                            players[pid]["team_source_id"] = str(entry.get("TeamId",""))
                            players[pid]["team_name"] = self.clean(entry.get("TeamName",""))
                        # Luon update name/team neu chua co
                        if not players[pid].get("name"):
                            players[pid]["name"] = self.clean(entry.get("ParticipantName",""))
                        if not players[pid].get("team_source_id"):
                            players[pid]["team_source_id"] = str(entry.get("TeamId",""))
                            players[pid]["team_name"] = self.clean(entry.get("TeamName",""))
                            players[pid]["league"] = "UCL"

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
                            cur_pos = players[pid].get("position", "")
                            if cur_pos == "GK" or not cur_pos:
                                players[pid]["clean_sheets"] = self.safe_int(val)
                                players[pid]["position"]     = "GK"
                        elif stat_key == "saves":
                            players[pid]["saves"]          = self.safe_int(val)
                            players[pid]["position"]       = "GK"
                        elif stat_key == "yellow_cards":
                            players[pid]["yellow_cards"]   = self.safe_int(val)
                        elif stat_key == "red_cards":
                            players[pid]["red_cards"]      = self.safe_int(val)
            except Exception as e:
                logger.debug(f"[UCLPlayers] Stat {stat_key} error: {e}")

        # Apply top cache - chi bo sung neu chua co tu StatList
        for pid, (category, p) in _top_cache.items():
            if pid not in players:
                players[pid] = self._base_player(pid, p)
                players[pid]["league"] = "UCL"
            if category == "byGoals" and not players[pid].get("goals"):
                players[pid]["goals"] = self.safe_int(p.get("goals", p.get("value", 0)))
            elif category == "byAssists" and not players[pid].get("assists"):
                players[pid]["assists"] = self.safe_int(p.get("assists", p.get("value", 0)))
            elif category == "byRating" and not players[pid].get("average_rating"):
                players[pid]["average_rating"] = self.safe_float(p.get("rating", p.get("value", 0)))

        # 3. Squad tu fixtures clubs
        fixtures = data.get("fixtures", {})
        club_ids = set()
        for m in fixtures.get("allMatches", []):
            home_id = m.get("home", {}).get("id")
            away_id = m.get("away", {}).get("id")
            if home_id: club_ids.add(str(home_id))
            if away_id: club_ids.add(str(away_id))

        for cid in list(club_ids)[:36]:
            self._fetch_squad_ucl(cid, players)

        results = list(players.values())
        logger.info(f"[UCLPlayers] Total {len(results)} players")
        return results

    def _fetch_squad_ucl(self, team_id: str, players: dict):
        try:
            data = self._get(f"https://www.fotmob.com/api/teams?id={team_id}")
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
                    if pid not in players:
                        players[pid] = self._base_player(pid, {
                            "name": member.get("name", ""),
                            "teamId": team_id,
                            "teamName": team_name,
                        })
                        players[pid]["league"] = "UCL"
                    players[pid].update({
                        "name":          self.clean(member.get("name", players[pid].get("name",""))),
                        "shirt_number":  self.safe_int(member.get("shirtNumber", 0)) or None,
                        "position":      self.map_position(member.get("role", {}).get("key", "")),
                        "nationality":   self.clean(member.get("ccode", "")),
                        "date_of_birth": self.clean(member.get("dateOfBirth", "")),
                        "height_cm":     self.safe_int(member.get("height", 0)) or None,
                        "team_source_id": team_id,
                        "team_name":     team_name,
                        "photo_url":     f"https://images.fotmob.com/image_resources/playerimages/{pid}.png",
                    })
        except Exception as e:
            logger.debug(f"[UCLPlayers] Squad team {team_id}: {e}")