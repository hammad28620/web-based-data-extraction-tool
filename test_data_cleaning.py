#!/usr/bin/env python3
"""
Quick test to demonstrate data cleaning functionality
"""

import sys
sys.path.insert(0, '.')

from scraper.scraper_engine import ScraperEngine
import json

def test_cleaning():
    """Test the data cleaning on a real website"""
    
    # Initialize scraper
    scraper = ScraperEngine(request_timeout=10, scraping_delay=1)
    
    # Test URLs
    test_urls = [
        'https://example.com',
        'https://en.wikipedia.org/wiki/Web_scraping',
    ]
    
    for url in test_urls:
        print(f"\n{'='*80}")
        print(f"Testing URL: {url}")
        print(f"{'='*80}")
        
        try:
            # Scrape without selector (extracts all cleaned content)
            result = scraper.scrape(url=url, selector=None, include_attributes=False)
            
            if result['success']:
                data = result['data']
                print(f"\n[OK] Successfully extracted {len(data)} cleaned content items\n")
                
                # Show first 5 items
                print("Sample of cleaned content (first 5 items):")
                print("-" * 80)
                for i, item in enumerate(data[:5], 1):
                    # Truncate long items
                    display_text = item if len(item) <= 100 else item[:100] + "..."
                    print(f"{i}. {display_text}")
                
                if len(data) > 5:
                    print(f"\n... and {len(data) - 5} more items")
                    print("\nLast 3 items:")
                    print("-" * 80)
                    for i, item in enumerate(data[-3:], len(data) - 2):
                        display_text = item if len(item) <= 100 else item[:100] + "..."
                        print(f"{i}. {display_text}")
            else:
                print(f"\n[ERROR] Scraping failed: {result.get('error')}")
        
        except Exception as e:
            print(f"\n[ERROR] Error: {str(e)}")

if __name__ == '__main__':
    test_cleaning()
