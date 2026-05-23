#!/bin/bash
# Script sao lưu MongoDB sử dụng mongodump

# Xác định thư mục của script hiện tại
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load biến môi trường nếu có từ thư mục cha
if [ -f "$SCRIPT_DIR/../.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/../.env" | xargs)
fi

DB_NAME=${MONGODB_DB_NAME:-"ban_do_sv_sp"}
BACKUP_DIR="$SCRIPT_DIR/../backups/mongodb"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="mongodb_backup_${DB_NAME}_${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

echo "Starting MongoDB backup for database: ${DB_NAME}..."

# Thực hiện mongodump qua Docker
docker exec ban-do-mongodb-dev mongodump --db "${DB_NAME}" --archive="/data/db/${BACKUP_NAME}.archive"

# Di chuyển file archive ra thư mục backup local
docker cp "ban-do-mongodb-dev:/data/db/${BACKUP_NAME}.archive" "${BACKUP_DIR}/${BACKUP_NAME}.archive"

# Xóa file tạm trong container
docker exec ban-do-mongodb-dev rm "/data/db/${BACKUP_NAME}.archive"

if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.archive" ]; then
    echo "Backup completed successfully: ${BACKUP_DIR}/${BACKUP_NAME}.archive"
    
    # Giữ tối đa 30 ngày
    find "$BACKUP_DIR" -name "mongodb_backup_*.archive" -type f -mtime +30 -delete
else
    echo "Backup failed!"
    exit 1
fi
