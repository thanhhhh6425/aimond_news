"""
app/models/standing.py - Model bảng xếp hạng
"""
from datetime import datetime, timezone
from app.extensions import db


class Standing(db.Model):
    """
    Bảng xếp hạng Premier League & Champions League 2025/26.
    Mỗi row là 1 đội trong 1 mùa giải / vòng bảng cụ thể.
    """
    __tablename__ = "standings"

    id = db.Column(db.Integer, primary_key=True)

    league = db.Column(db.String(10), nullable=False, index=True)   # 'PL' | 'UCL'
    season = db.Column(db.String(10), nullable=False, default="2025", index=True)

    # UCL có thể có nhiều bảng (group A, B, C...)
    group = db.Column(db.String(5), nullable=True, index=True)   # None = tổng, 'A'..'H'
    stage = db.Column(db.String(50), nullable=True)              # 'League Phase', 'Knockout'

    # Đội bóng
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=True)
    club = db.relationship("Club", lazy="joined")
    team_name = db.Column(db.String(100), nullable=False)
    team_badge = db.Column(db.String(500), nullable=True)
    team_short = db.Column(db.String(20), nullable=True)

    # Vị trí
    position = db.Column(db.Integer, nullable=False)
    form = db.Column(db.String(20), nullable=True)      # Ví dụ: "WWDLW"

    # Thống kê thi đấu
    played = db.Column(db.Integer, default=0)
    won = db.Column(db.Integer, default=0)
    drawn = db.Column(db.Integer, default=0)
    lost = db.Column(db.Integer, default=0)

    # Bàn thắng
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    goal_difference = db.Column(db.Integer, default=0)

    # Điểm số
    points = db.Column(db.Integer, default=0)

    # Vị trí nổi bật (để tô màu)
    # 'champions_league' | 'europa' | 'conference' | 'relegation' | None
    status = db.Column(db.String(30), nullable=True)

    # Timestamps
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "league", "season", "group", "club_id",
            name="uq_standing_league_season_group_club"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "league": self.league,
            "season": self.season,
            "group": self.group,
            "stage": self.stage,
            "position": self.position,
            "team": {
                "id": self.club_id,
                "name": self.team_name,
                "badge": self.team_badge,
                "short": self.team_short,
            },
            "form": self.form,
            "played": self.played,
            "won": self.won,
            "drawn": self.drawn,
            "lost": self.lost,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "goal_difference": self.goal_difference,
            "points": self.points,
            "status": self.status,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Standing {self.position}. {self.team_name} [{self.league} {self.season}]>"
