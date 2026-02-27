# Cấu trúc dự án AimondNews

```
aimond_news/
├── app/                                # Thư mục mã nguồn chính
│   ├── models/                         # Định nghĩa cấu trúc dữ liệu (ORM)
│   │   ├── __init__.py
│   │   ├── club.py                     # Model câu lạc bộ
│   │   ├── match.py                    # Model trận đấu
│   │   ├── news.py                     # Model tin tức
│   │   ├── player.py                   # Model cầu thủ
│   │   ├── standing.py                 # Model bảng xếp hạng
│   │   ├── statistic.py                # Model thống kê
│   │   └── user.py                     # Model người dùng
│   ├── routes/                         # Điều hướng trang và API
│   │   ├── __init__.py
│   │   ├── auth.py                     # API đăng ký, đăng nhập, hồ sơ
│   │   ├── chatbot.py                  # API chatbot AI
│   │   ├── clubs.py                    # API câu lạc bộ
│   │   ├── matches.py                  # API trận đấu & bracket UCL
│   │   ├── news.py                     # API tin tức
│   │   ├── pages.py                    # Route render các trang HTML
│   │   ├── players.py                  # API cầu thủ
│   │   ├── standings.py                # API bảng xếp hạng
│   │   └── statistics.py               # API thống kê cầu thủ
│   ├── services/                       # Dịch vụ nền
│   │   ├── __init__.py
│   │   ├── chatbot_service.py          # Xử lý logic chatbot (Gemini AI)
│   │   └── scheduler.py                # Lên lịch crawl dữ liệu tự động
│   ├── static/                         # Tài nguyên tĩnh
│   │   ├── css/
│   │   │   ├── style.css               # CSS chính toàn trang
│   │   │   ├── theme-pl.css            # CSS theme Premier League
│   │   │   └── theme-ucl.css           # CSS theme Champions League
│   │   ├── images/
│   │   │   ├── logo.png / logo.svg     # Logo AimondNews
│   │   │   ├── pl-ball.png             # Bóng Premier League
│   │   │   ├── pl-logo.png / .svg      # Logo Premier League
│   │   │   ├── placeholder.svg         # Ảnh placeholder
│   │   │   ├── ucl-ball.png            # Bóng Champions League
│   │   │   └── ucl-logo.png / .svg     # Logo Champions League
│   │   └── js/
│   │       ├── api.js                  # Wrapper gọi REST API
│   │       ├── auth.js                 # Xử lý đăng nhập/đăng xuất phía client
│   │       ├── chatbot.js              # Logic giao diện chatbot
│   │       ├── theme.js                # Chuyển đổi theme PL ↔ UCL
│   │       └── ui.js                   # Tiện ích giao diện chung
│   ├── templates/                      # Giao diện HTML (Jinja2)
│   │   ├── pages/
│   │   │   ├── bracket.html            # Nhánh đấu loại trực tiếp UCL
│   │   │   ├── club_detail.html        # Trang chi tiết câu lạc bộ
│   │   │   ├── clubs.html              # Danh sách câu lạc bộ
│   │   │   ├── home.html               # Trang chủ
│   │   │   ├── login.html              # Trang đăng nhập
│   │   │   ├── matches.html            # Lịch thi đấu & kết quả
│   │   │   ├── news.html               # Trang tin tức
│   │   │   ├── player_detail.html      # Trang chi tiết cầu thủ
│   │   │   ├── players.html            # Danh sách cầu thủ
│   │   │   ├── profile.html            # Trang hồ sơ người dùng
│   │   │   ├── register.html           # Trang đăng ký
│   │   │   ├── statistics.html         # Thống kê cầu thủ
│   │   │   └── table.html              # Bảng xếp hạng
│   │   ├── partials/
│   │   │   ├── chatbot.html            # Component chatbot
│   │   │   ├── footer.html             # Footer trang
│   │   │   ├── header.html             # Header/navbar
│   │   │   └── league-toggle.html      # Nút chuyển giải đấu
│   │   └── base.html                   # Layout gốc (kế thừa toàn trang)
│   ├── __init__.py                     # Khởi tạo Flask App & đăng ký Blueprint
│   ├── config.py                       # Cấu hình môi trường (dev/prod)
│   └── extensions.py                   # Khởi tạo DB, Cache, Login Manager
│
├── instance/
│   └── aimond_dev.db                   # SQLite database thực tế
│
├── migrations/                         # Lịch sử migration database (Flask-Migrate)
│
├── scripts/                            # Công cụ thu thập dữ liệu
│   ├── crawlers/
│   │   ├── __init__.py
│   │   ├── base_crawler.py             # Lớp crawler cơ sở
│   │   ├── pl_clubs.py                 # Crawl CLB Premier League
│   │   ├── pl_matches.py               # Crawl lịch/kết quả PL
│   │   ├── pl_news.py                  # Crawl tin tức PL
│   │   ├── pl_players.py               # Crawl cầu thủ PL
│   │   ├── pl_standings.py             # Crawl bảng XH PL
│   │   ├── ucl_clubs.py                # Crawl CLB Champions League
│   │   ├── ucl_matches.py              # Crawl lịch/kết quả UCL
│   │   ├── ucl_news.py                 # Crawl tin tức UCL
│   │   ├── ucl_players.py              # Crawl cầu thủ UCL
│   │   └── ucl_standings.py            # Crawl bảng XH UCL
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db_writer.py                # Tiện ích ghi dữ liệu vào DB
│   │   └── helpers.py                  # Hàm tiện ích chung
│   └── run_all.py                      # Chạy toàn bộ crawlers
│
├── crawl_events.py                     # Crawl sự kiện trận đấu (ESPN API)
├── crawl_matches.py                    # Crawl & cập nhật trận đấu (FotMob)
├── crawl_news.py                       # Crawl tin tức (BBC/Sky/Guardian RSS)
├── crawl_players.py                    # Crawl thống kê cầu thủ (FotMob)
├── update_matches.py                   # Cập nhật trạng thái trận đấu
├── reset_and_crawl.py                  # Reset DB và crawl lại toàn bộ
├── setup_ucl_playoff.py                # Thiết lập dữ liệu playoff UCL
├── create_admin.py                     # Tạo tài khoản admin
├── check_data.py                       # Kiểm tra dữ liệu trong DB
├── test_fotmob_api.py                  # Kiểm thử kết nối FotMob API
├── test_ucl_data.py                    # Kiểm thử dữ liệu UCL
├── tree.py                             # Xuất cấu trúc thư mục dự án
│
├── .env                                # Biến môi trường (ẩn, không commit)
├── .env.example                        # Mẫu biến môi trường
├── requirements.txt                    # Danh sách thư viện Python
├── run.py                              # Điểm khởi chạy server Flask
├── PROJECT_STRUCTURE.MD                # Tài liệu cấu trúc dự án
└── README.md                           # Hướng dẫn cài đặt và sử dụng
```

## Mô tả các thành phần chính

### Backend (Flask)
- **app/models/** — Định nghĩa schema database với SQLAlchemy ORM
- **app/routes/** — REST API endpoints và route render HTML
- **app/services/** — Logic nghiệp vụ: chatbot AI (Google Gemini) và scheduler tự động

### Frontend
- **app/static/css/** — CSS toàn trang với hệ thống dual-theme PL/UCL
- **app/static/js/** — JavaScript xử lý giao diện, API calls, xác thực
- **app/templates/** — Giao diện HTML dùng Jinja2 template engine

### Thu thập dữ liệu
- **scripts/crawlers/** — Module crawl theo từng giải đấu và loại dữ liệu
- **crawl_*.py** — Script crawl thực thi trực tiếp từ root, nguồn: FotMob API, ESPN API, BBC/Sky/Guardian RSS

### Database
- SQLite (`instance/aimond_dev.db`) cho môi trường phát triển
- Flask-Migrate quản lý lịch sử thay đổi schema

### Công cụ kiểm thử
- **check_data.py** — Truy vấn và kiểm tra dữ liệu trong DB
- **test_fotmob_api.py** — Kiểm thử kết nối và cấu trúc FotMob API
- **test_ucl_data.py** — Kiểm thử tính toàn vẹn dữ liệu UCL