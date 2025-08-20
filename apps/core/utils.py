"""
Utility functions for core app
"""

import json
import os
from django.conf import settings
from django.core.cache import cache


def load_governorates_data():
    """
    Load governorates data from JSON file with caching
    """
    cache_key = 'governorates_data'
    governorates = cache.get(cache_key)
    
    if governorates is None:
        json_file_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'governorates.json')
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                governorates = data.get('governorates', [])
                # Cache for 1 hour
                cache.set(cache_key, governorates, 3600)
        except FileNotFoundError:
            # Try alternative path
            json_file_path = os.path.join(settings.BASE_DIR, 'naebak', 'data', 'governorates.json')
            try:
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    governorates = data.get('governorates', [])
                    cache.set(cache_key, governorates, 3600)
            except FileNotFoundError:
                print(f"Governorates JSON file not found at: {json_file_path}")
                governorates = []
        except json.JSONDecodeError:
            print(f"Error decoding JSON file: {json_file_path}")
            governorates = []
    
    return governorates


def get_governorate_by_id(gov_id):
    """
    Get a specific governorate by ID
    """
    governorates = load_governorates_data()
    for gov in governorates:
        if gov['id'] == int(gov_id):
            return gov
    return None


def get_governorate_by_slug(slug):
    """
    Get a specific governorate by slug
    """
    governorates = load_governorates_data()
    for gov in governorates:
        if gov['slug'] == slug:
            return gov
    return None


def get_governorates_choices():
    """
    Get governorates as choices for Django forms
    Returns list of tuples (id, name_ar)
    """
    governorates = load_governorates_data()
    return [(gov['id'], gov['name_ar']) for gov in governorates]


def get_governorates_by_region():
    """
    Get governorates grouped by region
    """
    governorates = load_governorates_data()
    regions = {}
    
    for gov in governorates:
        region = gov.get('region', 'أخرى')
        if region not in regions:
            regions[region] = []
        regions[region].append(gov)
    
    return regions


def search_governorates(query):
    """
    Search governorates by name (Arabic or English)
    """
    governorates = load_governorates_data()
    query = query.lower().strip()
    
    if not query:
        return governorates
    
    results = []
    for gov in governorates:
        if (query in gov['name_ar'].lower() or 
            query in gov['name_en'].lower() or 
            query in gov.get('description', '').lower()):
            results.append(gov)
    
    return results


def format_number(number):
    """
    Format number with Arabic thousands separator
    """
    if number is None:
        return "0"
    
    # Convert to string and add thousands separator
    return f"{number:,}".replace(',', '،')


def truncate_text(text, max_length=100):
    """
    Truncate text to specified length with ellipsis
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length].rsplit(' ', 1)[0] + "..."


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Get user agent from request
    """
    return request.META.get('HTTP_USER_AGENT', '')


def calculate_percentage(part, total):
    """
    Calculate percentage with proper handling of zero division
    """
    if total == 0:
        return 0
    return round((part / total) * 100, 1)


def generate_slug(text):
    """
    Generate URL-friendly slug from Arabic text
    """
    import re
    from django.utils.text import slugify
    
    # Remove Arabic diacritics
    arabic_diacritics = re.compile(r'[\u064B-\u0652\u0670\u0640]')
    text = arabic_diacritics.sub('', text)
    
    # Replace Arabic characters with English equivalents
    arabic_to_english = {
        'ا': 'a', 'أ': 'a', 'إ': 'a', 'آ': 'a',
        'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
        'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'th',
        'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
        'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z',
        'ع': 'a', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
        'ه': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a',
        'ة': 'h', 'ء': 'a'
    }
    
    result = ''
    for char in text:
        if char in arabic_to_english:
            result += arabic_to_english[char]
        elif char.isalnum() or char in '-_':
            result += char
        else:
            result += '-'
    
    # Use Django's slugify for final cleanup
    return slugify(result)


def validate_egyptian_phone(phone):
    """
    Validate Egyptian phone number format
    """
    import re
    
    if not phone:
        return False
    
    # Remove spaces and special characters
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Egyptian phone patterns
    patterns = [
        r'^(\+20|0020|20)?1[0125]\d{8}$',  # Mobile numbers
        r'^(\+20|0020|20)?[2-9]\d{7,8}$',  # Landline numbers
    ]
    
    for pattern in patterns:
        if re.match(pattern, phone):
            return True
    
    return False


def format_egyptian_phone(phone):
    """
    Format Egyptian phone number to standard format
    """
    import re
    
    if not phone:
        return ""
    
    # Remove spaces and special characters
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Remove country code if present
    if phone.startswith('+20'):
        phone = phone[3:]
    elif phone.startswith('0020'):
        phone = phone[4:]
    elif phone.startswith('20'):
        phone = phone[2:]
    
    # Add leading zero if mobile number
    if len(phone) == 10 and phone[0] == '1':
        phone = '0' + phone
    
    return phone

