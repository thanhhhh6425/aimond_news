"""
crawl_news.py - Crawl news tu BBC RSS va luu vao DB
BBC PL:   https://feeds.bbci.co.uk/sport/football/premier-league/rss.xml
BBC UEFA: https://feeds.bbci.co.uk/sport/football/european/rss.xml
Sky PL:   https://www.skysports.com/rss/12040
"""
import sys, os, logging
os.environ["DISABLE_SCHEDULER"] = "1"
sys.path.insert(0, ".")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

import requests, urllib3
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml",
}

FEEDS = [
    ("PL",  "BBC Sport",    "https://feeds.bbci.co.uk/sport/football/premier-league/rss.xml"),
    ("PL",  "Sky Sports",   "https://www.skysports.com/rss/12040"),
    ("PL",  "The Guardian", "https://www.theguardian.com/football/premierleague/rss"),
    ("UCL", "BBC Sport",    "https://feeds.bbci.co.uk/sport/football/european/rss.xml"),
    ("UCL", "The Guardian", "https://www.theguardian.com/football/championsleague/rss"),
]

def fetch_rss(url):
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if r.status_code == 200:
            return r.content
    except Exception as e:
        logging.warning(f"RSS fetch error {url}: {e}")
    return None

def parse_rss(content, league, source_name):
    items = []
    try:
        root = ET.fromstring(content)
        ns = {"media": "http://search.yahoo.com/mrss/",
              "dc":    "http://purl.org/dc/elements/1.1/",
              "content": "http://purl.org/rss/1.0/modules/content/"}
        channel = root.find("channel")
        if channel is None:
            return items

        for item in channel.findall("item"):
            title    = (item.findtext("title") or "").strip()
            link     = (item.findtext("link")  or "").strip()
            desc     = (item.findtext("description") or "").strip()
            pub_str  = (item.findtext("pubDate") or "").strip()
            guid     = (item.findtext("guid")  or link or title).strip()

            # Thumbnail - thu media:thumbnail hoac enclosure
            thumb = ""
            media_thumb = item.find("media:thumbnail", ns)
            if media_thumb is not None:
                thumb = media_thumb.get("url","")
            if not thumb:
                enclosure = item.find("enclosure")
                if enclosure is not None:
                    thumb = enclosure.get("url","")
            if not thumb:
                media_content = item.find("media:content", ns)
                if media_content is not None:
                    thumb = media_content.get("url","")
            # Nang cap BBC thumbnail tu 240 -> 1024
            if thumb and "bbci.co.uk" in thumb:
                import re as _re
                thumb = _re.sub(r"/standard/\d+/", "/standard/1024/", thumb)

            # Published
            pub_dt = None
            if pub_str:
                try:
                    pub_dt = parsedate_to_datetime(pub_str)
                except:
                    try:
                        pub_dt = datetime.fromisoformat(pub_str.replace("Z","+00:00"))
                    except:
                        pub_dt = datetime.now(timezone.utc)
            else:
                pub_dt = datetime.now(timezone.utc)

            if not title or not link:
                continue

            # Category
            title_lower = title.lower()
            if any(k in title_lower for k in ["transfer","sign","move","join","deal","bid","loan"]):
                cat = "Chuyển nhượng"
            elif any(k in title_lower for k in ["injur","return","fit","miss","doubt","ruled out"]):
                cat = "Chấn thương"
            elif any(k in title_lower for k in ["preview","vs","clash","face","host","travel"]):
                cat = "Trận đấu"
            elif any(k in title_lower for k in ["interview","says","claims","insists","reveals","speaks"]):
                cat = "Phỏng vấn"
            else:
                cat = "Tin tức"

            # Source ID tu guid
            import hashlib
            source_id = hashlib.md5(guid.encode()).hexdigest()[:20]

            items.append({
                "source_id":    source_id,
                "league":       league,
                "title":        title,
                "excerpt":      desc[:300] if desc else "",
                "thumbnail_url":thumb,
                "source_url":   link,
                "source_name":  source_name,
                "category":     cat,
                "published_at": pub_dt,
            })
    except Exception as e:
        logging.error(f"RSS parse error: {e}")
    return items

# ── MAIN ─────────────────────────────────────────────────────────────────────
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    from app.models import News

    # Xoa news cu
    db.session.execute(db.text("DELETE FROM news"))
    db.session.commit()
    logging.info("Cleared news")

    total = 0
    for league, source, url in FEEDS:
        logging.info(f"Fetching {source} [{league}]: {url}")
        content = fetch_rss(url)
        if not content:
            logging.warning(f"  No content")
            continue

        items = parse_rss(content, league, source)
        logging.info(f"  Parsed {len(items)} articles")

        for item in items:
            try:
                # Skip neu da co source_id
                exists = News.query.filter_by(source_id=item["source_id"]).first()
                if exists:
                    continue

                news = News(
                    source_id    = item["source_id"],
                    league       = item["league"],
                    season       = "2025",
                    title        = item["title"],
                    excerpt      = item["excerpt"],
                    thumbnail_url= item["thumbnail_url"],
                    source_url   = item["source_url"],
                    source_name  = item["source_name"],
                    category     = item["category"],
                    published_at = item["published_at"],
                )
                db.session.add(news)
                total += 1
            except Exception as e:
                logging.error(f"  Error: {e}")
                db.session.rollback()

        db.session.commit()

    logging.info(f"\nDone: {total} articles saved")

    # Verify
    for lg in ["PL","UCL"]:
        n = db.session.execute(db.text(f"SELECT COUNT(*) FROM news WHERE league='{lg}'")).scalar()
        logging.info(f"  {lg}: {n} articles")

    # Sample
    rows = db.session.execute(db.text(
        "SELECT title, league, source_name, category, published_at FROM news ORDER BY published_at DESC LIMIT 5"
    )).fetchall()
    for r in rows:
        print(f"  [{r.league}] {r.title[:60]} ({r.source_name}, {r.category})")