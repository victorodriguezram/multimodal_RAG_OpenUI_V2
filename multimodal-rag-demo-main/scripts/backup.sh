#!/bin/bash

# Backup script for Multimodal RAG System
# Usage: ./backup.sh [backup_name]

set -e

# Configuration
BACKUP_DIR="/opt/rag-backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="${1:-backup_$TIMESTAMP}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Database configuration
DB_CONTAINER="multimodal-rag-demo-main-postgres-1"
DB_NAME="rag_db"
DB_USER="rag_user"

# Redis configuration
REDIS_CONTAINER="multimodal-rag-demo-main-redis-1"

# FAISS index path
FAISS_VOLUME="multimodal-rag-demo-main_faiss_data"

echo "Starting backup process..."
echo "Backup name: $BACKUP_NAME"
echo "Backup path: $BACKUP_PATH"

# Create backup directory
mkdir -p "$BACKUP_PATH"

# 1. Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_PATH/database.sql.gz"

# 2. Backup Redis data
echo "Backing up Redis data..."
docker exec "$REDIS_CONTAINER" redis-cli BGSAVE
sleep 5  # Wait for background save to complete
docker cp "$REDIS_CONTAINER:/data/dump.rdb" "$BACKUP_PATH/redis.rdb"

# 3. Backup FAISS indices
echo "Backing up FAISS indices..."
mkdir -p "$BACKUP_PATH/faiss"
docker run --rm -v "$FAISS_VOLUME:/source" -v "$BACKUP_PATH/faiss:/backup" alpine sh -c "cp -r /source/* /backup/"

# 4. Backup application configuration
echo "Backing up configuration files..."
mkdir -p "$BACKUP_PATH/config"
cp .env "$BACKUP_PATH/config/" 2>/dev/null || echo "No .env file found"
cp docker-compose.yml "$BACKUP_PATH/config/"
cp -r nginx/ "$BACKUP_PATH/config/" 2>/dev/null || echo "No nginx config found"
cp -r monitoring/ "$BACKUP_PATH/config/" 2>/dev/null || echo "No monitoring config found"

# 5. Create backup metadata
echo "Creating backup metadata..."
cat > "$BACKUP_PATH/metadata.json" << EOF
{
  "backup_name": "$BACKUP_NAME",
  "timestamp": "$TIMESTAMP",
  "date": "$(date -Iseconds)",
  "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "services": {
    "database": {
      "container": "$DB_CONTAINER",
      "database": "$DB_NAME",
      "user": "$DB_USER"
    },
    "redis": {
      "container": "$REDIS_CONTAINER"
    },
    "faiss": {
      "volume": "$FAISS_VOLUME"
    }
  }
}
EOF

# 6. Create backup archive
echo "Creating backup archive..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

echo "Backup completed successfully!"
echo "Backup file: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"

# 7. Cleanup old backups (keep last 7 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

# 8. Verify backup
echo "Verifying backup..."
if tar -tzf "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" > /dev/null; then
    echo "Backup verification successful!"
    
    # Get backup size
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)
    echo "Backup size: $BACKUP_SIZE"
    
    # Log successful backup
    echo "$(date -Iseconds): Backup $BACKUP_NAME completed successfully ($BACKUP_SIZE)" >> "$BACKUP_DIR/backup.log"
else
    echo "Backup verification failed!"
    exit 1
fi

echo "Backup process complete!"
