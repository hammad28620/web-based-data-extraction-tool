import requests
import json

BASE_URL = "http://localhost:5000"

# Test 1: Check supported platforms
print("🔍 Getting supported platforms...")
response = requests.get(f"{BASE_URL}/social/platforms")
platforms = response.json()
print(json.dumps(platforms, indent=2))
print("\n" + "="*60 + "\n")

# Test 2: Scrape Twitter profile
print("📱 Scraping Twitter profile...")
response = requests.post(f"{BASE_URL}/social/scrape-profile", json={
    "platform": "twitter",
    "username": "nasa"
})
profile = response.json()
print(json.dumps(profile, indent=2))
print("\n" + "="*60 + "\n")

# Test 3: Scrape Instagram posts
print("📸 Scraping Instagram posts...")
response = requests.post(f"{BASE_URL}/social/scrape-posts", json={
    "platform": "instagram",
    "username": "nasa",
    "limit": 5
})
posts = response.json()
print(json.dumps(posts, indent=2))
