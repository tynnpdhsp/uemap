# Reverse Proxy & API Gateway (Nginx)

Thư mục này chứa toàn bộ định nghĩa cấu hình và hướng dẫn triển khai Nginx cho dự án **Bản đồ sinh viên** ở cả hai môi trường: **Local Development** (sử dụng Docker) và **Production** (sử dụng Host-level Reverse Proxy).

---

## 1. Cấu trúc thư mục

```text
nginx/
├── conf.d/
│   └── app.conf                       # Cấu hình Local Dev (React + FastAPI) qua Docker
├── production/
│   ├── default                        # Cấu hình mặc định (catch-all) cho Production
│   ├── map.hcmue.info.vn.conf         # Cấu hình domain chính cho App (Frontend, Backend, MinIO)
│   └── grafana.hcmue.info.vn.conf     # Cấu hình domain cho Grafana (Port 3001)
└── README.md                          # Tài liệu hướng dẫn sử dụng và triển khai
```

---

## 2. Môi trường phát triển (Local Development)

Trong môi trường Local Dev (chạy qua Docker Compose bằng file `docker/docker-compose.dev.yml`), Nginx đóng vai trò là API Gateway duy nhất:

- **Cổng kết nối:** Nginx container lắng nghe trên cổng `80` nội bộ và được ánh xạ ra ngoài qua cổng `8080` (`http://localhost:8080`).
- **Cơ chế điều hướng (cấu hình trong `conf.d/app.conf`):**
  - Mọi yêu cầu bắt đầu bằng `/api` sẽ được chuyển hướng sang container `api` (FastAPI chạy ở port 8000).
  - Các yêu cầu còn lại `/` sẽ được chuyển hướng sang container `frontend` (React chạy ở port 3000).
- **Lợi ích:** Gom chung backend và frontend về một cổng duy nhất giúp giải quyết triệt để lỗi CORS từ phía trình duyệt.

---

## 3. Môi trường triển khai thực tế (Production)

Trên server Production (Ubuntu 20.04 / 22.04 / 24.04), Nginx chạy trực tiếp trên hệ điều hành làm Reverse Proxy và quản lý chứng chỉ SSL Let's Encrypt. 

### Sơ đồ kiến trúc Production
```text
Internet
   │
   ▼ (port 80 → tự động redirect 443)
Nginx Host (SSL Let's Encrypt)
   │
   ├── map.hcmue.info.vn /          → http://127.0.0.1:3000  (Frontend React)
   ├── map.hcmue.info.vn /api/      → http://127.0.0.1:8000  (Backend FastAPI)
   ├── map.hcmue.info.vn /storage/  → http://127.0.0.1:9000  (MinIO Storage)
   └── grafana.hcmue.info.vn        → http://127.0.0.1:3001  (Grafana, HTTP only nội bộ)
```

> [!IMPORTANT]
> Toàn bộ các cổng dịch vụ nội bộ (như 3000, 3001, 8000, 9000, 27017, 9090, 3100) chỉ bind vào `127.0.0.1` (localhost) trên Docker. Tuyệt đối không mở các port này ra ngoài Firewall UFW, chỉ truy cập duy nhất qua Nginx Reverse Proxy (SSL 443) hoặc SSH Tunnel. MongoDB (:27017) là nội bộ hoàn toàn, chỉ backend gọi trực tiếp qua Docker network, tuyệt đối không bao giờ expose.

---

### HƯỚNG DẪN SETUP CHI TIẾT TRÊN PRODUCTION

#### BƯỚC 1: Cài đặt Nginx trên Host
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx curl wget git ufw

sudo systemctl enable nginx
sudo systemctl start nginx
```

#### BƯỚC 2: Cấu hình UFW Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 26266/tcp (port SSH tùy chỉnh nếu có)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

#### BƯỚC 3: Reset cấu hình Nginx mặc định
```bash
# Xóa các symbolic link cấu hình cũ nếu có
sudo rm -f /etc/nginx/sites-enabled/*
sudo rm -f /etc/nginx/sites-available/default

# Tạo cấu hình default mới (catch-all port 80)
# (Copy file nginx/production/default vào /etc/nginx/sites-available/default)
sudo cp production/default /etc/nginx/sites-available/default

# Tạo link kích hoạt
sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### BƯỚC 4: Triển khai cấu hình Domain Web / App (`map.hcmue.info.vn`)
File cấu hình này bao gồm định tuyến cho cả 3 thành phần (Frontend, API Backend và MinIO Storage) chung một domain để triệt tiêu CORS:

```bash
# Copy file cấu hình mẫu vào sites-available
sudo cp production/map.hcmue.info.vn.conf /etc/nginx/sites-available/map.hcmue.info.vn

# Tạo link kích hoạt cấu hình
sudo ln -s /etc/nginx/sites-available/map.hcmue.info.vn /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### BƯỚC 5: Triển khai cấu hình Domain Grafana (`grafana.hcmue.info.vn`)
Grafana chạy trên cổng `3001` nội bộ để tránh đụng độ cổng với Frontend:

```bash
# Copy file cấu hình mẫu vào sites-available
sudo cp production/grafana.hcmue.info.vn.conf /etc/nginx/sites-available/grafana.hcmue.info.vn

# Tạo link kích hoạt cấu hình
sudo ln -s /etc/nginx/sites-available/grafana.hcmue.info.vn /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### BƯỚC 6: Cấp chứng chỉ bảo mật HTTPS SSL bằng Certbot Let's Encrypt
> Đảm bảo DNS của domain đã trỏ về IP của server trước khi chạy lệnh. Chỉ cấp SSL công khai cho domain Web App, Grafana giữ HTTP nội bộ để bảo mật.

```bash
# Cài đặt certbot và plugin nginx
sudo apt install -y certbot python3-certbot-nginx

# Kiểm tra HTTP hoạt động bình thường chưa
curl -I http://map.hcmue.info.vn

# Tiến hành cấp phát chứng chỉ SSL cho domain ứng dụng
sudo certbot --nginx -d map.hcmue.info.vn

# Kiểm tra tính năng tự động gia hạn (auto-renew)
sudo certbot renew --dry-run

# Xem chứng chỉ hiện có trên server
sudo certbot certificates
```

---

## 4. Lệnh quản lý hàng ngày

```bash
# Kiểm tra cú pháp cấu hình Nginx (Bắt buộc chạy trước khi reload/restart)
sudo nginx -t

# Tải lại cấu hình Nginx không làm gián đoạn kết nối
sudo systemctl reload nginx

# Khởi động lại dịch vụ Nginx
sudo systemctl restart nginx

# Kiểm tra trạng thái hoạt động
sudo systemctl status nginx

# Xem log truy cập và log lỗi của Nginx trên Host
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Kiểm tra gia hạn SSL Let's Encrypt
sudo certbot renew --dry-run
```

---

## 5. Xử lý lỗi thường gặp (Troubleshooting)

| Triệu chứng | Nguyên nhân phổ biến | Cách khắc phục |
|---|---|---|
| Lệnh `nginx -t` báo lỗi `conflicting server name ...` | Trùng lặp khai báo domain ở 2 file config khác nhau trong thư mục enabled. | Chạy lệnh `grep -r "domain" /etc/nginx/` để tìm file cấu hình bị trùng, tiến hành xóa hoặc chỉnh sửa rồi reload lại Nginx. |
| Certbot báo lỗi xác thực DNS | Bản ghi DNS của domain chưa cập nhật hoặc trỏ sai IP server. | Dùng lệnh `dig map.hcmue.info.vn` hoặc `nslookup` trên máy cá nhân để check xem IP đã cập nhật chưa. Hãy đợi vài phút để DNS propagate rồi thử lại. |
| Nginx báo lỗi `502 Bad Gateway` khi truy cập domain | Dịch vụ backend phía sau Nginx (Docker container Frontend/Backend/MinIO hoặc Grafana) chưa chạy hoặc listen sai port. | 1. Kiểm tra container: `docker compose ps` xem container có đang chạy không.<br>2. Kiểm tra port: Đảm bảo app frontend đang lắng nghe cổng `3000`, backend cổng `8000`, minio cổng `9000` và Grafana cổng `3001` trên localhost. |
| Lỗi không kết nối được HTTPS sau khi chạy Certbot | Firewall chưa mở port 443. | Chạy lại `sudo ufw allow 443/tcp` và `sudo ufw reload`. |
| Port bị conflict không khởi động được service | Có 2 service cùng cố gắng bind vào 1 cổng trên host. | Sử dụng lệnh `sudo ss -tlnp` hoặc `sudo netstat -tlnp` để tìm tiến trình đang sử dụng port đó và tắt nó đi. |
| Upload file lên MinIO báo lỗi kích thước | Nginx chặn request upload có body quá lớn. | Kiểm tra tham số `client_max_body_size 100M;` trong block `/storage/` đã được khai báo chính xác chưa. |
| Dữ liệu MongoDB không kết nối được | Sai URI kết nối của MongoDB. | Kiểm tra biến môi trường `MONGODB_URL` trong file cấu hình container `backend`. |
