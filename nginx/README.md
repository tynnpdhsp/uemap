# Reverse Proxy
Thư mục này chứa toàn bộ định nghĩa cấu hình cho Nginx. Trong hệ thống "Bản đồ sinh viên", Nginx đóng vai trò là API Gateway và Reverse Proxy duy nhất để hứng các truy cập từ người dùng và điều phối luồng dữ liệu.

## Cấu trúc thư mục

```text
nginx/
├── conf.d/
│   ├── app.conf      # Định nghĩa điều hướng cổng 80 cho React và FastAPI
│   └── ssl/          # Nơi chứa chứng chỉ HTTPS SSL tự cấp hoặc Let's Encrypt
└── README.md
```

## Vai trò của Nginx
- Ẩn kiến trúc hạ tầng phía sau với thế giới bên ngoài.
- Gom chung backend và frontend về một cổng duy nhất để giải quyết triệt để lỗi CORS từ phía trình duyệt.
- Xử lý chứng chỉ SSL bảo mật HTTPS.

Cấu hình mặc định trong `app.conf`:
- Mọi yêu cầu bắt đầu bằng `/api/` sẽ được chuyển hướng sang container `api`.
- Các yêu cầu còn lại `/` sẽ được chuyển sang container `frontend`.
