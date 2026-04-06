python crawl_matches.py
python scripts\run_all.py --only clubs
python scripts\run_all.py --only players
python scripts\run_all.py --only standings
python crawl_events.py
python crawl_news.py
git add .
git commit -m "update: full data refresh"
git push