#!/bin/bash

# Restore script for Multimodal RAG System
# Usage: ./restore.sh <backup_name_or_file>

set -e

# Configuration
BACKUP_DIR="/opt/rag-backups"
RESTORE_TEMP="/tmp/rag-restore"

# Check if backup name/file provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_name_or_file>"
    echo ""
    echo "Available backups:"
    ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_INPUT="$1"

# Determine backup file path
if [[ "$BACKUP_INPUT" == *.tar.gz ]]; then
    # Full path provided
    BACKUP_FILE="$BACKUP_INPUT"
elif [[ "$BACKUP_INPUT" == */* ]]; then
    # Relative or absolute path
    BACKUP_FILE="$BACKUP_INPUT"
else
    # Just backup name
    BACKUP_FILE="$BACKUP_DIR/${BACKUP_INPUT}.tar.gz"
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Starting restore process..."
echo "Backup file: $BACKUP_FILE"

# Create temporary restore directory
rm -rf "$RESTORE_TEMP"
mkdir -p "$RESTORE_TEMP"

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_TEMP"

# Find extracted directory
EXTRACTED_DIR=$(find "$RESTORE_TEMP" -mindepth 1 -maxdepth 1 -type d | head -n1)
if [ -z "$EXTRACTED_DIR" ]; then
    echo "Error: No directory found in backup"
    exit 1
fi

echo "Extracted to: $EXTRACTED_DIR"

# Read backup metadata
if [ -f "$EXTRACTED_DIR/metadata.json" ]; then
    echo "Backup metadata:"
    cat "$EXTRACTED_DIR/metadata.json"
    echo ""
else
    echo "Warning: No metadata found in backup"
fi

# Confirm restore
read -p "Are you sure you want to restore this backup? This will overwrite existing data. (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    rm -rf "$RESTORE_TEMP"
    exit 0
fi

# Stop services
echo "Stopping services..."
docker-compose down

# Database configuration
DB_CONTAINER="multimodal-rag-demo-main-postgres-1"
DB_NAME="rag_db"
DB_USER="rag_user"
REDIS_CONTAINER="multimodal-rag-demo-main-redis-1"
FAISS_VOLUME="multimodal-rag-demo-main_faiss_data"

# Start only database and redis for restore
echo "Starting database and redis services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# 1. Restore PostgreSQL database
if [ -f "$EXTRACTED_DIR/database.sql.gz" ]; then
    echo "Restoring PostgreSQL database..."
    
    # Drop and recreate database
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"
    
    # Restore data
    gunzip -c "$EXTRACTED_DIR/database.sql.gz" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"
    echo "Database restored successfully"
else
    echo "Warning: No database backup found"
fi

# 2. Restore Redis data
if [ -f "$EXTRACTED_DIR/redis.rdb" ]; then
    echo "Restoring Redis data..."
    docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL
    docker cp "$EXTRACTED_DIR/redis.rdb" "$REDIS_CONTAINER:/data/dump.rdb"
    docker-compose restart redis
    echo "Redis data restored successfully"
else
    echo "Warning: No Redis backup found"
fi

# 3. Restore FAISS indices
if [ -d "$EXTRACTED_DIR/faiss" ]; then
    echo "Restoring FAISS indices..."
    docker volume rm "$FAISS_VOLUME" 2>/dev/null || true
    docker volume create "$FAISS_VOLUME"
    docker run --rm -v "$EXTRACTED_DIR/faiss:/source" -v "$FAISS_VOLUME:/target" alpine sh -c "cp -r /source/* /target/"
    echo "FAISS indices restored successfully"
else
    echo "Warning: No FAISS backup found"
fi

# 4. Restore configuration files
if [ -d "$EXTRACTED_DIR/config" ]; then
    echo "Restoring configuration files..."
    
    # Backup current config
    mkdir -p "/tmp/config_backup_$(date +%s)"
    cp .env "/tmp/config_backup_$(date +%s)/" 2>/dev/null || true
    
    # Restore config
    cp "$EXTRACTED_DIR/config/.env" . 2>/dev/null || echo "No .env in backup"
    cp -r "$EXTRACTED_DIR/config/nginx/" . 2>/dev/null || echo "No nginx config in backup"
    cp -r "$EXTRACTED_DIR/config/monitoring/" . 2>/dev/null || echo "No monitoring config in backup"
    
    echo "Configuration files restored"
else
    echo "Warning: No configuration backup found"
fi

# Start all services
echo "Starting all services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Verify restoration
echo "Verifying restoration..."

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
fi

# Check UI
if curl -f http://localhost:8501 > /dev/null 2>&1; then
    echo "✅ UI is accessible"
else
    echo "❌ UI health check failed"
fi

# Check database
if docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database is accessible"
else
    echo "❌ Database connection failed"
fi

# Check Redis
if docker exec "$REDIS_CONTAINER" redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is accessible"
else
    echo "❌ Redis connection failed"
fi

# Cleanup
echo "Cleaning up temporary files..."
rm -rf "$RESTORE_TEMP"

echo ""
echo "Restore process completed!"
echo "Please verify that all services are working correctly."
echo ""
echo "Services status:"
docker-compose ps
