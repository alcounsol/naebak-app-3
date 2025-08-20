#!/bin/bash

# Deployment script for Naebak project
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-prod}
PROJECT_NAME="naebak"

echo "🚀 Starting deployment for environment: $ENVIRONMENT"

# Check if required environment variables are set
if [ "$ENVIRONMENT" = "prod" ]; then
    required_vars=("DB_NAME" "DB_USER" "DB_PASSWORD" "SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Error: $var environment variable is not set"
            exit 1
        fi
    done
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements/${ENVIRONMENT}.txt

# Set Django settings module
export DJANGO_SETTINGS_MODULE=config.settings.${ENVIRONMENT}

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (only for dev/test)
if [ "$ENVIRONMENT" != "prod" ]; then
    echo "👤 Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@naebak.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"
fi

# Load demo data (only for dev/test)
if [ "$ENVIRONMENT" != "prod" ]; then
    echo "📊 Loading demo data..."
    if [ -f "scripts/load_demo_data.py" ]; then
        python manage.py shell < scripts/load_demo_data.py
    fi
fi

# Run tests (only for test environment)
if [ "$ENVIRONMENT" = "test" ]; then
    echo "🧪 Running tests..."
    python manage.py test
fi

# Start the application
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🌐 Starting production server..."
    gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 120 config.wsgi:application
else
    echo "🔧 Starting development server..."
    python manage.py runserver 0.0.0.0:8000
fi

