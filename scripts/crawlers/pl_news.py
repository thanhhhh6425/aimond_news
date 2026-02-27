"""
scripts/crawlers/pl_news.py
Cào tin tức Premier League từ FotMob.

FotMob JSON structure (leagues?id=47):
  data["news"]  -> list of news articles
  Each article:
    id, title, subTitle (excerpt), imageUrl, newsArticleId,
    source, publishedAt (ISO string), link
"""
from typing import Dict, List, Optional
from scripts.crawlers.base_crawler import BaseFotMobCrawler
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PLNewsCrawler(BaseFotMobCrawler):
    LEAGUE = "PL"

    def parse(self, data: Dict) -> List[Dict]:
        results = []
        try:
            news_list = data.get("news", [])
            if not news_list:
                # Thử nested path
                news_list = data.get("newsArticles", data.get("articles", []))

            for article in news_list:
                record = self._parse_article(article)
                if record:
                    results.append(record)

        except Exception as e:
            logger.error(f"[PLNews] Parse error: {e}", exc_info=True)

        logger.info(f"[PLNews] Parsed {len(results)} articles")
        return results

    def _parse_article(self, article: Dict) -> Optional[Dict]:
        try:
            title = self.clean(article.get("title", ""))
            if not title:
                return None

            # Published time
            published_at = None
            pub_raw = article.get("publishedAt", article.get("published", ""))
            if pub_raw:
                try:
                    published_at = datetime.fromisoformat(
                        str(pub_raw).replace("Z", "+00:00")
                    )
                except Exception:
                    published_at = datetime.now(timezone.utc)
            else:
                published_at = datetime.now(timezone.utc)

            source_id = str(
                article.get("newsArticleId",
                article.get("id",
                article.get("articleId", "")))
            )
            if not source_id:
                return None

            return {
                "league": self.LEAGUE,
                "season": self.SEASON,
                "source_id": source_id,
                "title": title,
                "excerpt": self.clean(article.get("subTitle", article.get("subtitle", ""))),
                "thumbnail_url": self.clean(article.get("imageUrl", article.get("image", ""))),
                "source_url": self.clean(article.get("link", article.get("url", ""))),
                "source_name": self.clean(article.get("source", "FotMob")),
                "category": self._guess_category(title),
                "published_at": published_at,
            }
        except Exception as e:
            logger.debug(f"[PLNews] Skip article: {e}")
            return None

    def _guess_category(self, title: str) -> str:
        title_lower = title.lower()
        if any(k in title_lower for k in ["transfer", "sign", "move", "join", "deal", "bid"]):
            return "Transfer"
        if any(k in title_lower for k in ["injur", "return", "fit", "miss", "doubt"]):
            return "Injury"
        if any(k in title_lower for k in ["interview", "says", "claims", "insists", "reveals"]):
            return "Interview"
        if any(k in title_lower for k in ["preview", "preview", "ahead", "vs", "clash"]):
            return "Preview"
        if any(k in title_lower for k in ["report", "highlights", "goals", "result", "win", "loss", "draw"]):
            return "Match Report"
        return "News"
