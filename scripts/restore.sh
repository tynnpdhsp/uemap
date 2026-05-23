#!/bin/bash
# Script khôi phục cơ sở dữ liệu MongoDB và tài nguyên MinIO từ các bản sao lưu

# Xác định thư mục của script hiện tại
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load biến môi trường nếu có từ thư mục cha
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
fi

DB_NAME=${MONGODB_DB_NAME:-"ban_do_sv_sp"}
BUCKET_NAME=${MINIO_BUCKET_NAME:-"ban-do-uploads"}

echo "=== HƯỚNG DẪN KHÔI PHỤC HỆ THỐNG ==="
echo "Vui lòng chọn chức năng:"
echo "1) Khôi phục MongoDB"
echo "2) Khôi phục MinIO"
echo "3) Khôi phục cả hai"
read -p "Lựa chọn của bạn (1-3): " choice

case $choice in
    1|3)
        read -p "Nhập đường dẫn đến file MongoDB archive (.archive): " mongo_file
        if [ -f "$mongo_file" ]; then
            echo "Đang khôi phục MongoDB từ $mongo_file..."

            # Copy file vào container
            docker cp "$mongo_file" ban-do-mongodb-dev:/data/db/restore_temp.archive

            # Chạy mongorestore
            docker exec ban-do-mongodb-dev mongorestore --db "$DB_NAME" --drop --archive=/data/db/restore_temp.archive

            # Xóa file tạm
            docker exec ban-do-mongodb-dev rm /data/db/restore_temp.archive
            echo "Khôi phục MongoDB thành công."
        else
            echo "Không tìm thấy file backup MongoDB!"
            [ "$choice" == "1" ] && exit 1
        fi
        ;;
esac

case $choice in
    2|3)
        read -p "Nhập đường dẫn đến file MinIO tar.gz (.tar.gz): " minio_file
        if [ -f "$minio_file" ]; then
            echo "Đang khôi phục MinIO từ $minio_file..."
            
            # Giải nén tạm thời
            TEMP_DIR="$SCRIPT_DIR/../backups/minio/temp_restore"
            mkdir -p "$TEMP_DIR"
            tar -xzf "$minio_file" -C "$TEMP_DIR"
            
            # Khôi phục qua mc client
            docker run --rm \
              --network ban-do-network-dev \
              -v "${TEMP_DIR}:/temp_restore" \
              quay.io/minio/mc:latest \
              sh -c "mc alias set myminio http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY} && \
                     mc cp --recursive /temp_restore/ myminio/${BUCKET_NAME}"
            
            # Xóa thư mục tạm
            rm -rf "$TEMP_DIR"
            echo "Khôi phục MinIO thành công."
        else
            echo "Không tìm thấy file backup MinIO!"
            exit 1
        fi
        ;;
esac

echo "Quá trình khôi phục hoàn tất."
