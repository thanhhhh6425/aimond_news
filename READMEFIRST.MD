# AimondNews — Hướng dẫn chạy demo

---

## Yêu cầu

- Python 3.10+
- pip

---

## Cài đặt nhanh

### 1. Kích hoạt môi trường ảo

```bash
cd aimond_news

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Cài thư viện

```bash
pip install -r requirements.txt
```

### 3. Chạy ứng dụng

```bash
python run.py
```

Truy cập: **http://localhost:5000**

> Database đã có sẵn dữ liệu tại `instance/aimond_dev.db`, không cần crawl lại.

---

## Tài khoản demo

| Vai trò | Username | Password |
|---------|----------|----------|
| Người dùng | `demo` | `demo123` |

---

## Các trang có thể khám phá

| URL | Nội dung |
|-----|----------|
| `/` | Trang chủ — tin tức & top scorers |
| `/news` | Tin tức Premier League & UCL |
| `/matches` | Lịch thi đấu, kết quả, sự kiện trận đấu |
| `/table` | Bảng xếp hạng |
| `/statistics` | Thống kê cầu thủ (ghi bàn, kiến tạo...) |
| `/players` | Danh sách cầu thủ |
| `/players/<id>` | Hồ sơ chi tiết cầu thủ |
| `/clubs` | Danh sách câu lạc bộ |
| `/bracket` | Bracket đấu loại UCL (chỉ hiện khi chọn UCL) |
| `/profile` | Hồ sơ cá nhân (cần đăng nhập) |

> **Lưu ý:** Nút chuyển **PL ↔ UCL** ở góc phải navbar để đổi giải đấu.

---

## Tạo tài khoản demo (nếu chưa có)

Nếu tài khoản `demo` chưa tồn tại, chạy lệnh sau:

```bash
python -c "
import os, sys
os.environ['DISABLE_SCHEDULER'] = '1'
sys.path.insert(0, '.')
from app import create_app
from app.extensions import db
from app.models import User
app = create_app()
with app.app_context():
    if not User.query.filter_by(username='demo').first():
        u = User(username='demo', email='demo@aimondnews.com', full_name='Demo User')
        u.set_password('demo123')
        db.session.add(u)
        db.session.commit()
        print('Tao tai khoan demo thanh cong')
    else:
        print('Tai khoan demo da ton tai')
"
```

---

## Lưu ý

- Ứng dụng chạy ở chế độ **development**, không cần cấu hình thêm
- Dữ liệu được crawl từ **FotMob API**, **ESPN API**, **BBC/Sky/Guardian RSS**
- Chatbot **AAA** sử dụng Google Gemini AI — cần `GEMINI_API_KEY` trong `.env` để hoạt động
- Scheduler tự động cập nhật dữ liệu nền khi server chạy