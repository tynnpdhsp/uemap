# Script bảo trì
Thư mục này chứa các script chạy tự động phục vụ cho công tác quản trị máy chủ, sao lưu, phục hồi và thao tác dữ liệu.

## Danh sách script

- `backup-mongodb.sh`: Sử dụng công cụ `mongodump` thông qua Docker để nén và sao lưu toàn bộ cơ sở dữ liệu hệ thống ra tệp tin `.archive`.
- `backup-minio.sh`: Tạo bản sao lưu toàn bộ tài nguyên đa phương tiện đang chứa trong kho MinIO.
- `restore.sh`: Script có tính tương tác. Trợ giúp kỹ sư hạ tầng nhập đường dẫn tệp tin để phục hồi nóng cơ sở dữ liệu và MinIO.
- `seed-categories.py`: Đoạn mã Python nạp các dữ liệu danh mục bản đồ mặc định vào cơ sở dữ liệu nếu bảng dữ liệu trống.

## Lưu ý cấp quyền

Do các tệp tin này là script thực thi trên Linux, bạn phải đảm bảo cấp quyền thực thi cho chúng trước khi sử dụng.

```bash
chmod +x scripts/*.sh
```

Cách chạy script an toàn từ gốc dự án:
```bash
./scripts/backup-mongodb.sh
```
