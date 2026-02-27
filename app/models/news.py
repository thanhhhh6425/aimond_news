"""
app/models/news.py - Model tin tức bóng đá
"""
from datetime import datetime, timezone
from app.extensions import db


class News(db.Model):
    """
    Tin tức từ premierleague.com và uefa.com - 2025/26
    """
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)

    # Định danh từ nguồn cào
    source_id = db.Column(db.String(200), nullable=True, unique=True, index=True)
    source_url = db.Column(db.String(1000), nullable=True)
    league = db.Column(db.String(10), nullable=False, index=True)   # 'PL' | 'UCL'
    season = db.Column(db.String(10), nullable=False, default="2025")

    # Nội dung
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(600), nullable=True, index=True)
    excerpt = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)

    # Hình ảnh
    thumbnail_url = db.Column(db.String(1000), nullable=True)
    image_url = db.Column(db.String(1000), nullable=True)
    image_caption = db.Column(db.String(500), nullable=True)

    # Phân loại
    category = db.Column(db.String(50), nullable=True)   # 'Match Report', 'Transfer', 'Interview'
    tags = db.Column(db.Text, nullable=True)              # JSON array: ["Arsenal", "Salah"]

    # Tác giả & nguồn
    author = db.Column(db.String(100), nullable=True)
    source_name = db.Column(db.String(50), nullable=True)  # 'premierleague.com' | 'uefa.com'

    # Thời gian
    published_at = db.Column(db.DateTime, nullable=True, index=True)

    # Liên quan
    related_club_id = db.Column(db.Integer, db.ForeignKey("clubs.id"), nullable=True)
    related_player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=True)
    related_match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self, full=False):
        import json
        data = {
            "id": self.id,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "league": self.league,
            "season": self.season,
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "thumbnail_url": self.thumbnail_url,
            "image_url": self.image_url,
            "category": self.category,
            "tags": json.loads(self.tags) if self.tags else [],
            "author": self.author,
            "source_name": self.source_name,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
        if full:
            data["content"] = self.content
            data["image_caption"] = self.image_caption
        return data

    def __repr__(self):
        return f"<News '{self.title[:40]}...' [{self.league}]>"
