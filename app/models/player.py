"""
app/models/player.py - Model cầu thủ
"""
from datetime import datetime, timezone
from app.extensions import db


class Player(db.Model):
    """
    Hồ sơ và thông tin chi tiết cầu thủ - PL & UCL 2025/26
    """
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)

    # Định danh từ nguồn cào
    source_id = db.Column(db.String(50), nullable=True, index=True)
    league = db.Column(db.String(10), nullable=False, index=True)   # 'PL' | 'UCL'
    season = db.Column(db.String(10), nullable=False, default="2025")

    # Liên kết CLB
    club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=True)
    club = db.relationship("Club", back_populates="players")

    # Thông tin cơ bản
    name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    nationality = db.Column(db.String(50), nullable=True)
    position = db.Column(db.String(30), nullable=True)   # GK, DEF, MID, FWD
    shirt_number = db.Column(db.Integer, nullable=True)

    # Hình ảnh
    photo_url = db.Column(db.String(500), nullable=True)
    flag_url = db.Column(db.String(500), nullable=True)

    # Thể chất
    height_cm = db.Column(db.Integer, nullable=True)
    weight_kg = db.Column(db.Integer, nullable=True)
    foot = db.Column(db.String(10), nullable=True)  # 'left' | 'right' | 'both'

    # Timestamps
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    statistics = db.relationship("Statistic", back_populates="player", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("source_id", "league", "season", name="uq_player_source_league_season"),
    )

    @property
    def age(self):
        if self.date_of_birth:
            today = datetime.now(timezone.utc).date()
            d = self.date_of_birth
            return today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        return None

    @property
    def age_detail(self):
        """Tinh tuoi chinh xac: X tuoi Y ngay."""
        if not self.date_of_birth:
            return None
        try:
            today = datetime.now(timezone.utc).date()
            d = self.date_of_birth
            years = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
            # Handle Feb 29 (leap day birthday)
            try:
                bday = d.replace(year=today.year)
            except ValueError:
                bday = d.replace(year=today.year, day=28)
            if bday > today:
                try:
                    bday = d.replace(year=today.year - 1)
                except ValueError:
                    bday = d.replace(year=today.year - 1, day=28)
            days = (today - bday).days
            return {"years": years, "days": days, "display": f"{years} tuoi, {days} ngay"}
        except Exception:
            return None

    def to_dict(self, include_stats=False):
        data = {
            "id": self.id,
            "source_id": self.source_id,
            "league": self.league,
            "season": self.season,
            "club_id": self.club_id,
            "club_name": self.club.name if self.club else None,
            "club_badge": self.club.badge_url if self.club else None,
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "age_detail": self.age_detail,
            "nationality": self.nationality,
            "position": self.position,
            "shirt_number": self.shirt_number,
            "photo_url": self.photo_url,
            "flag_url": self.flag_url,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "foot": self.foot,
        }
        if include_stats:
            data["statistics"] = [s.to_dict() for s in self.statistics.all()]
        return data

    def __repr__(self):
        return f"<Player {self.name} [{self.league}]>"