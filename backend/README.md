# Bản đồ sinh viên sư phạm - API Backend

Đây là mã nguồn của phần API Backend cho dự án "Bản đồ sinh viên sư phạm", được phát triển dựa trên **FastAPI** và kết nối với cơ sở dữ liệu **MongoDB**.

## Công nghệ sử dụng
- **Framework:** FastAPI (Python 3.11+)
- **Database:** MongoDB (sử dụng thư viện bất đồng bộ `motor`)
- **Object Storage:** MinIO (lưu trữ ảnh, file)
- **Validation:** Pydantic (v2)
- **Authentication:** JWT (JSON Web Tokens)
- **Testing:** Pytest & HTTPX

## Cấu trúc thư mục

```text
backend/
├── app/
│   ├── api/          # Các endpoint API (Routes) và Dependencies (deps.py)
│   ├── core/         # Cấu hình cốt lõi (config, database, security, minio)
│   ├── models/       # Sơ đồ biểu diễn dữ liệu trong MongoDB
│   ├── schemas/      # Định nghĩa cấu trúc dữ liệu Request/Response (Pydantic)
│   ├── services/     # Logic nghiệp vụ (Business logic), gửi mail, xử lý ảnh
│   └── main.py       # Điểm khởi chạy của ứng dụng FastAPI
├── tests/            # Unit, integration, E2E (pytest + httpx)
├── Dockerfile        # Đóng gói backend thành Docker image
├── pyproject.toml    # Thông tin dự án và cấu hình công cụ (ruff, pytest)
├── requirements.txt  # Danh sách thư viện phụ thuộc
└── README.md         # File tài liệu này
```

## Hướng dẫn cài đặt và chạy máy cục bộ không dùng Docker

Nếu bạn muốn phát triển Backend mà không cần khởi chạy toàn bộ hệ thống bằng Docker, hãy làm theo các bước sau:

### 1. Cài đặt môi trường ảo
Đảm bảo máy tính của bạn đã cài đặt Python 3.11 trở lên. Mở terminal tại thư mục `backend/`:
```bash
python -m venv venv

# Kích hoạt trên Linux/macOS:
source venv/bin/activate
# Kích hoạt trên Windows:
venv\Scripts\activate
```

### 2. Cài đặt các thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường
Mặc định FastAPI sẽ đọc cấu hình từ file `.env` ở thư mục gốc (`source/.env`). Đảm bảo rằng bạn đang có file này và các dịch vụ phụ trợ như MongoDB, MinIO đang chạy (bạn có thể chạy riêng DB bằng Docker Compose).

### 4. Khởi chạy Server
Sử dụng Uvicorn để chạy server ở chế độ tự động cập nhật khi có code thay đổi:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Sau khi chạy thành công, bạn có thể truy cập:
- **Tài liệu API Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **API Health Check:** http://localhost:8000/api/health

## Kiểm thử

```bash
conda activate devops
cd backend
```

Integration và E2E cần MongoDB chạy (từ thư mục `source/`):

```bash
docker compose -f docker/docker-compose.dev.yml up -d mongodb
```

| Loại | Thư mục | Lệnh |
|------|---------|------|
| Unit | `tests/unit/` | `pytest tests/unit -m unit` |
| Integration | `tests/test_*.py` | `pytest tests/ -m integration` |
| E2E (API) | `tests/e2e/` | `pytest tests/e2e -m e2e` |
| Tất cả | `tests/` | `pytest tests/` |

Frontend (Jest): [frontend/README.md](../frontend/README.md#kiểm-thử). Tổng quan: [README gốc](../README.md#kiểm-thử).

## Linter và Format Code

Dự án sử dụng **Ruff** và **Mypy** để đảm bảo chất lượng, định dạng và tính toàn vẹn của kiểu dữ liệu (static typing) trong mã nguồn Python.

1. **Kiểm tra và sửa lỗi cú pháp:**
   ```bash
   ruff check .
   ```
   *Thêm cờ `--fix` để ruff tự động sửa các lỗi phổ biến như import dư thừa: `ruff check . --fix`*

2. **Định dạng code tự động:**
   ```bash
   ruff format .
   ```

3. **Kiểm tra kiểu dữ liệu tĩnh:**
   ```bash
   mypy .
   ```

## Quy chuẩn phát triển
- Luôn khai báo **schema Pydantic** trong `app/schemas` thay vì trả về JSON tự do. Điều này giúp Swagger tự sinh tài liệu API.
- Logic truy xuất hoặc thao tác cơ sở dữ liệu nên được viết thành các hàm riêng biệt tại thư mục `app/services` thay vì viết thẳng vào các API endpoint router.
- Giữ nguyên tắc đặt tên biến `snake_case` và tên class `PascalCase` chuẩn của Python.
