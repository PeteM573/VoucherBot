#!/usr/bin/env python3
"""
Quick check of Craigslist to see what's happening
"""

import helium
import time
from selenium.webdriver.chrome.options import Options

def quick_craigslist_check():
    """Quick check of what's on the Craigslist page"""
    print("🔍 QUICK CRAIGSLIST CHECK")
    print("=" * 30)
    
    try:
        # Start headless browser
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = helium.start_chrome(headless=True, options=chrome_options)
        
        # Test Brooklyn URL
        url = "https://newyork.craigslist.org/search/brk/apa?format=list"
        print(f"Testing URL: {url}")
        helium.go_to(url)
        
        time.sleep(2)
        
        # Get basic page info
        page_info = driver.execute_script("""
        return {
            title: document.title,
            url: window.location.href,
            bodyText: document.body.textContent.substring(0, 500),
            hasSearchInput: !!document.querySelector('input'),
            inputCount: document.querySelectorAll('input').length,
            hasQuery: !!document.querySelector('#query'),
            hasSearchForm: !!document.querySelector('form')
        };
        """)
        
        print(f"Page Title: {page_info['title']}")
        print(f"Current URL: {page_info['url']}")
        print(f"Has Search Input: {page_info['hasSearchInput']}")
        print(f"Input Count: {page_info['inputCount']}")
        print(f"Has #query: {page_info['hasQuery']}")
        print(f"Has Form: {page_info['hasSearchForm']}")
        print(f"Body Text Preview: {page_info['bodyText'][:200]}...")
        
        # Check if we're redirected or blocked
        if "craigslist.org" not in page_info['url']:
            print("❌ REDIRECTED: Not on Craigslist anymore")
        elif "blocked" in page_info['bodyText'].lower():
            print("❌ BLOCKED: Access blocked")
        elif page_info['inputCount'] == 0:
            print("❌ NO INPUTS: Page has no input elements")
        elif not page_info['hasQuery']:
            print("⚠️ NO #query: Search box selector changed")
        else:
            print("✅ PAGE LOOKS OK: Basic elements present")
        
        return page_info
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        try:
            helium.kill_browser()
        except:
            pass

if __name__ == "__main__":
    result = quick_craigslist_check()
    
    if result:
        if not result['hasQuery'] and result['hasSearchInput']:
            print("\n🔧 LIKELY FIX NEEDED:")
            print("The #query selector is not working, but there are input elements.")
            print("Need to update search selectors in browser_agent.py")
        elif not result['hasSearchInput']:
            print("\n🚨 MAJOR ISSUE:")
            print("No input elements found. Craigslist may have changed significantly.")
    else:
        print("\n❌ Could not diagnose the issue") 