"""
scripts/utils/db_writer.py - Ghi du lieu vao database
Viet lai hoan toan: don gian, ro rang, khong bug.
"""
import logging
from datetime import datetime, timezone, date
from typing import Dict, List

logger = logging.getLogger(__name__)


class DBWriter:
    def __init__(self):
        pass

    def upsert_clubs(self, records: List[Dict], league: str = "PL") -> int:
        from app.extensions import db
        from app.models import Club
        count = 0
        for r in records:
            try:
                source_id = str(r.get("source_id", "")).strip()
                r_league  = r.get("league", league)
                r_season  = r.get("season", "2025")
                if not source_id:
                    continue
                club = Club.query.filter_by(source_id=source_id, league=r_league).first()
                if not club:
                    club = Club(source_id=source_id, league=r_league, season=r_season)
                    db.session.add(club)
                club.league = r_league; club.season = r_season
                club.name = r.get("name",""); club.short_name = r.get("short_name","")
                club.country = r.get("country",""); club.badge_url = r.get("badge_url","")
                club.stadium_name = r.get("stadium_name",""); club.stadium_city = r.get("stadium_city","")
                club.stadium_capacity = r.get("stadium_capacity") or None
                club.manager = r.get("manager","")
                db.session.flush(); count += 1
            except Exception as e:
                logger.error(f"[DBWriter.clubs] {e}"); db.session.rollback()
        db.session.commit()
        logger.info(f"[DBWriter] Clubs upserted: {count}")
        return count

    def upsert_standings(self, records: List[Dict], league: str = "PL") -> int:
        from app.extensions import db
        from app.models import Club, Standing
        clubs = {c.source_id: c for c in Club.query.filter_by(league=league).all()}
        count = 0
        for r in records:
            try:
                source_id = str(r.get("source_id","")).strip()
                season = r.get("season","2025")
                if not source_id: continue
                club = clubs.get(source_id)
                if not club:
                    # Tao club don gian voi name tu standings record
                    club = Club(
                        source_id=source_id, league=league, season=season,
                        name=r.get("team_name",""), short_name=r.get("team_short",""),
                        badge_url=r.get("badge_url","")
                    )
                    db.session.add(club); db.session.flush()
                    clubs[source_id] = club
                else:
                    if not club.name: club.name = r.get("team_name","")
                    if not club.badge_url: club.badge_url = r.get("badge_url","")
                db.session.flush()
                st = Standing.query.filter_by(club_id=club.id, league=league, season=season).first()
                if not st:
                    st = Standing(club_id=club.id, league=league, season=season)
                    db.session.add(st)
                st.team_name=r.get("team_name",""); st.team_short=r.get("team_short","")
                st.team_badge=club.badge_url or r.get("badge_url","")
                st.position=r.get("position",0); st.group=r.get("group_name","")
                st.stage=r.get("group_name","League Phase")
                st.played=r.get("played",0); st.won=r.get("won",0)
                st.drawn=r.get("drawn",0); st.lost=r.get("lost",0)
                st.goals_for=r.get("goals_for",0); st.goals_against=r.get("goals_against",0)
                st.goal_difference=r.get("goal_difference",0); st.points=r.get("points",0)
                st.form=r.get("form",""); st.status=r.get("status","normal")
                st.updated_at=datetime.now(timezone.utc); count += 1
            except Exception as e:
                logger.error(f"[DBWriter.standings] {e}"); db.session.rollback()
        db.session.commit()
        logger.info(f"[DBWriter] Standings upserted: {count}")
        return count

    def upsert_matches(self, records: List[Dict], league: str = "PL") -> int:
        from app.extensions import db
        from app.models import Club, Match
        clubs = {c.source_id: c for c in Club.query.filter_by(league=league).all()}
        count = 0
        for r in records:
            try:
                # Match model dung source_id, home_team_name, kickoff_at
                source_id = str(r.get("source_id", r.get("match_id",""))).strip()
                season = r.get("season","2025")
                if not source_id: continue
                home_club = clubs.get(str(r.get("home_source_id","")))
                away_club = clubs.get(str(r.get("away_source_id","")))
                m = Match.query.filter_by(source_id=source_id, league=league).first()
                if not m:
                    m = Match(source_id=source_id, league=league, season=season)
                    db.session.add(m)
                m.league          = league
                m.season          = season
                m.home_club_id    = home_club.id if home_club else None
                m.away_club_id    = away_club.id if away_club else None
                m.home_team_name  = r.get("home_team_name", r.get("home_team",""))
                m.away_team_name  = r.get("away_team_name", r.get("away_team",""))
                m.home_team_badge = r.get("home_badge","")
                m.away_team_badge = r.get("away_badge","")
                m.home_score      = r.get("home_score")
                m.away_score      = r.get("away_score")
                m.status          = r.get("status","SCHEDULED")
                m.kickoff_at      = r.get("kickoff_at") or r.get("kickoff_utc")
                m.matchweek       = r.get("matchweek") or r.get("round_num")
                m.round           = r.get("round_name","")
                m.venue           = r.get("venue","")
                m.home_score_pen  = r.get("home_score_pen")
                m.away_score_pen  = r.get("away_score_pen")
                count += 1
            except Exception as e:
                logger.error(f"[DBWriter.matches] {e} | {r.get('source_id')}")
                db.session.rollback()
        db.session.commit()
        logger.info(f"[DBWriter] Matches upserted: {count}")
        return count

    def upsert_players(self, records: List[Dict], league: str = "PL") -> int:
        from app.extensions import db
        from app.models import Player, Club, Statistic

        clubs = {c.source_id: c for c in Club.query.filter_by(league=league).all()}
        existing = {p.source_id: p for p in Player.query.filter_by(league=league, season="2025").all()}

        count = 0
        for i, r in enumerate(records):
            try:
                source_id = str(r.get("source_id","")).strip()
                p_league  = r.get("league", league)
                p_season  = r.get("season","2025")
                name      = r.get("name","").strip()
                if not source_id or not name:
                    continue

                club = clubs.get(str(r.get("team_source_id","")))

                # Player
                player = existing.get(source_id)
                if not player:
                    player = Player(source_id=source_id, league=p_league, season=p_season)
                    db.session.add(player)
                    existing[source_id] = player

                player.name         = name
                player.league       = p_league
                player.season       = p_season
                player.club_id      = club.id if club else None
                player.position     = r.get("position","FWD")
                player.nationality  = r.get("nationality","")
                player.photo_url    = r.get("photo_url","")
                player.shirt_number = r.get("shirt_number") or None
                player.height_cm    = r.get("height_cm") or None

                dob = r.get("date_of_birth","")
                if dob and isinstance(dob, str) and len(dob) >= 10:
                    try: player.date_of_birth = date.fromisoformat(dob[:10])
                    except: pass

                db.session.flush()

                # Statistic - 1 record per player+league+season
                stat = Statistic.query.filter_by(
                    player_id=player.id, league=p_league, season=p_season
                ).first()
                if not stat:
                    stat = Statistic(player_id=player.id, league=p_league, season=p_season,
                                     club_id=club.id if club else None)
                    db.session.add(stat)

                stat.club_id        = club.id if club else None
                stat.goals          = int(r.get("goals") or 0)
                stat.assists        = int(r.get("assists") or 0)
                stat.appearances    = int(r.get("appearances") or 0)
                stat.minutes_played = int(r.get("minutes_played") or 0)
                stat.yellow_cards   = int(r.get("yellow_cards") or 0)
                stat.red_cards      = int(r.get("red_cards") or 0)
                stat.saves          = int(r["saves"]) if r.get("saves") else None
                stat.clean_sheets   = int(r["clean_sheets"]) if r.get("clean_sheets") else None
                stat.expected_goals = float(r["expected_goals"]) if r.get("expected_goals") else None
                stat.average_rating = float(r["average_rating"]) if r.get("average_rating") else None
                count += 1

                if (i+1) % 100 == 0:
                    db.session.commit()

            except Exception as e:
                logger.error(f"[DBWriter.players] {e} | {r.get('source_id')} {r.get('name')}")
                db.session.rollback()
                existing = {p.source_id: p for p in Player.query.filter_by(league=league, season="2025").all()}

        try:
            db.session.commit()
        except Exception as e:
            logger.error(f"[DBWriter.players] final commit: {e}"); db.session.rollback()

        logger.info(f"[DBWriter] Players upserted: {count}")
        return count

    def upsert_news(self, records: List[Dict], league: str = "PL") -> int:
        from app.extensions import db
        from app.models import News
        count = 0
        for r in records:
            try:
                source_id = str(r.get("source_id","")).strip()
                if not source_id: continue
                news = News.query.filter_by(source_id=source_id).first()
                if not news:
                    news = News(source_id=source_id); db.session.add(news)
                news.league=league; news.title=r.get("title","")
                news.summary=r.get("summary",""); news.url=r.get("url","")
                news.image_url=r.get("image_url",""); news.published_at=r.get("published_at")
                news.category=r.get("category",""); news.source=r.get("source","")
                count += 1
            except Exception as e:
                logger.error(f"[DBWriter.news] {e}"); db.session.rollback()
        db.session.commit()
        logger.info(f"[DBWriter] News upserted: {count}")
        return count