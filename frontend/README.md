# Bản đồ sinh viên sư phạm - Frontend

Đây là mã nguồn của phần giao diện người dùng cho dự án "Bản đồ sinh viên sư phạm", được phát triển bằng **React** và trình đóng gói **Vite**.

## Công nghệ sử dụng

- **Thư viện lõi:** React 18, TypeScript
- **Công cụ build:** Vite siêu tốc, hỗ trợ hot-reload nhanh
- **Styling:** Tailwind CSS
- **Bản đồ:** Leaflet tương tác trực tiếp với bản đồ và tọa độ
- **Quản lý state & data fetching:** React Query hoặc Zustand dự kiến tích hợp

## Cấu trúc thư mục

```text
frontend/
├── public/           # Chứa các file tĩnh không qua trình đóng gói Vite
├── src/
│   ├── assets/       # Tài nguyên tĩnh qua đóng gói
│   ├── components/   # Các component React dùng chung
│   ├── layouts/      # Các bố cục giao diện chính
│   ├── pages/        # Các trang màn hình chính
│   ├── services/     # Cấu hình gọi API tới backend
│   ├── utils/        # Các hàm tiện ích dùng chung
│   ├── App.tsx       # Component gốc của ứng dụng
│   └── main.tsx      # Điểm neo vào index.html
├── index.html        # Khung HTML gốc
├── package.json      # Danh sách thư viện và các lệnh npm
├── tailwind.config.js# Cấu hình giao diện và màu sắc cho Tailwind
├── vite.config.ts    # Cấu hình máy chủ phát triển và đóng gói
└── README.md         # Tài liệu hướng dẫn
```

## Hướng dẫn cài đặt và chạy máy cục bộ không dùng Docker

Nếu bạn muốn phát triển giao diện độc lập mà không cần bật toàn bộ hệ thống bằng Docker, hãy làm theo các bước sau:

### 1. Cài đặt thư viện

Đảm bảo máy tính đã cài đặt **Node.js** khuyến nghị phiên bản LTS từ 18 trở lên. Tại thư mục `frontend/`, chạy lệnh:

```bash
npm install
```

### 2. Khởi chạy máy chủ phát triển

```bash
npm run dev
```

Dịch vụ sẽ khởi chạy tại http://localhost:3000. Mọi thay đổi trong code sẽ tự động cập nhật lên trình duyệt ngay lập tức nhờ tính năng HMR của Vite.

_Lưu ý: Để ứng dụng có thể lấy được dữ liệu thực, bạn vẫn cần đảm bảo backend API đang hoạt động_

## Linter và định dạng code

Dự án sử dụng **ESLint** để kiểm tra chất lượng code và **Prettier** để định dạng.

- Kiểm tra lỗi code:
  ```bash
  npm run lint
  ```
- Định dạng code tự động:
  ```bash
  npm run format
  ```
  _Hoặc tận dụng tính năng Format on Save của trình soạn thảo VSCode._

## Kiểm thử

```bash
npm install
npm run test              # unit + integration
npm run test:unit
npm run test:integration
npm run test:coverage
```

| Loại | Thư mục | Mô tả |
|------|---------|--------|
| Unit | `src/__tests__/` (trừ `integration/`) | Component, context, API client |
| Integration | `src/__tests__/integration/` | Router + AuthProvider + mock `fetch`, luồng auth đầy đủ |

API + MongoDB: [backend/README.md](../backend/README.md#kiểm-thử). E2E trình duyệt: [README gốc](../README.md#kiểm-thử-e2e).

## Quy chuẩn phát triển

- Luôn sử dụng **TypeScript** và định nghĩa kiểu dữ liệu cho mọi component. Tránh lạm dụng kiểu `any`.
- Các component lớn cần được chia nhỏ thành các component chức năng đơn giản đặt trong `src/components`.
- Chỉ lưu trữ các state tĩnh mang tính toàn cục, còn state cục bộ nên gắn liền với component đó.
- Đặt tên file theo chuẩn PascalCase cho các component và camelCase cho các hàm tiện ích.
