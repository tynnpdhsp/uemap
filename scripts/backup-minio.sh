#!/bin/bash
# Script sao lưu dữ liệu MinIO (ảnh, video)

# Xác định thư mục của script hiện tại
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load biến môi trường nếu có từ thư mục cha
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
fi

BUCKET_NAME=${MINIO_BUCKET_NAME:-"ban-do-uploads"}
BACKUP_DIR="$SCRIPT_DIR/../backups/minio"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="minio_backup_${BUCKET_NAME}_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Starting MinIO backup for bucket: ${BUCKET_NAME}..."

# Thực hiện nén dữ liệu MinIO bằng cách nén thư mục volume local hoặc mc mirror
docker run --rm \
  --network ban-do-network-dev \
  -v "${BACKUP_DIR}:/backups" \
  quay.io/minio/mc:latest \
  sh -c "mc alias set myminio http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY} && \
         mc cp --recursive myminio/${BUCKET_NAME} /backups/${BACKUP_NAME}_tmp && \
         tar -czf /backups/${BACKUP_NAME} -C /backups/${BACKUP_NAME}_tmp . && \
         rm -rf /backups/${BACKUP_NAME}_tmp"

if [ -f "${BACKUP_DIR}/${BACKUP_NAME}" ]; then
    echo "MinIO Backup completed successfully: ${BACKUP_DIR}/${BACKUP_NAME}"
    
    # Giữ tối đa 30 ngày
    find "$BACKUP_DIR" -name "minio_backup_*.tar.gz" -type f -mtime +30 -delete
else
    echo "MinIO Backup failed!"
    exit 1
fi
