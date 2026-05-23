# Hạ tầng Docker

Thư mục này chứa các tệp tin cấu hình Container Orchestration sử dụng Docker Compose cho các môi trường khác nhau.

## Các tệp cấu hình chính

- `docker-compose.dev.yml`: Cấu hình toàn bộ Dev Stack. Bao gồm:
  - Database: MongoDB
  - Object Storage: MinIO
  - Backend API: FastAPI
  - Frontend: React Vite
  - Reverse Proxy: Nginx

Các tệp cấu hình cho môi trường staging hoặc production sẽ được bổ sung vào đây trong tương lai.

## Hướng dẫn thao tác nhanh

Khởi chạy hệ thống môi trường phát triển:
```bash
docker compose --env-file .env -f docker/docker-compose.dev.yml up -d --build
```

Dừng và xóa toàn bộ container cùng với mạng lưới:
```bash
docker compose --env-file .env -f docker/docker-compose.dev.yml down
```

Xem log của một dịch vụ cụ thể:
```bash
docker compose -f docker/docker-compose.dev.yml logs -f api
```
