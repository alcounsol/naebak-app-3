#!/bin/bash

# سكريبت نشر Django على Google Cloud Run
# تأكد من تسجيل الدخول إلى gcloud وتحديد المشروع الصحيح

set -e

# متغيرات المشروع
PROJECT_ID="stalwart-star-468902-j1"
SERVICE_NAME="naebak-service"
REGION="europe-west1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# ألوان للإخراج
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 بدء نشر Django على Cloud Run${NC}"

# التحقق من تسجيل الدخول
echo -e "${YELLOW}📋 التحقق من تسجيل الدخول إلى gcloud...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ يجب تسجيل الدخول إلى gcloud أولاً${NC}"
    echo "تشغيل: gcloud auth login"
    exit 1
fi

# تحديد المشروع
echo -e "${YELLOW}📋 تحديد المشروع: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# بناء الصورة
echo -e "${YELLOW}🔨 بناء صورة Docker...${NC}"
gcloud builds submit --tag ${IMAGE_NAME} .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ فشل في بناء الصورة${NC}"
    exit 1
fi



# نشر الخدمة
echo -e "${YELLOW}🚀 نشر الخدمة على Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.prod,ALLOWED_HOSTS=*,DB_NAME=naebak_db,DB_USER=postgres,DB_PASSWORD=YOUR_DB_PASSWORD,DB_HOST=/cloudsql/naebak:europe-west1:naebak-db-instance,DB_PORT=5432,REDIS_HOST=10.231.192.181,REDIS_PORT=6379" \
    --set-secrets "SECRET_KEY=django-secret-key:latest" \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ تم النشر بنجاح!${NC}"
    
    # الحصول على رابط الخدمة
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)")
    echo -e "${GREEN}🌐 رابط الخدمة: ${SERVICE_URL}${NC}"
    
    # اختبار الخدمة
    echo -e "${YELLOW}🧪 اختبار الخدمة...${NC}"
    if curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL} | grep -q "200\|301\|302"; then
        echo -e "${GREEN}✅ الخدمة تعمل بشكل صحيح${NC}"
    else
        echo -e "${RED}⚠️  قد تكون هناك مشكلة في الخدمة. تحقق من السجلات:${NC}"
        echo "gcloud logs read --service=${SERVICE_NAME} --region=${REGION}"
    fi
else
    echo -e "${RED}❌ فشل في النشر${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 انتهى النشر!${NC}"

