import requests

# Test the web interface is running
response = requests.get('http://127.0.0.1:5000')

if response.status_code == 200:
    html = response.text
    
    # Check for social media elements
    checks = {
        'Social Media Tab': '📱 Social Media Scraper' in html,
        'Profile Tab': '👤 Profile' in html,
        'Posts Tab': '📝 Posts' in html,
        'Platform Select': 'platformSelect' in html,
        'Username Input': 'usernameInput' in html,
        'Social Media JS': 'social_media.js' in html,
        'Profile Form': 'socialProfileForm' in html,
        'Posts Form': 'socialPostsForm' in html,
    }
    
    print("✅ Web Interface Integration Check:\n")
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}: {'Found' if result else 'Missing'}")
    
    all_passed = all(checks.values())
    if all_passed:
        print("\n✅ All checks passed! Social media scraper is integrated.")
    else:
        print("\n⚠️ Some elements are missing.")
else:
    print(f"❌ Server error: {response.status_code}")
