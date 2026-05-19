# SalesManager Pro

Hệ thống quản lý bán hàng tích hợp phân tích và dự báo doanh thu.

## Cài đặt

```bash
# 1. Tạo virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate     # Windows

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Đảm bảo MongoDB đang chạy
# MongoDB: mongodb://localhost:27017

# 4. Chạy ứng dụng (sẽ tự seed sample data)
python app.py
```

## Tài khoản mặc định

| Vai trò | Username | Password |
|---------|----------|----------|
| Admin   | admin    | admin123 |
| Staff   | staff1   | staff123 |

## Truy cập

http://localhost:5000

## Tính năng

- 🔐 Đăng nhập / Đăng ký / Phân quyền Admin & Staff
- 📦 Quản lý sản phẩm (CRUD, upload ảnh, tồn kho)
- 👤 Quản lý khách hàng (CRUD, lịch sử mua hàng)
- 🧾 Hóa đơn (tạo, xem, lọc theo thời gian)
- 📊 Dashboard với Chart.js (animated)
- 🤖 Dự báo doanh thu AI (Linear Regression)
