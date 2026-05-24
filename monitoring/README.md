# Monitoring & Logging Stack

Thư mục này chứa toàn bộ cấu hình Docker Compose và các tệp cấu hình cho hệ thống giám sát tài nguyên (Metrics) và thu thập nhật ký (Logs) của dự án **Bản đồ sinh viên**.

---

## 1. Kiến trúc ngăn xếp giám sát

Hệ thống giám sát được xây dựng bằng bộ công cụ **Grafana - Prometheus - Loki (LGTM Stack)**:

```text
               ┌────────────────┐
               │   Docker Logs  │
               └───────┬────────┘
                       │ (qua /var/run/docker.sock)
                       ▼
┌──────────────┐   ┌──────────┐
│  Host (CPU/  │   │          │
│  RAM/Disk)   ├──►│ Promtail │
└──────────────┘   │          │
                       │
                       ▼
┌──────────────┐   ┌──────────┐     ┌───────────┐
│ Containers   ├──►│   Loki   ├────►│  Grafana  │
│ (cAdvisor)   │   └──────────┘     │           │
└──────────────┘                    │  (Port    │
                       ▲            │   3001)   │
┌──────────────┐   ┌───┴──────┐     │           │
│ NodeExporter ├──►│Prometheus├────►│           │
└──────────────┘   └──────────┘     └───────────┘
```

### Các dịch vụ cốt lõi

1. **Prometheus:** Thu thập và lưu trữ Metrics (dữ liệu dạng chuỗi thời gian) từ Node Exporter và cAdvisor.
2. **Node Exporter:** Thu thập thông số phần cứng trực tiếp từ máy Host (CPU, RAM, ổ đĩa, mạng).
3. **cAdvisor:** Phân tích và đo lường tài nguyên tiêu thụ của từng Container Docker.
4. **Loki:** Thu thập, lưu trữ và đánh chỉ mục Logs từ Promtail.
5. **Promtail:** Agent tự động đọc toàn bộ Logs của các Container Docker trên Host và đẩy về Loki.
6. **Grafana:** Giao diện trực quan hóa, hiển thị Dashboards tổng quan tài nguyên và cho phép truy vấn Log nhanh chóng.

---

## 2. Cấu trúc thư mục

```text
monitoring/
├── docker-compose.monitoring.yml     # Định nghĩa khởi chạy toàn bộ Monitoring Stack
├── prometheus/
│   └── prometheus.yml                 # Cấu hình các jobs thu thập metrics
├── loki/
│   └── loki-config.yml                # Cấu hình lưu trữ log cục bộ (Retention 7 ngày)
├── promtail/
│   └── promtail-config.yml            # Cấu hình agent thu gom docker logs
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── datasources.yml        # Tự động nạp nguồn dữ liệu Prometheus & Loki
└── README.md                          # Tài liệu hướng dẫn sử dụng chi tiết
```

---

## 3. Khởi động và Quản lý nhanh

### Phân quyền dữ liệu (Chỉ cần nếu dùng thư mục Host volume)

_Mẹo: File docker-compose.monitoring.yml hiện tại sử dụng Docker Named Volumes giúp tự động cấp quyền mà không cần chạy lệnh `chown` thủ công._

### Lệnh khởi chạy

```bash
# Di chuyển tới thư mục chứa code
cd monitoring/

# Khởi động Monitoring Stack (Tự tạo network bridge "monitoring" trước khi chạy App chính)
docker compose -f docker-compose.monitoring.yml up -d

# Kiểm tra trạng thái các service
docker compose -f docker-compose.monitoring.yml ps
```

---

## 4. Hướng dẫn thiết lập Grafana lần đầu

1. **Truy cập:** Mở trình duyệt vào địa chỉ `http://localhost:3001` (qua SSH Tunnel hoặc cấu hình Nginx reverse proxy `grafana.hcmue.info.vn`).
2. **Đăng nhập mặc định:**
   - **Tài khoản:** `admin`
   - **Mật khẩu:** Khai báo trong biến môi trường `GF_SECURITY_ADMIN_PASSWORD` (mặc định trong compose: `your_strong_password`).
   - Hãy đổi mật khẩu ngay trong lần đầu đăng nhập.
3. **Kiểm tra nguồn dữ liệu (Datasources):**
   - Vào mục **Connections** -> **Data Sources**.
   - Cả hai nguồn **Prometheus** (`http://prometheus:9090`) và **Loki** (`http://loki:3100`) đều đã được tự động nạp sẵn và hoạt động .

### Import các Dashboards quan trọng

Vào **Dashboards** -> **New** -> **Import**, điền ID tương ứng và chọn Datasource phù hợp:

| Tên Dashboard               | ID Grafana | Nguồn dữ liệu | Hiển thị thông số                                                 |
| --------------------------- | ---------- | ------------- | ----------------------------------------------------------------- |
| **Node Exporter Full**      | `1860`     | Prometheus    | CPU, RAM, Latency, Mạng và Dung lượng đĩa của máy Host.           |
| **cAdvisor - Docker**       | `14282`    | Prometheus    | Tài nguyên tiêu thụ chi tiết (CPU/RAM) của từng Container Docker. |
| **Loki & Promtail Metrics** | `10880`    | Prometheus    | Trạng thái hoạt động nội bộ của Loki và lưu lượng logs.           |
| **Docker Container Logs**   | `15141`    | Loki          | Xem trực tiếp logs của toàn bộ container theo thời gian thực.     |

---

## 5. Các truy vấn LogQL ( logs ) thực tế trong Grafana

Truy cập **Grafana** -> **Explore** -> Chọn **Loki** làm nguồn dữ liệu để chạy các câu truy vấn sau:

### 1. Xem toàn bộ logs của một container cụ thể

```logql
{container_name="backend"}
{container_name="frontend"}
```

### 2. Lọc log lỗi của toàn bộ các dịch vụ trên server

```logql
{job="containerlogs"} |~ "(?i)(error|warn|fatal|exception)"
```

### 3. Đếm số lỗi phát sinh theo thời gian thực

```logql
sum by (container_name) (
  count_over_time({job="containerlogs"} |~ "(?i)error" [5m])
)
```

### 4. Phân tích Log Nginx — Đếm request theo HTTP Status Code

```logql
sum by (status) (
  rate(
    {container_name="frontend"}
    | pattern `<ip> - - [<_>] "<method> <path> <_>" <status> <_>`
    [1m]
  )
)
```

### 5. Phát hiện IP truy cập nhiều nhất (Top 10 IP)

```logql
topk(10,
  sum by (ip) (
    count_over_time(
      {container_name="frontend"}
      | pattern `<ip> - -`
      [5m]
    )
  )
)
```

### 6. So sánh tỷ lệ logs sinh ra giữa các container

```logql
sum by (container_name) (
  rate({job="containerlogs"} [1m])
)
```

---

## 6. Lệnh quản lý hàng ngày

```bash
# Xem log thời gian thực của container cụ thể
docker compose -f docker-compose.monitoring.yml logs -f grafana
docker compose -f docker-compose.monitoring.yml logs -f loki

# Khởi động lại toàn bộ stack
docker compose -f docker-compose.monitoring.yml restart

# Cập nhật các image giám sát lên phiên bản mới nhất
docker compose -f docker-compose.monitoring.yml pull && docker compose -f docker-compose.monitoring.yml up -d

# Kiểm tra endpoints hoạt động tốt từ host
curl http://localhost:9090/-/healthy   # Prometheus -> OK
curl http://localhost:3100/ready       # Loki -> ready
```

---

## 7. Xử lý sự cố thường gặp (Troubleshooting)

| Triệu chứng                              | Nguyên nhân phổ biến                                                | Giải pháp khắc phục                                                                                                                                           |
| ---------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dữ liệu Dashboard trống trơn             | 1. Khoảng thời gian chọn quá hẹp.<br>2. Cài đặt múi giờ không khớp. | 1. Thay đổi thời gian góc trên bên phải thành `Last 1 hour` hoặc `Last 3 hours`.<br>2. Chỉnh timezone trong Profile Grafana thành UTC hoặc Local.             |
| Dashboard báo đỏ, lỗi kết nối Datasource | Prometheus hoặc Loki chưa hoàn tất khởi động hoặc bị crash.         | Chạy lệnh `docker compose -f docker-compose.monitoring.yml restart prometheus loki` để khởi động lại dịch vụ.                                                 |
| Promtail không đẩy được log              | Sai địa chỉ endpoint của Loki.                                      | Kiểm tra tệp `promtail-config.yml`, đảm bảo url đẩy log khớp: `http://loki:3100/loki/api/v1/push`.                                                            |
| Port bị conflict không start được stack  | Cổng 9090 hoặc 3001 đã bị chiếm bởi dịch vụ khác trên Host.         | Chạy lệnh `sudo ss -tlnp` trên Host để tìm xem dịch vụ nào đang chiếm cổng, sau đó tắt dịch vụ đó hoặc đổi cổng ánh xạ trong `docker-compose.monitoring.yml`. |
| cAdvisor không hoạt động hoặc không có metrics | Không tương thích cgroups v2 (trên Linux mới như Ubuntu 22.04+) hoặc thiếu device kmsg. | 1. Sử dụng image `gcr.io/cadvisor/cadvisor:v0.49.1` (thay vì `latest` vì latest đã quá cũ).<br>2. Bổ sung cấu hình `devices: - /dev/kmsg` trong file docker-compose để đọc dữ liệu hệ thống chính xác. |
