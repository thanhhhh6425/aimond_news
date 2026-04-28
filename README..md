# AimondNews

Website tin tức bóng đá tích hợp AI – Premier League & Champions League 2025/26.

---

## Tổng Quan Dự Án

**AimondNews** là ứng dụng web chuyên cung cấp thông tin bóng đá theo thời gian thực cho hai giải đấu hàng đầu thế giới: **Premier League (Anh)** và **UEFA Champions League**. Hệ thống tự động thu thập dữ liệu từ các nguồn uy tín như FotMob API, BBC Sport, Sky Sports và The Guardian, đồng thời tích hợp trợ lý AI thông minh hỗ trợ tiếng Việt.

### Mục Tiêu

Xây dựng một nền tảng tin tức bóng đá chuyên nghiệp, cập nhật liên tục và chính xác, cho phép người dùng tra cứu số liệu, xem lịch thi đấu, thống kê cầu thủ và đặt câu hỏi bằng tiếng Việt thông qua chatbot AI.

### Công Nghệ Sử Dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | Python 3.11+, Flask |
| Database | SQLAlchemy ORM, SQLite |
| Xác thực | Flask-Login, Flask-Bcrypt |
| Caching | Flask-Caching |
| Lập lịch tự động | APScheduler |
| Thu thập dữ liệu | Requests, FotMob API, RSS feeds |
| AI Chatbot | Google Gemini (google-genai) |
| Frontend | HTML, CSS (dual-theme), JavaScript |

### Cấu Trúc Thư Mục

```
aimond_news/
├── app/
│   ├── models/          # Các model SQLAlchemy (Club, Match, Player, Standing, News, Statistic, User)
│   ├── routes/          # Các Blueprint: matches, standings, players, clubs, news, chatbot, auth
│   ├── services/
│   │   ├── chatbot_service.py   # Gọi Google Gemini, xử lý AI
│   │   └── scheduler.py         # Các job tự động cập nhật dữ liệu
│   ├── __init__.py      # Flask app factory
│   ├── config.py        # Cấu hình từ biến môi trường
│   └── extensions.py    # Khởi tạo db, cache, scheduler, login_manager
│
├── scripts/
│   └── crawlers/        # Các script thu thập dữ liệu PL & UCL
│
├── static/
│   ├── css/             # style.css, theme-pl.css, theme-ucl.css
│   ├── js/              # api.js, chatbot.js, theme.js, ui.js, auth.js
│   └── images/
│
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── home.html, matches.html, table.html, bracket.html
│   ├── statistics.html, players.html, player_detail.html
│   ├── clubs.html, club_detail.html, news.html
│   └── login.html, register.html, profile.html
│
├── instance/
│   └── aimond_dev.db    # SQLite database (có sẵn dữ liệu mẫu)
│
├── crawl_matches.py     # Crawl lịch thi đấu & kết quả
├── crawl_events.py      # Crawl sự kiện trận đấu (bàn thắng, thẻ)
├── crawl_news.py        # Crawl tin tức từ RSS
├── run.py               # Entry point
└── requirements.txt
```

---

## Yêu Cầu

- Python 3.11+

---

## Cài Đặt

```bash
# 1. Tạo môi trường ảo
python -m venv venv

# 2. Kích hoạt venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 3. Cài thư viện
pip install -r requirements.txt
```

---



Mở trình duyệt: **http://localhost:5000**

> Dữ liệu đã có sẵn trong `instance/aimond_dev.db`, không cần cấu hình thêm.

---

## Cập Nhật Dữ Liệu Mới (Tuỳ Chọn)

Nếu muốn lấy dữ liệu mới nhất từ internet:

```bash
python crawl_matches.py
python scripts\run_all.py --only clubs
python scripts\run_all.py --only players
python scripts\run_all.py --only standings
python crawl_events.py
python crawl_news.py
```

### Dữ Liệu Lấy Từ Đâu?

| Script | Nguồn dữ liệu | Dữ liệu thu thập |
|--------|---------------|-----------------|
| `crawl_matches.py` | FotMob API | Lịch thi đấu, kết quả, tỉ số theo vòng |
| `run_all.py --only clubs` | FotMob API | Tên CLB, logo, sân vận động, HLV |
| `run_all.py --only players` | FotMob API | Danh sách cầu thủ, số áo, vị trí, ảnh |
| `run_all.py --only standings` | FotMob API | Bảng xếp hạng (điểm, trận, hiệu số) |
| `crawl_events.py` | FotMob API | Sự kiện: bàn thắng, thẻ vàng, thẻ đỏ |
| `crawl_news.py` | BBC Sport, Sky Sports, The Guardian | Tin tức bóng đá mới nhất |

### Thứ Tự Crawl Khuyến Nghị

Khi chạy lần đầu hoặc muốn làm mới toàn bộ dữ liệu, nên chạy theo thứ tự:

```bash
# Bước 1: Câu lạc bộ (cần có trước khi crawl cầu thủ & trận đấu)
python scripts\run_all.py --only clubs

# Bước 2: Cầu thủ
python scripts\run_all.py --only players

# Bước 3: Bảng xếp hạng
python scripts\run_all.py --only standings

# Bước 4: Lịch thi đấu và kết quả
python crawl_matches.py

# Bước 5: Sự kiện trận đấu (bàn thắng, thẻ)
python crawl_events.py

# Bước 6: Tin tức
python crawl_news.py
```

> **Lưu ý:** Quá trình crawl toàn bộ có thể mất 5–15 phút tuỳ tốc độ mạng. Đảm bảo kết nối internet ổn định trước khi chạy.

## Chạy Ứng Dụng

```bash
python run.py
```

### Cập Nhật Tự Động (Scheduler)

Khi ứng dụng đang chạy (`python run.py`), các job nền sẽ tự động cập nhật theo lịch mà không cần can thiệp thủ công:

| Job | Tần suất | Tác vụ |
|-----|----------|--------|
| Trận live | Mỗi 60 giây | Cập nhật tỉ số, sự kiện các trận đang diễn ra |
| Bảng xếp hạng | Mỗi 1 giờ | Đồng bộ bảng xếp hạng mới nhất |
| Tin tức | Mỗi 30 phút | Lấy bài viết mới từ RSS |
| Thống kê cầu thủ | 3:00 AM mỗi ngày | Cập nhật goals, assists, rating |
| Lịch thi đấu | Mỗi 6 giờ | Đồng bộ lịch các vòng sắp tới |

---

## Tính Năng Chính

- Lịch thi đấu, kết quả, sự kiện trận đấu (PL & UCL)
- Bảng xếp hạng, bracket knockout UCL
- Thống kê cầu thủ – top scorer, kiến tạo, rating
- Thông tin câu lạc bộ & đội hình
- Tin tức từ BBC Sport, Sky Sports, The Guardian
- Chatbot AI hỗ trợ tiếng Việt (AAA – AimondAI Assistant)
- Đăng ký / đăng nhập tài khoản
- Giao diện dark mode, dual-theme PL / UCL

### Chi Tiết Từng Tính Năng

**Lịch thi đấu & kết quả**

Hiển thị đầy đủ lịch thi đấu theo từng vòng (matchweek), lọc theo trạng thái: sắp diễn ra (SCHEDULED), đang diễn ra (LIVE), đã kết thúc (FT). Với các trận LIVE, tỉ số và sự kiện (bàn thắng, thẻ phạt) được cập nhật theo thời gian thực.

**Bảng xếp hạng**

Hiển thị đầy đủ các chỉ số: số trận, thắng/hoà/thua, bàn thắng/thua, hiệu số, điểm. Có màu sắc phân biệt rõ ràng: dự Champions League (xanh lá), dự Europa League (vàng), vòng play-off (xanh nhạt), xuống hạng (đỏ).

**Bracket UCL**

Sơ đồ nhánh đấu vòng loại trực tiếp Champions League, hiển thị các cặp đấu, tỉ số lượt đi/lượt về.

**Thống kê cầu thủ**

Danh sách top cầu thủ theo nhiều chỉ số: bàn thắng, kiến tạo, điểm trung bình (rating), thẻ vàng, thẻ đỏ. Có thể sắp xếp và lọc theo từng chỉ số.

**Thông tin câu lạc bộ & đội hình**

Trang chi tiết từng câu lạc bộ gồm: logo, tên sân, sức chứa, thành phố, huấn luyện viên. Đội hình phân nhóm theo vị trí: thủ môn, hậu vệ, tiền vệ, tiền đạo.

**Thông tin chi tiết cầu thủ**

Trang cầu thủ gồm: ảnh, số áo, quốc tịch, chiều cao, chân thuận, vị trí và thống kê đầy đủ trong mùa giải.

**Tin tức**

Tin tức tổng hợp từ BBC Sport, Sky Sports, The Guardian. Phân loại theo chuyên mục (trận đấu, chuyển nhượng, chấn thương, phỏng vấn), hiển thị kèm ảnh đại diện và thời gian đăng.

**Chatbot AI (AAA – AimondAI Assistant)**

Trợ lý AI tích hợp Google Gemini, hỗ trợ hỏi đáp hoàn toàn bằng tiếng Việt. Người dùng có thể hỏi về bảng xếp hạng, lịch thi đấu, thống kê cầu thủ, tin tức mới nhất. Nếu không có API key, chatbot tự động chuyển sang chế độ trả lời bằng từ khóa (fallback mode).

Để bật chatbot AI đầy đủ, tạo file `.env` trong thư mục gốc và thêm:

```
GEMINI_API_KEY=your_google_gemini_api_key
```

Lấy API key miễn phí tại: https://aistudio.google.com/app/apikeys

**Hệ thống tài khoản**

Đăng ký, đăng nhập, xem và cập nhật hồ sơ cá nhân (họ tên, ảnh đại diện), đổi mật khẩu.

**Dual-theme & Dark mode**

Chuyển đổi giao diện giữa Premier League (màu tím/xanh lá) và Champions League (màu xanh biển/vàng). Tuỳ chọn được lưu trong trình duyệt và ảnh hưởng đến dữ liệu hiển thị trên toàn bộ ứng dụng.
