# CI/CD

Thư mục này chứa các khai báo về Pipeline phục vụ quá trình CI/CD bằng Jenkins.

## Tệp cấu hình chính

- `Jenkinsfile`: Script khai báo toàn bộ luồng xử lý mã nguồn Pipeline as Code sử dụng cú pháp Groovy Declarative.

## Quy trình Pipeline

Mỗi khi mã nguồn được đẩy lên kho lưu trữ trên nhánh main hoặc staging, Jenkins sẽ thực hiện các bước sau:
1. Tải mã nguồn mới nhất.
2. Kiểm tra mã nguồn bằng Linter.
3. Chạy Unit Test và thu thập Test Coverage.
4. Phân tích chất lượng mã qua SonarQube Quality Gate.
5. Đóng gói mã nguồn thành Docker Image và đẩy lên Registry.
6. Triển khai máy chủ tự động bằng Docker Compose.
