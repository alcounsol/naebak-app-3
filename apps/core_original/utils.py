"""
Utility functions for naebak app
"""

import json
import os
from django.conf import settings


def load_governorates_data():
    """
    Load governorates data from JSON file
    Returns list of governorate dictionaries
    """
    json_file_path = os.path.join(settings.BASE_DIR, 'naebak', 'data', 'governorates.json')
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('governorates', [])
    except FileNotFoundError:
        print(f"Governorates JSON file not found at: {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON file: {json_file_path}")
        return []


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

