"""
Test script for Phase 8 - Pagination & Advanced Scraping Features
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

print("=" * 60)
print("PHASE 8 - PAGINATION & ADVANCED SCRAPING TEST SUITE")
print("=" * 60)

# Test 1: Pagination Detection
print("\n[TEST 1] Pagination Detection on niftact.com")
print("-" * 60)

test1_payload = {
    "url": "https://niftact.com"
}

try:
    response = requests.post(
        f"{BASE_URL}/detect-pagination",
        json=test1_payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ Pagination Detection Successful")
        print(f"   Has Pagination: {result['pagination']['has_pagination']}")
        print(f"   Pagination Type: {result['pagination'].get('pagination_type', 'N/A')}")
        print(f"   Next Page URL: {result['pagination'].get('next_page_url', 'N/A')}")
        
        if result['page_info']:
            print(f"   Page Info:")
            for key, value in result['page_info'].items():
                print(f"      - {key}: {value}")
    else:
        print(f"❌ Error: {result['error']}")
        print(f"   Message: {result['message']}")
    
except Exception as e:
    print(f"❌ Test Failed: {str(e)}")

# Test 2: Advanced Scraping - Single Page
print("\n[TEST 2] Advanced Scraping - Single Page (h1 selectors)")
print("-" * 60)

test2_payload = {
    "url": "https://niftact.com",
    "selector": "h1",
    "pages": 1
}

try:
    response = requests.post(
        f"{BASE_URL}/scrape-advanced",
        json=test2_payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ Advanced Scraping Successful")
        print(f"   Pages Scraped: {result['pages_scraped']}")
        print(f"   Total Items: {result['total_items']}")
        
        if result['progress']:
            print(f"   Progress: {result['progress']['page_progress']}")
            print(f"   Completion: {result['progress']['percentage']}%")
        
        if result['data']:
            print(f"   Sample Data (first 3 items):")
            for i, item in enumerate(result['data'][:3], 1):
                print(f"      {i}. {item[:50]}..." if len(item) > 50 else f"      {i}. {item}")
    else:
        print(f"❌ Error: {result['error']}")
        print(f"   Message: {result['message']}")
    
except Exception as e:
    print(f"❌ Test Failed: {str(e)}")

# Test 3: Advanced Scraping - With Paragraph Extraction
print("\n[TEST 3] Advanced Scraping - Paragraph Elements (p selectors)")
print("-" * 60)

test3_payload = {
    "url": "https://niftact.com",
    "selector": "p",
    "pages": 1,
    "delay": 0.5
}

try:
    response = requests.post(
        f"{BASE_URL}/scrape-advanced",
        json=test3_payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ Advanced Scraping Successful")
        print(f"   Total Paragraphs: {result['total_items']}")
        print(f"   Pages Scraped: {result['pages_scraped']}")
        
        if result['summary']:
            print(f"   Summary:")
            for key, value in result['summary'].items():
                print(f"      - {key}: {value}")
        
        if result['data']:
            print(f"   Sample Paragraphs (first 2):")
            for i, para in enumerate(result['data'][:2], 1):
                preview = para[:60] + "..." if len(para) > 60 else para
                print(f"      {i}. {preview}")
    else:
        print(f"❌ Error: {result['error']}")
        print(f"   Message: {result['message']}")
    
except Exception as e:
    print(f"❌ Test Failed: {str(e)}")

# Test 4: Pagination Handler Test - Invalid URL
print("\n[TEST 4] Error Handling - Invalid URL")
print("-" * 60)

test4_payload = {
    "url": "invalid-url"
}

try:
    response = requests.post(
        f"{BASE_URL}/detect-pagination",
        json=test4_payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if not result.get('success'):
        print(f"✅ Error Handling Working Correctly")
        print(f"   Error: {result['error']}")
        print(f"   Message: {result['message']}")
    else:
        print(f"❌ Should have failed with invalid URL")
    
except Exception as e:
    print(f"❌ Test Failed: {str(e)}")

# Test 5: Progress Tracking Verification
print("\n[TEST 5] Progress Tracking with Multiple Pages")
print("-" * 60)

test5_payload = {
    "url": "https://niftact.com",
    "selector": ".items",  # Non-existent selector to test error handling
    "pages": 2
}

try:
    response = requests.post(
        f"{BASE_URL}/scrape-advanced",
        json=test5_payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    if 'progress' in result:
        print(f"✅ Progress Tracking Available")
        progress = result['progress']
        print(f"   Total Pages: {progress['total_pages']}")
        print(f"   Pages Completed: {progress['pages_completed']}")
        print(f"   Pages Remaining: {progress['pages_remaining']}")
        print(f"   Items Scraped: {progress['items_scraped']}")
        print(f"   Completion: {progress['percentage']}%")
    
except Exception as e:
    print(f"❌ Test Failed: {str(e)}")

print("\n" + "=" * 60)
print("PHASE 8 TEST SUITE COMPLETED")
print(f"Timestamp: {datetime.utcnow().isoformat()}")
print("=" * 60)
