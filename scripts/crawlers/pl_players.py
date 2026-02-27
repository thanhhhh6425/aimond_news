"""
scripts/crawlers/pl_players.py
Cao cu thu Premier League tu FotMob.

Nguon du lieu:
  1. data.fotmob.com/stats/47/season/27110/*.json  -> stats tung cau thu
  2. fotmob.com/api/teams?id=<id>                  -> squad + thong tin ca nhan
  3. overview.topPlayers                            -> top goals/assists/rating
"""
from typing import Dict, List, Optional
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging

logger = logging.getLogger(__name__)

# PL season ID 2025/26
PL_SEASON_ID = 27110
PL_LEAGUE_ID = 47

# Cac stat URLs can fetch
# Position codes FotMob -> DB
# Positions list: 103=GK, 104=DEF, 105=MID, 106=FWD, 83=LW, 85=RW, etc.
GK_POSITIONS = {103}  # FotMob position IDs cho thu mon

STAT_URLS = [
    ("goals",        f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/goals.json"),
    ("assists",      f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/goal_assist.json"),
    ("rating",       f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/rating.json"),
    ("mins_played",  f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/mins_played.json"),
    ("clean_sheets", f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/clean_sheet.json"),
    ("saves",        f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/saves.json"),
    ("yellow_cards", f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/yellow_card.json"),
    ("red_cards",    f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/red_card.json"),
    ("xg",           f"https://data.fotmob.com/stats/{PL_LEAGUE_ID}/season/{PL_SEASON_ID}/expected_goals.json"),
    # appearances bi 403, dung MatchesPlayed tu goals thay the
]


class PLPlayersCrawler(BaseFotMobCrawler):
    LEAGUE = "PL"

    def parse(self, data: Dict) -> List[Dict]:
        """Parse tu leagues API - lay danh sach club IDs va topPlayers."""
        players: Dict[str, Dict] = {}

        # ── 1. Fetch stats URLs truoc (co du lieu chinh xac nhat) ────
        for stat_key, url in STAT_URLS:
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

                        # Luu Positions de xac dinh vi tri
                        positions = entry.get("Positions", [])
                        if positions and not players[pid].get("_positions"):
                            players[pid]["_positions"] = positions
                            pos_id = positions[0] if positions else 0
                            # FotMob position IDs (tu debug thuc te):
                            # GK=11
                            # DEF=32-38,51,59,62,71 (cb, lb, rb, wb)
                            # MID=64-82 (dm, cm, am, wm)
                            # FWD=83-88,103-107,115 (winger, forward, striker)
                            if pos_id == 11:
                                players[pid]["position"] = "GK"
                            elif pos_id in range(32, 72):
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
                                players[pid]["appearances"]    = self.safe_int(entry.get("MatchesPlayed", 0))
                        elif stat_key == "clean_sheets":
                            # Chi set cho thu mon (position GK)
                            cur_pos = players[pid].get("position", "")
                            if cur_pos == "GK" or not cur_pos:
                                players[pid]["clean_sheets"] = self.safe_int(val)
                                players[pid]["position"]     = "GK"
                        elif stat_key == "saves":
                            players[pid]["saves"]          = self.safe_int(val)
                            players[pid]["position"]       = "GK"  # saves chi co GK
                        elif stat_key == "yellow_cards":
                            players[pid]["yellow_cards"]   = self.safe_int(val)
                        elif stat_key == "red_cards":
                            players[pid]["red_cards"]      = self.safe_int(val)
                        elif stat_key == "xg":
                            players[pid]["expected_goals"] = self.safe_float(val)
            except Exception as e:
                logger.debug(f"[PLPlayers] Stat {stat_key} error: {e}")

        # ── 2. TopPlayers tu overview (chi bo sung neu chua co) ──────
        overview = data.get("overview", {})
        top = overview.get("topPlayers", {})
        for category, cat_data in top.items():
            if category == "seeAllUrl":
                continue
            for p in cat_data.get("players", []):
                pid = str(p.get("id", ""))
                if not pid:
                    continue
                if pid not in players:
                    players[pid] = self._base_player(pid, p)
                # Chi set neu chua co tu StatList
                if category == "byGoals" and not players[pid].get("goals"):
                    players[pid]["goals"] = self.safe_int(p.get("goals", p.get("value", 0)))
                elif category == "byAssists" and not players[pid].get("assists"):
                    players[pid]["assists"] = self.safe_int(p.get("assists", p.get("value", 0)))
                elif category == "byRating" and not players[pid].get("average_rating"):
                    players[pid]["average_rating"] = self.safe_float(p.get("rating", p.get("value", 0)))

        # ── 3. Fetch squad tu tung club (cap nhat thong tin ca nhan) ─
        table = data.get("table", [])
        club_ids = set()
        for section in table:
            rows = section.get("data", {}).get("table", {}).get("all", [])
            for row in rows:
                cid = row.get("id")
                if cid:
                    club_ids.add(str(cid))

        for cid in list(club_ids)[:20]:
            self._fetch_squad(cid, players)

        results = list(players.values())
        logger.info(f"[PLPlayers] Total {len(results)} players")
        return results

    def _fetch_squad(self, team_id: str, players: dict):
        """Fetch squad cua 1 doi va cap nhat thong tin ca nhan."""
        try:
            data = self._get(f"https://www.fotmob.com/api/teams?id={team_id}")
            if not data:
                return
            squad_sections = data.get("squad", {}).get("squad", [])
            team_name = data.get("details", {}).get("name", "")
            for section in squad_sections:
                title = section.get("title", "").lower()
                if title in ("coach", "coaches"):
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
                    # Cap nhat thong tin ca nhan
                    players[pid].update({
                        "name": self.clean(member.get("name", players[pid].get("name",""))),
                        "shirt_number": self.safe_int(member.get("shirtNumber", 0)) or None,
                        "position": self.map_position(member.get("role", {}).get("key", "")),
                        "nationality": self.clean(member.get("ccode", "")),
                        "date_of_birth": self.clean(member.get("dateOfBirth", "")),
                        "height_cm": self.safe_int(member.get("height", 0)) or None,
                        "team_source_id": team_id,
                        "team_name": team_name,
                        "photo_url": f"https://images.fotmob.com/image_resources/playerimages/{pid}.png",
                    })
        except Exception as e:
            logger.debug(f"[PLPlayers] Squad fetch error team {team_id}: {e}")

    def _base_player(self, pid: str, entry: Dict) -> Dict:
        return {
            "league": "PL",
            "season": self.SEASON,
            "source_id": pid,
            "name": self.clean(entry.get("name", entry.get("playerName", ""))),
            "team_source_id": str(entry.get("teamId", "")),
            "team_name": self.clean(entry.get("teamName", "")),
            "position": "FWD",
            "nationality": self.clean(entry.get("ccode", "")),
            "photo_url": f"https://images.fotmob.com/image_resources/playerimages/{pid}.png",
            "goals": 0, "assists": 0, "saves": 0, "clean_sheets": 0,
            "yellow_cards": 0, "red_cards": 0, "appearances": 0,
            "minutes_played": 0, "average_rating": 0.0, "expected_goals": 0.0,
            "shirt_number": None, "date_of_birth": "", "height_cm": None,
        }

    def _base_player_from_stat(self, pid: str, entry: Dict) -> Dict:
        return {
            "league": "PL",
            "season": self.SEASON,
            "source_id": pid,
            "name": self.clean(entry.get("ParticipantName", "")),
            "team_source_id": str(entry.get("TeamId", "")),
            "team_name": "",
            "position": "FWD",
            "nationality": "",
            "photo_url": f"https://images.fotmob.com/image_resources/playerimages/{pid}.png",
            "goals": 0, "assists": 0, "saves": 0, "clean_sheets": 0,
            "yellow_cards": 0, "red_cards": 0, "appearances": 0,
            "minutes_played": 0, "average_rating": 0.0, "expected_goals": 0.0,
            "shirt_number": None, "date_of_birth": "", "height_cm": None,
        }