"""
app/models/statistic.py - Model thống kê cầu thủ & đội bóng
"""
from datetime import datetime, timezone
from app.extensions import db


class Statistic(db.Model):
    """
    Thống kê chi tiết theo cầu thủ - PL & UCL 2025/26.
    Mỗi record = 1 cầu thủ, 1 giải đấu, 1 mùa giải.
    """
    __tablename__ = "statistics"

    id = db.Column(db.Integer, primary_key=True)

    league = db.Column(db.String(10), nullable=False, index=True)
    season = db.Column(db.String(10), nullable=False, default="2025")

    # Cầu thủ
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    player = db.relationship("Player", back_populates="statistics")

    # CLB (có thể thay đổi giữa mùa)
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=True)
    club = db.relationship("Club", lazy="joined")

    # === Số liệu tấn công ===
    appearances = db.Column(db.Integer, default=0)
    starts = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    expected_goals = db.Column(db.Float, nullable=True)          # xG
    expected_assists = db.Column(db.Float, nullable=True)        # xA
    shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    big_chances_created = db.Column(db.Integer, default=0)
    big_chances_missed = db.Column(db.Integer, default=0)

    # === Chuyền bóng ===
    passes = db.Column(db.Integer, default=0)
    passes_completed = db.Column(db.Integer, default=0)
    pass_accuracy = db.Column(db.Float, nullable=True)           # %
    key_passes = db.Column(db.Integer, default=0)
    through_balls = db.Column(db.Integer, default=0)
    crosses = db.Column(db.Integer, default=0)

    # === Phòng thủ ===
    tackles = db.Column(db.Integer, default=0)
    tackles_won = db.Column(db.Integer, default=0)
    interceptions = db.Column(db.Integer, default=0)
    clearances = db.Column(db.Integer, default=0)
    blocks = db.Column(db.Integer, default=0)
    recoveries = db.Column(db.Integer, default=0)
    duels_won = db.Column(db.Integer, default=0)
    duels_lost = db.Column(db.Integer, default=0)
    aerial_duels_won = db.Column(db.Integer, default=0)

    # === Thủ môn (chỉ GK) ===
    saves = db.Column(db.Integer, nullable=True)
    save_percentage = db.Column(db.Float, nullable=True)         # %
    clean_sheets = db.Column(db.Integer, nullable=True)
    goals_conceded = db.Column(db.Integer, nullable=True)
    penalties_saved = db.Column(db.Integer, nullable=True)
    punches = db.Column(db.Integer, nullable=True)
    high_claims = db.Column(db.Integer, nullable=True)

    # === Kỷ luật ===
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    fouls_committed = db.Column(db.Integer, default=0)
    fouls_won = db.Column(db.Integer, default=0)
    offsides = db.Column(db.Integer, default=0)
    penalties_won = db.Column(db.Integer, default=0)
    penalties_conceded = db.Column(db.Integer, default=0)

    # === Rating ===
    average_rating = db.Column(db.Float, nullable=True)

    # Timestamps
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("player_id", "league", "season", name="uq_stat_player_league_season"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "league": self.league,
            "season": self.season,
            "player_id": self.player_id,
            "player_name": self.player.name if self.player else None,
            "player_photo": self.player.photo_url if self.player else None,
            "player_position": self.player.position if self.player else None,
            "club_id": self.club_id,
            "club_name": self.club.name if self.club else None,
            "club_badge": self.club.badge_url if self.club else None,
            # Attack
            "appearances": self.appearances,
            "starts": self.starts,
            "minutes_played": self.minutes_played,
            "goals": self.goals,
            "assists": self.assists,
            "expected_goals": self.expected_goals,
            "expected_assists": self.expected_assists,
            "shots": self.shots,
            "shots_on_target": self.shots_on_target,
            "big_chances_created": self.big_chances_created,
            # Passing
            "passes": self.passes,
            "pass_accuracy": self.pass_accuracy,
            "key_passes": self.key_passes,
            # Defence
            "tackles": self.tackles,
            "interceptions": self.interceptions,
            "clearances": self.clearances,
            "duels_won": self.duels_won,
            # GK
            "saves": self.saves,
            "save_percentage": self.save_percentage,
            "clean_sheets": self.clean_sheets,
            # Discipline
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "fouls_committed": self.fouls_committed,
            # Rating
            "average_rating": self.average_rating,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        name = self.player.name if self.player else self.player_id
        return f"<Statistic {name} [{self.league} {self.season}]>"


class TeamStatistic(db.Model):
    """
    Thống kê tổng hợp theo đội bóng - PL & UCL 2025/26
    """
    __tablename__ = "team_statistics"

    id = db.Column(db.Integer, primary_key=True)

    league = db.Column(db.String(10), nullable=False, index=True)
    season = db.Column(db.String(10), nullable=False, default="2025")

    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=False)
    club = db.relationship("Club", lazy="joined")

    # Tấn công
    goals_scored = db.Column(db.Integer, default=0)
    goals_conceded = db.Column(db.Integer, default=0)
    clean_sheets = db.Column(db.Integer, default=0)
    shots = db.Column(db.Integer, default=0)
    shots_on_target = db.Column(db.Integer, default=0)
    expected_goals = db.Column(db.Float, nullable=True)
    possession_avg = db.Column(db.Float, nullable=True)     # % trung bình

    # Chuyền
    passes_per_game = db.Column(db.Float, nullable=True)
    pass_accuracy = db.Column(db.Float, nullable=True)

    # Kỷ luật
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    fouls = db.Column(db.Integer, default=0)

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("club_id", "league", "season", name="uq_teamstat_club_league_season"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "league": self.league,
            "season": self.season,
            "club_id": self.club_id,
            "club_name": self.club.name if self.club else None,
            "club_badge": self.club.badge_url if self.club else None,
            "goals_scored": self.goals_scored,
            "goals_conceded": self.goals_conceded,
            "clean_sheets": self.clean_sheets,
            "shots": self.shots,
            "shots_on_target": self.shots_on_target,
            "expected_goals": self.expected_goals,
            "possession_avg": self.possession_avg,
            "passes_per_game": self.passes_per_game,
            "pass_accuracy": self.pass_accuracy,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
