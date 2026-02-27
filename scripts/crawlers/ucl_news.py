"""
scripts/crawlers/ucl_news.py
Cào tin tức Champions League từ FotMob.

UCL news có các category đặc thù riêng:
  - Match Report (Phân tích trận đấu sau khi kết thúc)
  - Preview (Nhận định trước trận)
  - Transfer (Chuyển nhượng liên quan UCL)
  - Tactical Analysis (Phân tích chiến thuật)
  - Press Conference (Họp báo trước/sau trận)
  - UCL Record (Kỷ lục UCL)
  - Road to Final (Hành trình đến chung kết)

FotMob JSON (leagues?id=42):
  data["news"]  -> list of articles
  Each article:
    id/newsArticleId, title, subTitle, imageUrl,
    publishedAt (ISO), source, link,
    tag (có thể chứa "Champions League", "Match Report"...)
"""
from typing import Dict, List, Optional
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Keywords đặc trưng UCL để phân loại category
UCL_CATEGORY_KEYWORDS = {
    "Match Report":       ["report", "highlights", "recap", "result", "goals", "win", "draw", "loss", "beat", "defeat"],
    "Preview":            ["preview", "preview", "ahead", "prepare", "vs", "clash", "face", "take on"],
    "Transfer":           ["transfer", "sign", "join", "move", "deal", "bid", "want", "target", "linked"],
    "Press Conference":   ["press", "conference", "said", "says", "reveals", "insist", "claims", "confirm"],
    "Tactical Analysis":  ["tactical", "analysis", "formation", "system", "pressing", "how", "why", "shape"],
    "UCL Record":         ["record", "history", "most", "ever", "first time", "landmark", "milestone"],
    "Injury":             ["injur", "doubt", "miss", "return", "fit", "ruled out", "unavailable"],
    "Road to Final":      ["final", "semi", "quarter", "round of 16", "knockout", "eliminate", "advance"],
}


class UCLNewsCrawler(BaseFotMobCrawler):
    LEAGUE = "UCL"

    def parse(self, data: Dict) -> List[Dict]:
        results = []
        try:
            # FotMob có thể trả news ở nhiều path khác nhau
            news_list = (
                data.get("news")
                or data.get("newsArticles")
                or data.get("articles")
                or []
            )

            if not news_list:
                logger.warning("[UCLNews] No news found in response")
                return []

            for article in news_list:
                record = self._parse_article(article)
                if record:
                    results.append(record)

        except Exception as e:
            logger.error(f"[UCLNews] Parse error: {e}", exc_info=True)

        logger.info(f"[UCLNews] Parsed {len(results)} articles")
        return results

    def _parse_article(self, article: Dict) -> Optional[Dict]:
        try:
            title = self.clean(article.get("title", ""))
            if not title:
                return None

            # Source ID — thử nhiều field
            source_id = str(
                article.get("newsArticleId")
                or article.get("id")
                or article.get("articleId")
                or ""
            )
            if not source_id:
                return None

            # Published time
            pub_raw = (
                article.get("publishedAt")
                or article.get("published")
                or article.get("date")
                or ""
            )
            published_at = self._parse_datetime(str(pub_raw))

            # Image URL
            image_url = self.clean(
                article.get("imageUrl")
                or article.get("image")
                or article.get("thumbnail")
                or ""
            )

            # Source URL
            source_url = self.clean(
                article.get("link")
                or article.get("url")
                or article.get("href")
                or ""
            )

            # Excerpt / subtitle
            excerpt = self.clean(
                article.get("subTitle")
                or article.get("subtitle")
                or article.get("description")
                or ""
            )

            # Tên nguồn
            source_name = self.clean(
                article.get("source")
                or article.get("sourceName")
                or "FotMob UCL"
            )

            # Tags từ FotMob (nếu có)
            tags = article.get("tags", article.get("categories", []))
            tag_str = " ".join(str(t) for t in tags).lower() if tags else ""

            # Phân loại category
            category = self._classify_category(title, excerpt, tag_str)

            # Có liên quan đến round cụ thể không?
            ucl_round = self._detect_round(title + " " + excerpt)

            return {
                "league":        "UCL",
                "season":        self.SEASON,
                "source_id":     source_id,
                "title":         title,
                "excerpt":       excerpt,
                "thumbnail_url": image_url,
                "source_url":    source_url,
                "source_name":   source_name,
                "category":      category,
                "ucl_round":     ucl_round,   # Extra field: "Quarter-finals", "Semi-finals"...
                "published_at":  published_at,
            }
        except Exception as e:
            logger.debug(f"[UCLNews] Skip article: {e}")
            return None

    def _classify_category(self, title: str, excerpt: str, tags: str) -> str:
        """
        Phân loại category dựa trên title + excerpt + tags.
        UCL có nhiều category hơn PL.
        """
        text = (title + " " + excerpt + " " + tags).lower()

        for category, keywords in UCL_CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category

        return "News"

    def _detect_round(self, text: str) -> str:
        """Phát hiện vòng đấu UCL được đề cập trong bài."""
        text_lower = text.lower()
        if "final" in text_lower and "semi" not in text_lower and "quarter" not in text_lower:
            return "Final"
        if "semi" in text_lower:
            return "Semi-finals"
        if "quarter" in text_lower:
            return "Quarter-finals"
        if "round of 16" in text_lower or "r16" in text_lower or "last 16" in text_lower:
            return "Round of 16"
        if "knockout playoff" in text_lower or "play-off" in text_lower:
            return "Knockout Playoffs"
        if "league phase" in text_lower or "group stage" in text_lower:
            return "League Phase"
        return ""

    def _parse_datetime(self, raw: str) -> datetime:
        """Parse ISO datetime, fallback về now()."""
        if not raw or raw in ("None", "null", ""):
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)