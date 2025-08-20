import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naebak_project.settings")
django.setup()

from django.contrib.auth import get_user_model
from naebak.models import Citizen, Candidate, Governorate, FeaturedCandidate

User = get_user_model()

def add_demo_data():
    print("Adding demo data...")

    # Create Governorates if they don\'t exist
    suez_governorate, created = Governorate.objects.get_or_create(name="السويس")
    if created:
        print("Governorate \'السويس\' created.")
    cairo_governorate, created = Governorate.objects.get_or_create(name="القاهرة")
    if created:
        print("Governorate \'القاهرة\' created.")

    # Add 5 Citizens
    citizens_data = [
        {"first_name": "مواطن", "last_name": "سويس1", "email": "suez_citizen1@example.com", "phone_number": "01000000001", "governorate": suez_governorate, "area_type": "مدينة", "area_name": "السويس", "address": "شارع 1، حي الأربعين"},
        {"first_name": "مواطن", "last_name": "سويس2", "email": "suez_citizen2@example.com", "phone_number": "01000000002", "governorate": suez_governorate, "area_type": "حي", "area_name": "فيصل", "address": "شارع 2، حي فيصل"},
        {"first_name": "مواطن", "last_name": "سويس3", "email": "suez_citizen3@example.com", "phone_number": "01000000003", "governorate": suez_governorate, "area_type": "قرية", "area_name": "جناين", "address": "شارع 3، جناين"},
        {"first_name": "مواطن", "last_name": "سويس4", "email": "suez_citizen4@example.com", "phone_number": "01000000004", "governorate": suez_governorate, "area_type": "مركز", "area_name": "عتاقة", "address": "شارع 4، عتاقة"},
        {"first_name": "مواطن", "last_name": "قاهرة1", "email": "cairo_citizen1@example.com", "phone_number": "01000000005", "governorate": cairo_governorate, "area_type": "مدينة", "area_name": "القاهرة", "address": "شارع 5، مدينة نصر"},
    ]

    for data in citizens_data:
        user, created = User.objects.get_or_create(username=data["email"], defaults={"email": data["email"], "first_name": data["first_name"], "last_name": data["last_name"]})
        if created:
            user.set_password("password123")
            user.save()
        Citizen.objects.get_or_create(user=user, defaults=data)
        print(f"Citizen {data['first_name']} {data['last_name']} added/updated.")

    # Add 6 Candidates for Suez
    candidates_data = [
        {"first_name": "مرشح", "last_name": "سويس1", "email": "suez_candidate1@example.com", "phone_number": "01200000001", "governorate_id": suez_governorate.id, "constituency": "السويس", "bio": "مرشح للبرلمان من السويس", "electoral_program": "برنامج انتخابي 1", "facebook_url": "https://facebook.com/suez_candidate1"},
        {"first_name": "مرشح", "last_name": "سويس2", "email": "suez_candidate2@example.com", "phone_number": "01200000002", "governorate_id": suez_governorate.id, "constituency": "السويس", "bio": "مرشح للبرلمان من السويس", "electoral_program": "برنامج انتخابي 2", "facebook_url": "https://facebook.com/suez_candidate2"},
        {"first_name": "مرشح", "last_name": "سويس3", "email": "suez_candidate3@example.com", "phone_number": "01200000003", "governorate_id": suez_governorate.id, "constituency": "السويس", "bio": "مرشح للبرلمان من السويس", "electoral_program": "برنامج انتخابي 3", "facebook_url": "https://facebook.com/suez_candidate3"},
        {"first_name": "مرشح", "last_name": "سويس4", "email": "suez_candidate4@example.com", "phone_number": "01200000004", "governorate_id": suez_governorate.id, "constituency": "السويس", "bio": "مرشح للبرلمان من السويس", "electoral_program": "برنامج انتخابي 4", "facebook_url": "https://facebook.com/suez_candidate4"},
        {"first_name": "مرشح", "last_name": "سويس5", "email": "suez_candidate5@example.com", "phone_number": "01200000005", "governorate_id": suez_governorate.id, "constituency": "السويس", "bio": "مرشح للبرلمان من السويس", "electoral_program": "برنامج انتخابي 5", "facebook_url": "https://facebook.com/suez_candidate5"},
        {"first_name": "مرشح", "last_name": "سويس6", "email": "suez_candidate6@example.com", "phone_number": "01200000006", "governorate_id": suez_governorate.id, "constituency": "السويس", "bio": "مرشح للبرلمان من السويس", "electoral_program": "برنامج انتخابي 6", "facebook_url": "https://facebook.com/suez_candidate6"},
    ]

    for data in candidates_data:
        user, created = User.objects.get_or_create(username=data["email"], defaults={"email": data["email"], "first_name": data["first_name"], "last_name": data["last_name"]})
        if created:
            user.set_password("password123")
            user.save()
        # Remove fields that are part of the User model before passing to Candidate.objects.get_or_create
        candidate_defaults = {k: v for k, v in data.items() if k not in ["first_name", "last_name", "email"]}
        candidate, _ = Candidate.objects.get_or_create(user=user, defaults=candidate_defaults)
        candidate.is_featured = True
        candidate.save()
        print(f'Candidate {data["first_name"]} {data["last_name"]} added/updated as featured.')

if __name__ == "__main__":
    add_demo_data()




    print("Demo data added successfully!")

