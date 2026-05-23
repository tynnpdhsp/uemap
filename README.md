# Bản đồ sinh viên sư phạm

Ứng dụng bản đồ công khai cho sinh viên Trường Đại học Sư phạm TP.HCM.

## Tổng quan

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Leaflet
- **Backend:** FastAPI, Python
- **Database:** MongoDB (GeoJSON, 2dsphere index)
- **Storage:** MinIO (ảnh, video)
- **Reverse Proxy:** Nginx
- **CI/CD:** Jenkins, SonarQube
- **Monitoring:** Grafana, Prometheus, Loki

## Cấu trúc thư mục

```
source/
├── frontend/          # React, Vite, TypeScript, Tailwind
├── backend/           # FastAPI, Python
├── docker/            # Dockerfile, docker-compose
├── nginx/             # Cấu hình reverse proxy, SSL
├── jenkins/           # Jenkinsfile, job cấu hình
├── monitoring/        # Grafana, Prometheus, Loki
├── scripts/           # Backup, deploy, seed, tiện ích
├── .env.example       # Mẫu biến môi trường
└── README.md
```

## Hướng dẫn chạy trên môi trường phát triển

### Yêu cầu hệ thống
* **Phần mềm:** Docker và Docker Compose (v2) đã được cài đặt và cấp quyền hoạt động.
* **Cấu hình tối thiểu (Dev Stack):**
  * CPU: 2 Cores
  * RAM: 4GB
  * Ổ cứng trống: Tối thiểu 5GB
* **Cấu hình khuyến nghị nếu chạy thêm hệ thống giám sát:**
  * CPU: 4 Cores
  * RAM: 8GB
  * Ổ cứng trống: Tối thiểu 10GB

### Các bước khởi động chi tiết

#### Bước 1: Thiết lập cấu hình biến môi trường
Sao chép tệp tin mẫu và kiểm tra các cấu hình:
```bash
cp .env.example .env
```
*Bạn có thể tùy chỉnh các cổng hoặc cấu hình kết nối trong tệp `.env` vừa tạo nếu cần thiết.*

#### Bước 2: Khởi chạy các container phát triển
Sử dụng docker-compose để tải các Docker image, build mã nguồn skeleton và hiển thị log trực tiếp (không chạy ngầm):
```bash
docker compose -f docker/docker-compose.dev.yml up --build
```
*Tiến trình này sẽ liên tục hiển thị log. Hãy giữ nguyên terminal này và mở một terminal mới cho các bước tiếp theo.*

#### Bước 3: Nạp dữ liệu mặc định cho cơ sở dữ liệu
Thực hiện trên một terminal mới
Nạp 4 danh mục địa điểm mặc định: hành chính của trường, quán ăn và uống, quán in ấn, tiện ích gần trường vào MongoDB:
```bash
docker compose -f docker/docker-compose.dev.yml exec api python /app/scripts/seed-categories.py
```

#### Bước 4: Khởi chạy hệ thống giám sát và log tùy chọn
Thực hiện trên một terminal mới
Nếu cần theo dõi metrics tài nguyên và lưu trữ logs của ứng dụng qua Grafana/Prometheus/Loki:
```bash
docker compose -f monitoring/docker-compose.monitoring.yml up
```

---

## Bảng tổng hợp liên kết truy cập hệ thống

Sau khi khởi chạy thành công, toàn bộ tài nguyên của hệ thống có thể được truy cập tại các địa chỉ dưới đây:

| Thành phần / Dịch vụ | Địa chỉ truy cập (URL) | Tài khoản mặc định / Ghi chú |
| :--- | :--- | :--- |
| **Giao diện người dùng** | [http://localhost:8080](http://localhost:8080) | Cổng HTTP phát triển thông qua proxy |
| **Giao diện React** | [http://localhost:3000](http://localhost:3000) | Truy cập trực tiếp có HMR |
| **Tài liệu Swagger API** | [http://localhost:8080/api/docs](http://localhost:8080/api/docs) | Bật tài liệu Swagger tương tác ở môi trường dev |
| **Kiểm tra trạng thái** | [http://localhost:8080/api/health](http://localhost:8080/api/health) | Trả về `{"success":true,"data":{"status":"ok"}}` |
| **MinIO Console** | [http://localhost:9001](http://localhost:9001) | User: `minioadmin` \| Pass: `minioadmin` |
| **Grafana Dashboard** | [http://localhost:4000](http://localhost:4000) | User: `admin` \| Pass: `admin` |
| **Prometheus Dashboard** | [http://localhost:9090](http://localhost:9090) | Theo dõi các metrics tài nguyên |
| **Loki Logs Endpoint** | [http://localhost:3100](http://localhost:3100) | Cổng thu thập logs tập trung |

## Quy ước nhánh

| Nhánh | Mục đích |
|-------|----------|
| `main` | Production |
| `staging` | Tích hợp, deploy dev |
| `feature/<tên>` | Tính năng mới |
| `fix/<tên>` | Sửa lỗi |
| `hotfix/<tên>` | Sửa khẩn trên main |

## Commit message

Theo chuẩn Conventional Commits:
```
<type>(<scope>): <mô tả ngắn>
```

Ví dụ:
- `feat(map): thêm lọc danh mục trên bản đồ`
- `fix(auth): sửa thông báo OTP hết hạn`
- `chore(devops): cập nhật Jenkinsfile`
