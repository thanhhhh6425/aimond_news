# Cấu trúc dự án AimondNews

```
aimond_news/
│
├── run.py                          # Entry point – khởi động Flask app
├── requirements.txt                # Thư viện Python
├── .env.example                    # Mẫu biến môi trường
│
├── crawl_matches.py                # Crawl lịch + kết quả trận (PL & UCL)
├── crawl_events.py                 # Crawl sự kiện trận đấu (ESPN API)
├── crawl_news.py                   # Crawl tin tức (RSS fallback)
├── create_admin.py                 # Tạo tài khoản admin
│
├── scripts/                        # Hệ thống crawler chính
│   ├── run_all.py                  # Chạy thủ công: --only clubs/players/standings/news
│   ├── crawlers/
│   │   ├── base_crawler.py         # Lớp cơ sở – HTTP session, retry, headers
│   │   ├── pl_clubs.py             # Crawler CLB Premier League
│   │   ├── ucl_clubs.py            # Crawler CLB Champions League
│   │   ├── pl_matches.py           # Crawler lịch/kết quả PL
│   │   ├── ucl_matches.py          # Crawler lịch/kết quả UCL
│   │   ├── pl_players.py           # Crawler cầu thủ + thống kê PL
│   │   ├── ucl_players.py          # Crawler cầu thủ + thống kê UCL
│   │   ├── pl_standings.py         # Crawler bảng xếp hạng PL
│   │   ├── ucl_standings.py        # Crawler bảng xếp hạng UCL
│   │   ├── pl_news.py              # Crawler tin tức PL
│   │   └── ucl_news.py             # Crawler tin tức UCL
│   └── utils/
│       ├── db_writer.py            # Upsert dữ liệu vào DB
│       └── helpers.py              # Hàm tiện ích dùng chung
│
├── app/                            # Flask application
│   ├── __init__.py                 # App factory – create_app()
│   ├── config.py                   # Cấu hình môi trường (Dev/Production)
│   ├── extensions.py               # db, cache, login_manager, bcrypt
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── club.py                 # Câu lạc bộ
│   │   ├── match.py                # Trận đấu
│   │   ├── player.py               # Cầu thủ
│   │   ├── statistic.py            # Thống kê cầu thủ
│   │   ├── standing.py             # Bảng xếp hạng
│   │   ├── news.py                 # Tin tức
│   │   └── user.py                 # Tài khoản người dùng
│   │
│   ├── routes/                     # API endpoints & page routes
│   │   ├── pages.py                # Render HTML pages
│   │   ├── matches.py              # /api/matches/*
│   │   ├── standings.py            # /api/standings
│   │   ├── players.py              # /api/players/*
│   │   ├── statistics.py           # /api/statistics/*
│   │   ├── clubs.py                # /api/clubs/*
│   │   ├── news.py                 # /api/news
│   │   ├── chatbot.py              # /api/chatbot/message
│   │   └── auth.py                 # /api/auth/*
│   │
│   └── services/
│       ├── chatbot_service.py      # Gemini AI integration + RAG context
│       └── scheduler.py            # APScheduler – tự động cập nhật dữ liệu
│
├── templates/                      # Jinja2 HTML templates
│   ├── base.html                   # Layout chính – navbar, theme, chatbot widget
│   ├── pages/
│   │   ├── home.html
│   │   ├── matches.html            # Lịch thi đấu
│   │   ├── table.html              # Bảng xếp hạng
│   │   ├── bracket.html            # UCL knockout bracket
│   │   ├── players.html            # Danh sách cầu thủ
│   │   ├── player_detail.html      # Chi tiết cầu thủ
│   │   ├── statistics.html         # Thống kê
│   │   ├── clubs.html              # Danh sách CLB
│   │   ├── club_detail.html        # Chi tiết CLB
│   │   ├── news.html               # Tin tức
│   │   ├── login.html
│   │   ├── register.html
│   │   └── profile.html
│   └── partials/
│       ├── header.html
│       ├── footer.html
│       ├── chatbot.html            # Widget chatbot AAA
│       └── league-toggle.html      # Toggle PL/UCL
│
├── static/
│   ├── css/
│   │   ├── style.css               # CSS chính + CSS variables
│   │   ├── theme-pl.css            # Theme Premier League (tím)
│   │   └── theme-ucl.css           # Theme Champions League (navy/gold)
│   ├── js/
│   │   ├── api.js                  # Fetch wrapper + history management
│   │   ├── chatbot.js              # Chatbot UI + multi-turn conversation
│   │   ├── theme.js                # Toggle PL/UCL, localStorage
│   │   ├── ui.js                   # UI helpers
│   │   └── auth.js                 # Auth forms
│   └── images/
│       ├── pl-logo.svg
│       ├── ucl-logo.svg
│       └── placeholder.svg
│
└── instance/
    └── aimond_dev.db               # SQLite database (local development)
```

---

## Nguồn dữ liệu

| Nguồn | Dữ liệu |
|---|---|
| FotMob API (`fotmob.com/api/data`) | Lịch thi đấu, cầu thủ, CLB, bảng xếp hạng, bracket UCL |
| ESPN API (`site.api.espn.com`) | Sự kiện trận đấu (bàn thắng, thẻ phạt) |
| BBC Sport RSS | Tin tức bóng đá |
| Sky Sports RSS | Tin tức bóng đá |
| Google Gemini API | Chatbot AI (AAA) |

---

## Database schema

| Bảng | Mô tả |
|---|---|
| `clubs` | Thông tin câu lạc bộ (20 PL + 36 UCL) |
| `players` | Cầu thủ (~1000 người, 2 giải) |
| `statistics` | Thống kê cầu thủ (goals, assists, cards...) |
| `matches` | Lịch + kết quả (~570 trận) |
| `standings` | Bảng xếp hạng (cập nhật sau mỗi vòng) |
| `news` | Tin tức (cập nhật tự động) |
| `users` | Tài khoản người dùng |
