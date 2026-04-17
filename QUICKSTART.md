"""
Quick Start Guide - Web-Based Data Extraction Tool
How to run and use the application
"""

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.14+ installed
- Virtual environment activated (.venv)
- All dependencies installed (requirements.txt)

---

## 1️⃣ RUNNING THE APPLICATION

### Step 1: Navigate to Project Directory
```powershell
cd "e:\semester 4\OS\project\web-based-data-extraction-tool"
```

### Step 2: Activate Virtual Environment (if not already active)
```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Start Flask Server
```powershell
.venv\Scripts\python.exe run.py
```

**Expected Output:**
```
2026-04-11 12:00:00,000 - app - INFO - Flask app initialized in DevelopmentConfig mode
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### Step 4: Open Web Browser
Visit: **http://localhost:5000**

---

## 2️⃣ USING THE APPLICATION

### Basic Scraping Workflow

1. **Enter Website URL** 
   - Example: `https://example.com`
   - Protocol required (http:// or https://)

2. **Enter CSS Selector**
   - Extract h1 headers: `h1`
   - Extract by class: `.article`
   - Extract by ID: `#main`
   - Extract paragraphs: `p`
   - Complex: `div.container > article`

3. **Click "Scrape"**
   - System extracts matching elements
   - Removes HTML tags automatically
   - Displays in table format

4. **Process Results** (Optional)
   - Remove duplicates
   - Handle missing values
   - Validate data

5. **Download CSV**
   - Click "Download CSV"
   - File saved locally

---

## 3️⃣ TIMEOUT TROUBLESHOOTING

### Problem: "Request timeout after 30 seconds"

**Solution 1: Try Simple Websites First**
- `https://example.com`
- `https://httpbin.org`
- `https://quotes.toscrape.com`

**Solution 2: Check Internet Connection**
```powershell
# Test DNS resolution
nslookup google.com

# Test connection
Test-NetConnection -ComputerName google.com -Port 443
```

**Solution 3: Increase Timeout**
Edit `config.py`:
```python
REQUEST_TIMEOUT = 60  # Increase from 30 to 60 seconds
```

**Solution 4: Try Different Selectors**
Some pages load dynamically. Try simpler selectors:
- `h1` instead of `div.header > h1`
- `p` instead of `article > p`

---

## 4️⃣ COMMON CSS SELECTORS

| Selector | Example | Matches |
|----------|---------|---------|
| Tag name | `p` | All paragraphs |
| Class | `.price` | All elements with class "price" |
| ID | `#header` | Element with id "header" |
| Descendant | `div p` | All p inside div |
| Child | `div > p` | Direct p children of div |
| Attribute | `a[href]` | All links with href |
| Multiple | `.item, .product` | Items OR products |

---

## 5️⃣ RUNNING TESTS

```powershell
# All tests
.venv\Scripts\pytest.exe tests/ -v

# Specific module
.venv\Scripts\pytest.exe tests/test_validators.py -v

# With coverage
.venv\Scripts\pytest.exe tests/ --cov=scraper --cov=app
```

---

## 6️⃣ KEY IMPROVEMENTS IN LATEST BUILD

✅ **Timeout increased to 30 seconds** (from 10s)
- Handles slow websites better
- Can be increased further if needed

✅ **Automatic HTML tag removal**
- Clean text extraction
- No extra whitespace
- Properly formatted output

✅ **Better error messages**
- Clear feedback on failures
- Suggestions for fixing issues
- Detailed logging

✅ **Rate limiting**
- Prevents server overload
- 10-20 requests per minute per endpoint
- 50 requests per hour per IP

---

## 7️⃣ PROJECT STATUS

**Completed Phases:** 9/10 ✅
- Phase 1-9: Fully implemented and tested
- Phase 10: Documentation (in progress)

**111 Tests Passing** ✅
- 33 validator tests
- 25 data processor tests
- 32 integration tests
- 15 security tests
- 6+ performance tests

---

## 8️⃣ TROUBLESHOOTING GUIDE

### Issue: "Cannot connect to website"
**Causes & Solutions:**
- ❌ No internet → Check network
- ❌ Firewall blocking → Allow Flask through firewall
- ❌ Website down → Try different website
- ❌ DNS issues → Reset DNS or use different resolver

### Issue: "No data found"
**Causes & Solutions:**
- ❌ Wrong selector → Inspect page (F12) and find correct selector
- ❌ Dynamic content → Website may load content with JavaScript
- ❌ Bot detection → Try with fewer/slower requests
- ❌ Empty selector result → Selector matches no elements

### Issue: "Request timeout"
**Causes & Solutions:**
- ❌ Slow website → Increase REQUEST_TIMEOUT in config.py
- ❌ Large page → Website may have heavy content
- ❌ Network issues → Test with ping or tracert
- ❌ Server overloaded → Retry after delay

### Issue: "CSV download fails"
**Causes & Solutions:**
- ❌ No data to export → Scrape successfully first
- ❌ Disk full → Free up space
- ❌ Permission denied → Check folder permissions
- ❌ File deleted → Restart Flask app

---

## 9️⃣ ADVANCED USAGE

### Multi-page Scraping
```
Use /scrape-advanced endpoint:

{
  "url": "https://example.com",
  "selector": ".item",
  "pages": 3,
  "delay": 1.5
}
```

### Pagination Detection
```
POST to /detect-pagination:

{
  "url": "https://example.com"
}

Response shows if pagination detected
```

### Custom Delay Between Requests
```
Set in /scrape-advanced:

"delay": 2.0  # 2 second delay between pages
```

---

## 🔟 GETTING HELP

Check these files for more info:
- `README.md` - Project overview
- `PHASES.md` - Development phases
- `TEST_RESULTS.md` - Test coverage
- `logs/scraper.log` - Detailed logs
- `app/__init__.py` - All flask routes

---

## Quick Command Reference

```powershell
# Start app
.venv\Scripts\python.exe run.py

# Run tests
.venv\Scripts\pytest.exe tests/ -v

# Run specific test
.venv\Scripts\pytest.exe tests/test_validators.py -v

# Check syntax
.venv\Scripts\python.exe -m py_compile app/__init__.py

# Install new package
.venv\Scripts\pip.exe install package_name

# View logs
Get-Content logs/scraper.log -Tail 50
```

---

**Last Updated:** April 11, 2026
**Version:** 1.0 (Phase 9 Complete)
**Status:** Production Ready ✅
