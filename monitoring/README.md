# Monitoring Stack

Thư mục này định nghĩa Monitoring Stack để giám sát tài nguyên và phân tích log hệ thống. Môi trường giám sát được tách biệt hoàn toàn khỏi kiến trúc ứng dụng cốt lõi để đảm bảo không tranh giành tài nguyên.

## Các thành phần cốt lõi

1. **Prometheus:** Máy chủ thu thập và lưu trữ các Metrics của hệ thống theo định dạng Time-series.
2. **Loki:** Hệ thống gom cụm và đánh chỉ mục Logs, siêu nhẹ và tiết kiệm tài nguyên.
3. **Grafana:** Nền tảng trực quan hóa dữ liệu, cung cấp các Dashboards để hiển thị thông số từ Prometheus và log từ Loki.

## Cấu trúc thư mục

- `docker-compose.monitoring.yml`: Tệp điều phối khởi chạy toàn bộ ngăn xếp giám sát.
- Các thư mục cấu hình con: Chứa `prometheus.yml`, Dashboards mặc định cho Grafana và cấu hình đường ống dẫn log.

## Hướng dẫn thao tác nhanh

Khởi động Monitoring Stack:
```bash
docker compose --env-file .env -f monitoring/docker-compose.monitoring.yml up -d
```

Các Dashboards thường được truy cập tại http://localhost:4000 với tài khoản mặc định `admin`/`admin`.
