"""
app/models/club.py - Model câu lạc bộ
"""
from datetime import datetime, timezone
from app.extensions import db


class Club(db.Model):
    """
    Thông tin câu lạc bộ - PL & UCL 2025/26
    """
    __tablename__ = "clubs"

    id = db.Column(db.Integer, primary_key=True)

    # Định danh từ nguồn cào
    source_id = db.Column(db.String(50), nullable=True)  # ID từ PL.com/UEFA.com
    league = db.Column(db.String(10), nullable=False, index=True)  # 'PL' | 'UCL'
    season = db.Column(db.String(10), nullable=False, default="2025", index=True)

    # Thông tin cơ bản
    name = db.Column(db.String(100), nullable=False)
    short_name = db.Column(db.String(20), nullable=True)       # Ví dụ: MCI, ARS
    full_name = db.Column(db.String(150), nullable=True)
    founded = db.Column(db.Integer, nullable=True)
    country = db.Column(db.String(50), nullable=True)

    # Hình ảnh
    badge_url = db.Column(db.String(500), nullable=True)
    stadium_image_url = db.Column(db.String(500), nullable=True)

    # Sân vận động
    stadium_name = db.Column(db.String(100), nullable=True)
    stadium_capacity = db.Column(db.Integer, nullable=True)
    stadium_city = db.Column(db.String(100), nullable=True)

    # Thông tin CLB
    manager = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)

    # Timestamps
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    players = db.relationship("Player", back_populates="club", lazy="dynamic")
    home_matches = db.relationship(
        "Match", foreign_keys="Match.home_club_id",
        back_populates="home_club", lazy="dynamic"
    )
    away_matches = db.relationship(
        "Match", foreign_keys="Match.away_club_id",
        back_populates="away_club", lazy="dynamic"
    )

    __table_args__ = (
        db.UniqueConstraint("source_id", "league", "season", name="uq_club_source_league_season"),
    )

    def to_dict(self, include_players=False):
        data = {
            "id": self.id,
            "source_id": self.source_id,
            "league": self.league,
            "season": self.season,
            "name": self.name,
            "short_name": self.short_name,
            "full_name": self.full_name,
            "founded": self.founded,
            "country": self.country,
            "badge_url": self.badge_url,
            "stadium_name": self.stadium_name,
            "stadium_capacity": self.stadium_capacity,
            "stadium_city": self.stadium_city,
            "manager": self.manager,
            "website": self.website,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_players:
            data["players"] = [p.to_dict() for p in self.players.all()]
        return data

    def __repr__(self):
        return f"<Club {self.name} [{self.league}]>"
