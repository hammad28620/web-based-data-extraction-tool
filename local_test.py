"""
Local testing script - Test the application without network access
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from scraper.validators import validate_url, validate_selector, validate_scrape_request
from scraper.data_processor import DataProcessor
from scraper.csv_exporter import CSVExporter
import tempfile

print("=" * 70)
print("WEB-BASED DATA EXTRACTION TOOL - LOCAL TEST MODE")
print("=" * 70)

# Test 1: Input Validation
print("\n[TEST 1] Input Validation")
print("-" * 70)

test_urls = [
    ("https://example.com", True),
    ("http://example.com", True),
    ("invalid-url", False),
    ("ftp://example.com", False),
]

for url, should_pass in test_urls:
    try:
        validate_url(url)
        result = "✅ PASS" if should_pass else "❌ FAIL (should reject)"
    except:
        result = "❌ FAIL" if should_pass else "✅ PASS (correctly rejected)"
    print(f"  {url:40} {result}")

# Test 2: CSS Selector Validation
print("\n[TEST 2] CSS Selector Validation")
print("-" * 70)

test_selectors = [
    ("div", True),
    (".class-name", True),
    ("#id-name", True),
    ("div.class > p", True),
    ("", False),
    ("<script>alert('xss')</script>", False),
]

for selector, should_pass in test_selectors:
    try:
        validate_selector(selector)
        result = "✅ PASS" if should_pass else "❌ FAIL (should reject)"
    except:
        result = "❌ FAIL" if should_pass else "✅ PASS (correctly rejected)"
    print(f"  {selector:40} {result}")

# Test 3: Data Processing
print("\n[TEST 3] Data Processing")
print("-" * 70)

processor = DataProcessor()

# Create sample data
sample_data = ['Product A', 'Product B', '  Product C  ', 'Product B', 'Product D']
print(f"  Input data ({len(sample_data)} items): {sample_data}")

# Create DataFrame
df = processor.create_dataframe(sample_data)
print(f"  ✅ DataFrame created: {len(df)} rows")

# Clean data
cleaned_df = processor.clean_dataframe(df)
print(f"  ✅ Data cleaned: {len(cleaned_df)} rows")

# Remove duplicates
dedup_df = processor.remove_duplicates(cleaned_df)
print(f"  ✅ Duplicates removed: {len(dedup_df)} rows")

# Get summary
summary = processor.get_data_summary(dedup_df)
print(f"  ✅ Summary generated: {summary['rows']} rows, {summary['columns']} columns")

# Test 4: CSV Export
print("\n[TEST 4] CSV Export")
print("-" * 70)

exporter = CSVExporter()

with tempfile.TemporaryDirectory() as tmpdir:
    exporter = CSVExporter(output_dir=tmpdir)
    
    # Export data
    filename = exporter.generate_filename(prefix='test')
    success, filepath = exporter.export_to_csv(dedup_df, filename)
    print(f"  ✅ File exported: {filename}")
    
    # List exports
    files = exporter.list_exports()
    print(f"  ✅ Exports listed: {len(files)} file(s)")
    
    # Get file info
    file_info = exporter.get_file_info(filepath)
    print(f"  ✅ File info: {file_info['size_bytes']} bytes")

# Test 5: Scrape Request Validation
print("\n[TEST 5] Complete Scrape Request Validation")
print("-" * 70)

valid_request = {
    "url": "https://example.com",
    "selector": "div.item"
}

try:
    result = validate_scrape_request(valid_request)
    print(f"  ✅ Valid request accepted: {result['url']}")
except Exception as e:
    print(f"  ❌ Valid request rejected: {str(e)}")

invalid_request = {
    "url": "not-a-url",
    "selector": "div"
}

try:
    validate_scrape_request(invalid_request)
    print(f"  ❌ Invalid request accepted")
except Exception as e:
    print(f"  ✅ Invalid request correctly rejected: {str(e)}")

# Summary
print("\n" + "=" * 70)
print("LOCAL TEST COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Start Flask server: .venv\\Scripts\\python.exe run.py")
print("2. Try with a simpler URL: https://example.com or https://httpbin.org")
print("3. Check internet connection if still having issues")
print("4. Run full test suite: .venv\\Scripts\\pytest.exe tests/")
print("=" * 70)
