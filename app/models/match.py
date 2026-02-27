"""
app/models/match.py - Model trận đấu & kết quả
"""
from datetime import datetime, timezone
from app.extensions import db


class Match(db.Model):
    """
    Lịch thi đấu và kết quả - PL & UCL 2025/26
    Tự động cập nhật sau khi trận kết thúc qua Scheduler.
    """
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)

    # Định danh từ nguồn cào
    source_id = db.Column(db.String(100), nullable=True, unique=True, index=True)
    league = db.Column(db.String(10), nullable=False, index=True)   # 'PL' | 'UCL'
    season = db.Column(db.String(10), nullable=False, default="2025")

    # Vòng đấu
    matchweek = db.Column(db.Integer, nullable=True)          # PL gameweek
    round = db.Column(db.String(50), nullable=True)           # UCL round (e.g. "Group Stage")
    group = db.Column(db.String(5), nullable=True)            # UCL group (e.g. "A")

    # Đội bóng
    home_club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=True)
    away_club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=True)
    home_club = db.relationship("Club", foreign_keys=[home_club_id], back_populates="home_matches")
    away_club = db.relationship("Club", foreign_keys=[away_club_id], back_populates="away_matches")

    # Tên đội (backup nếu chưa có Club record)
    home_team_name = db.Column(db.String(100), nullable=True)
    away_team_name = db.Column(db.String(100), nullable=True)
    home_team_badge = db.Column(db.String(500), nullable=True)
    away_team_badge = db.Column(db.String(500), nullable=True)

    # Thời gian thi đấu
    kickoff_at = db.Column(db.DateTime, nullable=True, index=True)
    kickoff_at_utc = db.Column(db.DateTime, nullable=True)

    # Trạng thái trận đấu
    STATUS_SCHEDULED = "SCHEDULED"
    STATUS_LIVE = "LIVE"
    STATUS_HT = "HT"
    STATUS_FT = "FT"
    STATUS_POSTPONED = "POSTPONED"
    STATUS_CANCELLED = "CANCELLED"

    status = db.Column(db.String(20), default="SCHEDULED", nullable=False, index=True)
    minute = db.Column(db.Integer, nullable=True)    # Phút thi đấu (khi LIVE)

    # Kết quả
    home_score = db.Column(db.Integer, nullable=True)
    away_score = db.Column(db.Integer, nullable=True)
    home_score_ht = db.Column(db.Integer, nullable=True)   # Half time
    away_score_ht = db.Column(db.Integer, nullable=True)
    home_score_et = db.Column(db.Integer, nullable=True)   # Extra time
    away_score_et = db.Column(db.Integer, nullable=True)
    home_score_pen = db.Column(db.Integer, nullable=True)  # Penalties
    away_score_pen = db.Column(db.Integer, nullable=True)

    # Sân vận động
    venue = db.Column(db.String(100), nullable=True)
    venue_city = db.Column(db.String(50), nullable=True)

    # Metadata
    broadcast = db.Column(db.String(100), nullable=True)  # Đài truyền hình
    attendance = db.Column(db.Integer, nullable=True)
    referee = db.Column(db.String(100), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Events (goals, cards) lưu dạng JSON text
    # UCL knockout fields
    is_knockout    = db.Column(db.Boolean, default=False)
    leg            = db.Column(db.Integer, nullable=True)   # 1=luot di, 2=luot ve
    agg_home       = db.Column(db.Integer, nullable=True)   # Tong 2 luot home
    agg_away       = db.Column(db.Integer, nullable=True)   # Tong 2 luot away
    ended_aet      = db.Column(db.Boolean, default=False)   # Ket thuc sau hiep phu
    ended_pen      = db.Column(db.Boolean, default=False)   # Ket thuc sau penalty

    events_json = db.Column(db.Text, nullable=True)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "source_id": self.source_id,
            "league": self.league,
            "season": self.season,
            "matchweek": self.matchweek,
            "round": self.round,
            "group": self.group,
            "home_team": {
                "id": self.home_club_id,
                "name": self.home_team_name or (self.home_club.name if self.home_club else None),
                "badge": self.home_team_badge or (self.home_club.badge_url if self.home_club else None),
                "score": self.home_score,
                "score_ht": self.home_score_ht,
            },
            "away_team": {
                "id": self.away_club_id,
                "name": self.away_team_name or (self.away_club.name if self.away_club else None),
                "badge": self.away_team_badge or (self.away_club.badge_url if self.away_club else None),
                "score": self.away_score,
                "score_ht": self.away_score_ht,
            },
            "kickoff_at": self.kickoff_at.isoformat() if self.kickoff_at else None,
            "status": self.status,
            "minute": self.minute,
            "venue": self.venue,
            "venue_city": self.venue_city,
            "referee": self.referee,
            "attendance": self.attendance,
            "is_knockout": self.is_knockout,
            "leg": self.leg,
            "agg_home": self.agg_home,
            "agg_away": self.agg_away,
            "ended_aet": self.ended_aet,
            "ended_pen": self.ended_pen,
            "events": json.loads(self.events_json) if self.events_json else [],
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<Match {self.home_team_name} vs {self.away_team_name} "
            f"[{self.league} GW{self.matchweek}]>"
        )