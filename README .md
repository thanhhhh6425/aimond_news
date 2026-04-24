# AimondNews

Website tin tức bóng đá tích hợp AI – Premier League & Champions League 2025/26.

---

## Yêu cầu

- Python 3.11+

---

## Cài đặt

```bash
# 1. Tạo môi trường ảo
python -m venv venv

# 2. Kích hoạt venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# 3. Cài thư viện
pip install -r requirements.txt
```



## Cập nhật dữ liệu mới

Chạy lần lượt các lệnh phía dưới lấy dữ liệu mới nhất từ internet:

```bash
python crawl_matches.py
python scripts\run_all.py --only clubs
python scripts\run_all.py --only players
python scripts\run_all.py --only standings
python crawl_events.py
python crawl_news.py
```
---

## Chạy ứng dụng

```bash
python run.py
```

Mở trình duyệt: **http://localhost:5000**

> Dữ liệu đã có sẵn trong `instance/aimond_dev.db`, không cần cấu hình thêm.

---
---

## Tính năng chính

- Lịch thi đấu, kết quả, sự kiện trận đấu (PL & UCL)
- Bảng xếp hạng, bracket knockout UCL
- Thống kê cầu thủ – top scorer, kiến tạo, rating
- Thông tin câu lạc bộ & đội hình
- Tin tức từ BBC Sport, Sky Sports, The Guardian
- Chatbot AI hỗ trợ tiếng Việt (AAA – AimondAI Assistant)
- Đăng ký / đăng nhập tài khoản
- Giao diện dark mode, dual-theme PL / UCL
