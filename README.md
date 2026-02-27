# AimondNews — Nền tảng tin tức & số liệu bóng đá

> Ứng dụng web theo dõi **Premier League** và **UEFA Champions League** mùa giải 2025/26.  
> Dữ liệu thời gian thực từ FotMob API, ESPN API và BBC/Sky Sports/The Guardian RSS.

---

## Tính năng

- Bảng xếp hạng, lịch thi đấu, kết quả trực tiếp
- Thống kê cầu thủ: ghi bàn, kiến tạo, thẻ phạt, điểm TB
- Trang chi tiết cầu thủ & câu lạc bộ
- Bracket đấu loại trực tiếp UCL
- Tin tức tổng hợp từ BBC Sport, Sky Sports, The Guardian
- Dual-theme: chuyển đổi giao diện PL ↔ UCL
- Chatbot AI (AAA) tích hợp Google Gemini
- Hệ thống tài khoản người dùng (đăng ký, đăng nhập, hồ sơ)

---

## Yêu cầu hệ thống

- Python 3.10+
- pip
- Git

---

## Cài đặt

### Bước 1: Clone và cài dependencies

```bash
cd aimond_news

# Tạo và kích hoạt virtualenv
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Cài toàn bộ thư viện
pip install -r requirements.txt
```

### Bước 2: Cấu hình môi trường

```bash
cp .env.example .env
```

Mở `.env` và điền các giá trị:

```env
SECRET_KEY=your_secret_key_here
GEMINI_API_KEY=your_gemini_api_key   # Dùng cho chatbot AAA
DATABASE_URL=                         # Để trống = dùng SQLite mặc định
```

### Bước 3: Khởi tạo database

```bash
flask --app run:app db upgrade
```

Hoặc tạo bảng trực tiếp:

```bash
python -c "
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
    print('Tables created!')
"
```

### Bước 4: Crawl dữ liệu ban đầu

```bash
# Crawl dữ liệu Premier League & UCL (cần internet, ~10-15 phút)
python crawl_matches.py
python crawl_players.py
python crawl_news.py
python crawl_events.py
```

### Bước 5: Tạo tài khoản admin

```bash
python create_admin.py
```

### Bước 6: Chạy ứng dụng

```bash
python run.py
```

Truy cập: **http://localhost:5000**

---

## Cấu trúc URL

| URL | Trang |
|-----|-------|
| `/` | Trang chủ |
| `/news` | Tin tức |
| `/matches` | Lịch thi đấu & kết quả |
| `/table` | Bảng xếp hạng |
| `/bracket` | Bracket UCL |
| `/statistics` | Thống kê cầu thủ |
| `/players` | Danh sách cầu thủ |
| `/players/<id>` | Chi tiết cầu thủ |
| `/clubs` | Danh sách câu lạc bộ |
| `/clubs/<id>` | Chi tiết câu lạc bộ |
| `/profile` | Hồ sơ người dùng |
| `/login` | Đăng nhập |
| `/register` | Đăng ký |

---

## API Endpoints chính

| Method | URL | Chức năng |
|--------|-----|-----------|
| GET | `/api/news/?league=PL` | Danh sách tin tức |
| GET | `/api/matches/?league=UCL&status=FT` | Trận đấu |
| GET | `/api/standings/?league=PL` | Bảng xếp hạng |
| GET | `/api/players/?league=PL&position=FWD` | Cầu thủ |
| GET | `/api/statistics/players?sort=goals` | Thống kê cầu thủ |
| GET | `/api/matches/bracket?league=UCL` | Bracket UCL |
| POST | `/api/auth/register` | Đăng ký |
| POST | `/api/auth/login` | Đăng nhập |
| GET | `/api/auth/me` | Thông tin người dùng |
| PATCH | `/api/auth/me` | Cập nhật hồ sơ |
| POST | `/api/chatbot/message` | Chatbot AAA |

---

## Scheduler tự động

APScheduler chạy nền ngay khi khởi động server:

| Job | Chu kỳ | Chức năng |
|-----|--------|-----------|
| `live_matches` | 60 giây | Cập nhật trạng thái trận live |
| `standings` | 1 giờ | Đồng bộ bảng xếp hạng |
| `news` | 30 phút | Kéo tin tức mới |
| `players` | 3h sáng UTC | Cập nhật thống kê cầu thủ |
| `fixtures` | 6 giờ | Đồng bộ lịch thi đấu |

Trigger thủ công (cần tài khoản admin):

```bash
curl -X POST http://localhost:5000/api/admin/trigger/news
curl -X POST http://localhost:5000/api/admin/trigger/standings
```

---

## Công cụ kiểm thử & tiện ích

```bash
python check_data.py          # Kiểm tra dữ liệu trong DB
python test_fotmob_api.py     # Kiểm thử kết nối FotMob API
python test_ucl_data.py       # Kiểm thử dữ liệu UCL
python update_matches.py      # Cập nhật trạng thái trận đấu thủ công
python setup_ucl_playoff.py   # Thiết lập dữ liệu playoff UCL
python reset_and_crawl.py     # Reset DB và crawl lại toàn bộ
```

---

## Triển khai Production

```bash
pip install gunicorn
FLASK_ENV=production gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
```

Với PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/aimond_news
```

---

## Xử lý lỗi thường gặp

**Lỗi import module:**
```bash
cd aimond_news
venv\Scripts\activate
python run.py
```

**Dữ liệu trống sau crawl:**
- Kiểm tra kết nối internet
- Chạy `python check_data.py` để xem trạng thái DB

**Chatbot không hoạt động:**
- Kiểm tra `GEMINI_API_KEY` trong file `.env`

**Theme không chuyển đổi:**
- Xóa localStorage: F12 → Application → Local Storage → Clear

---

## Thư viện chính

| Thư viện | Chức năng |
|----------|-----------|
| Flask | Web framework |
| SQLAlchemy | ORM database |
| Flask-Migrate | Migration DB |
| Flask-Login | Xác thực người dùng |
| Flask-Caching | Cache API response |
| APScheduler | Lên lịch crawl tự động |
| Requests | Gọi API bên ngoài |
| google-generativeai | Chatbot Gemini AI |
| python-dotenv | Quản lý biến môi trường |