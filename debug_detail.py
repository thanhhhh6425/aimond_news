import os
import logging
import requests

# 1. BẬT LOGGING ĐỂ XEM LỖI ẨN
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

os.environ["DISABLE_SCHEDULER"] = "1"
from scripts.crawlers.ucl_players import UCLPlayersCrawler
from app import create_app
from app.extensions import db
from scripts.utils.db_writer import DBWriter

# 2. KIỂM TRA TRỰC TIẾP MÃ MÙA GIẢI UCL TỪ FOTMOB
print("\n" + "=" * 50)
print("🔍 ĐANG TRUY TÌM MÃ MÙA GIẢI (SEASON ID) MỚI NHẤT CỦA UCL...")
try:
    r = requests.get(
        "https://www.fotmob.com/api/leagues?id=42",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    data = r.json()
    see_all = data.get("overview", {}).get("topPlayers", {}).get("byGoals", {}).get("seeAllUrl", "")
    if see_all:
        season_id = see_all.split("/season/")[1].split("/")[0]
        print(f"🎯 TÌM THẤY RỒI! Mã mùa giải Champions League hiện tại là: {season_id}")
        print("👉 HÃY COPY MÃ SỐ NÀY VÀ ĐỔI TRONG FILE ucl_players.py NHÉ!")
    else:
        print("❌ FotMob đã đổi cấu trúc, không tìm thấy đường dẫn seeAllUrl.")
except Exception as e:
    print(f"❌ Lỗi khi tìm mã mùa giải: {e}")
print("=" * 50 + "\n")

# 3. CHẠY LẠI CRAWLER NHƯ BÌNH THƯỜNG
app = create_app()
with app.app_context():
    crawler = UCLPlayersCrawler()
    records = crawler.run_sync()

    with_goals = [r for r in records if r.get("goals", 0) > 0]
    print(f"\n✅ Số cầu thủ có bàn thắng lấy được: {len(with_goals)}")

    writer = DBWriter()
    n = writer.upsert_players(records, league="UCL")
    print(f"✅ Đã ghi vào DB: {n} cầu thủ")

    from app.models import Statistic

    cnt = Statistic.query.filter_by(league="UCL", season="2025").filter(Statistic.goals > 0).count()
    print(f"✅ Số lượng trong DB sau khi ghi: {cnt}")