#!/usr/bin/env python3
"""
Script to load demo data for Naebak project
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.core.models import Governorate
from apps.accounts.models import Citizen
from apps.candidates.models import Candidate, ElectoralPromise
from apps.news.models import News

User = get_user_model()

def create_governorates():
    """Create governorates"""
    governorates_data = [
        {'name': 'القاهرة', 'name_en': 'Cairo'},
        {'name': 'الجيزة', 'name_en': 'Giza'},
        {'name': 'الإسكندرية', 'name_en': 'Alexandria'},
        {'name': 'السويس', 'name_en': 'Suez'},
        {'name': 'أسوان', 'name_en': 'Aswan'},
        {'name': 'الأقصر', 'name_en': 'Luxor'},
    ]
    
    for gov_data in governorates_data:
        gov, created = Governorate.objects.get_or_create(
            name=gov_data['name'],
            defaults={'name_en': gov_data['name_en']}
        )
        if created:
            print(f"Created governorate: {gov.name}")

def create_citizens():
    """Create demo citizens"""
    suez = Governorate.objects.get(name='السويس')
    cairo = Governorate.objects.get(name='القاهرة')
    
    citizens_data = [
        {'username': 'citizen1', 'email': 'citizen1@example.com', 'first_name': 'أحمد', 'last_name': 'محمد', 'governorate': suez},
        {'username': 'citizen2', 'email': 'citizen2@example.com', 'first_name': 'فاطمة', 'last_name': 'علي', 'governorate': suez},
        {'username': 'citizen3', 'email': 'citizen3@example.com', 'first_name': 'محمد', 'last_name': 'أحمد', 'governorate': suez},
        {'username': 'citizen4', 'email': 'citizen4@example.com', 'first_name': 'عائشة', 'last_name': 'حسن', 'governorate': suez},
        {'username': 'citizen5', 'email': 'citizen5@example.com', 'first_name': 'عمر', 'last_name': 'خالد', 'governorate': cairo},
    ]
    
    for citizen_data in citizens_data:
        user, created = User.objects.get_or_create(
            username=citizen_data['username'],
            defaults={
                'email': citizen_data['email'],
                'first_name': citizen_data['first_name'],
                'last_name': citizen_data['last_name'],
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            
            citizen, created = Citizen.objects.get_or_create(
                user=user,
                defaults={
                    'governorate': citizen_data['governorate'],
                    'phone': '01234567890',
                    'national_id': f'123456789{user.id:02d}',
                }
            )
            if created:
                print(f"Created citizen: {user.get_full_name()}")

def create_candidates():
    """Create demo candidates"""
    suez = Governorate.objects.get(name='السويس')
    
    candidates_data = [
        {
            'name': 'د. أحمد السيد',
            'bio': 'طبيب ومهندس، خبرة 20 سنة في الخدمة العامة',
            'age': 45,
            'profession': 'طبيب',
            'education': 'دكتوراه في الطب',
            'experience': 'عضو مجلس محلي سابق',
        },
        {
            'name': 'أ. فاطمة محمد',
            'bio': 'محامية ومدافعة عن حقوق المرأة',
            'age': 38,
            'profession': 'محامية',
            'education': 'ليسانس حقوق',
            'experience': 'رئيسة جمعية نسائية',
        },
        {
            'name': 'م. محمد علي',
            'bio': 'مهندس مدني، خبرة في مشاريع البنية التحتية',
            'age': 42,
            'profession': 'مهندس',
            'education': 'بكالوريوس هندسة مدنية',
            'experience': 'مدير مشاريع حكومية',
        },
        {
            'name': 'د. عائشة حسن',
            'bio': 'أستاذة جامعية في علوم التربية',
            'age': 50,
            'profession': 'أستاذة جامعية',
            'education': 'دكتوراه في التربية',
            'experience': 'عميدة كلية سابقة',
        },
        {
            'name': 'أ. عمر خالد',
            'bio': 'رجل أعمال ومؤسس شركات ناشئة',
            'age': 35,
            'profession': 'رجل أعمال',
            'education': 'ماجستير إدارة أعمال',
            'experience': 'رئيس غرفة تجارة',
        },
        {
            'name': 'د. نورا أحمد',
            'bio': 'طبيبة أطفال ومتخصصة في الصحة العامة',
            'age': 40,
            'profession': 'طبيبة',
            'education': 'دكتوراه في طب الأطفال',
            'experience': 'مديرة مستشفى',
        },
    ]
    
    for candidate_data in candidates_data:
        candidate, created = Candidate.objects.get_or_create(
            name=candidate_data['name'],
            defaults={
                'governorate': suez,
                'bio': candidate_data['bio'],
                'age': candidate_data['age'],
                'profession': candidate_data['profession'],
                'education': candidate_data['education'],
                'experience': candidate_data['experience'],
                'is_featured': True,
            }
        )
        if created:
            print(f"Created candidate: {candidate.name}")
            
            # Add electoral promises
            promises = [
                'تحسين الخدمات الصحية',
                'تطوير البنية التحتية',
                'دعم التعليم والشباب',
                'تنمية الاقتصاد المحلي',
            ]
            
            for promise_text in promises:
                ElectoralPromise.objects.create(
                    candidate=candidate,
                    title=promise_text,
                    description=f"تفاصيل {promise_text} للمحافظة",
                    priority='high'
                )

def create_news():
    """Create demo news"""
    news_data = [
        {
            'title': 'افتتاح مشروع تطوير الطرق في السويس',
            'summary': 'تم افتتاح مشروع جديد لتطوير شبكة الطرق في محافظة السويس',
            'content': 'تفاصيل المشروع وأهدافه...',
            'is_ticker': True,
        },
        {
            'title': 'مؤتمر للتنمية المستدامة',
            'summary': 'عقد مؤتمر حول التنمية المستدامة بحضور المرشحين',
            'content': 'تفاصيل المؤتمر والمشاركين...',
            'is_ticker': True,
        },
        {
            'title': 'حملة توعية صحية',
            'summary': 'إطلاق حملة توعية صحية للمواطنين',
            'content': 'تفاصيل الحملة وأهدافها...',
            'is_ticker': False,
        },
    ]
    
    for news_item in news_data:
        news, created = News.objects.get_or_create(
            title=news_item['title'],
            defaults={
                'summary': news_item['summary'],
                'content': news_item['content'],
                'is_ticker': news_item['is_ticker'],
                'is_published': True,
            }
        )
        if created:
            print(f"Created news: {news.title}")

def main():
    """Main function to load all demo data"""
    print("Loading demo data...")
    
    try:
        create_governorates()
        create_citizens()
        create_candidates()
        create_news()
        print("✅ Demo data loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading demo data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

