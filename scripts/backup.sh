#!/bin/bash

# Backup script for Naebak project
# Usage: ./scripts/backup.sh

set -e

BACKUP_DIR="/tmp/naebak_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="naebak_backup_${TIMESTAMP}"

echo "📦 Starting backup process..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Set Django settings
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Database backup
echo "🗄️ Backing up database..."
python manage.py dumpdata --natural-foreign --natural-primary \
    --exclude=contenttypes --exclude=auth.permission \
    --exclude=sessions.session --exclude=admin.logentry \
    > "${BACKUP_DIR}/${BACKUP_NAME}_data.json"

# Media files backup
echo "📁 Backing up media files..."
if [ -d "media" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_media.tar.gz" media/
fi

# Static files backup (optional)
echo "🎨 Backing up static files..."
if [ -d "staticfiles" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_static.tar.gz" staticfiles/
fi

# Configuration backup
echo "⚙️ Backing up configuration..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz" \
    config/ requirements/ scripts/ docker/ \
    manage.py .env.example

# Create complete backup archive
echo "📦 Creating complete backup archive..."
cd $BACKUP_DIR
tar -czf "${BACKUP_NAME}_complete.tar.gz" ${BACKUP_NAME}_*

# Cleanup individual files
rm -f ${BACKUP_NAME}_data.json ${BACKUP_NAME}_media.tar.gz \
      ${BACKUP_NAME}_static.tar.gz ${BACKUP_NAME}_config.tar.gz

echo "✅ Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}_complete.tar.gz"

# Upload to cloud storage (if configured)
if [ ! -z "$GS_BUCKET_NAME" ]; then
    echo "☁️ Uploading backup to Google Cloud Storage..."
    gsutil cp "${BACKUP_DIR}/${BACKUP_NAME}_complete.tar.gz" \
        "gs://${GS_BUCKET_NAME}/backups/"
    echo "✅ Backup uploaded to cloud storage"
fi

# Cleanup old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR -name "naebak_backup_*.tar.gz" -mtime +7 -delete

echo "🎉 Backup process completed successfully!"

