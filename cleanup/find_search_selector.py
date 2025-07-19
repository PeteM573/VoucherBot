#!/usr/bin/env python3
"""
Find the correct search input selector for current Craigslist
"""

import helium
import time
from selenium.webdriver.chrome.options import Options

def find_search_selector():
    """Find the working search input selector"""
    print("🔍 FINDING CORRECT SEARCH SELECTOR")
    print("=" * 40)
    
    try:
        # Start headless browser
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = helium.start_chrome(headless=True, options=chrome_options)
        
        url = "https://newyork.craigslist.org/search/brk/apa?format=list"
        print(f"Testing URL: {url}")
        helium.go_to(url)
        
        time.sleep(2)
        
        # Find all input elements and analyze them
        analysis = driver.execute_script("""
        function findSearchInputs() {
            let inputs = document.querySelectorAll('input');
            let candidates = [];
            
            for (let input of inputs) {
                let info = {
                    tagName: input.tagName,
                    type: input.type,
                    id: input.id,
                    name: input.name,
                    className: input.className,
                    placeholder: input.placeholder,
                    value: input.value,
                    visible: input.offsetParent !== null,
                    width: input.offsetWidth,
                    height: input.offsetHeight
                };
                
                // Look for search-like characteristics
                let isSearchCandidate = (
                    input.type === 'text' || 
                    input.type === 'search' ||
                    (input.placeholder && input.placeholder.toLowerCase().includes('search')) ||
                    (input.name && input.name.toLowerCase().includes('search')) ||
                    (input.id && input.id.toLowerCase().includes('search')) ||
                    (input.className && input.className.toLowerCase().includes('search'))
                );
                
                info.isSearchCandidate = isSearchCandidate;
                info.score = 0;
                
                // Scoring system
                if (input.type === 'search') info.score += 10;
                if (input.type === 'text' && input.offsetWidth > 100) info.score += 5;
                if (input.placeholder && input.placeholder.toLowerCase().includes('search')) info.score += 8;
                if (input.name && input.name.toLowerCase().includes('search')) info.score += 8;
                if (input.id && input.id.toLowerCase().includes('search')) info.score += 8;
                if (input.className && input.className.toLowerCase().includes('search')) info.score += 6;
                if (input.offsetParent !== null) info.score += 3; // visible
                if (input.offsetWidth > 200) info.score += 2; // reasonable width
                
                candidates.push(info);
            }
            
            // Sort by score
            candidates.sort((a, b) => b.score - a.score);
            
            return {
                totalInputs: inputs.length,
                candidates: candidates.slice(0, 10), // Top 10
                topCandidate: candidates[0]
            };
        }
        return findSearchInputs();
        """)
        
        print(f"Total inputs found: {analysis['totalInputs']}")
        print(f"\nTop search candidates:")
        
        for i, candidate in enumerate(analysis['candidates'][:5]):
            print(f"\n{i+1}. Score: {candidate['score']}")
            print(f"   Type: {candidate['type']}")
            print(f"   ID: {candidate['id']}")
            print(f"   Name: {candidate['name']}")
            print(f"   Class: {candidate['className']}")
            print(f"   Placeholder: {candidate['placeholder']}")
            print(f"   Visible: {candidate['visible']}")
            print(f"   Size: {candidate['width']}x{candidate['height']}")
        
        # Test the top candidate
        top = analysis['topCandidate']
        if top and top['score'] > 0:
            print(f"\n🎯 TESTING TOP CANDIDATE:")
            
            # Build selector for top candidate
            selectors_to_try = []
            
            if top['id']:
                selectors_to_try.append(f"#{top['id']}")
            if top['name']:
                selectors_to_try.append(f"input[name='{top['name']}']")
            if top['className']:
                # Try first class
                first_class = top['className'].split()[0] if top['className'] else ""
                if first_class:
                    selectors_to_try.append(f"input.{first_class}")
            
            selectors_to_try.extend([
                f"input[type='{top['type']}']",
                "input[type='text']"
            ])
            
            working_selector = None
            for selector in selectors_to_try:
                try:
                    element = driver.find_element("css selector", selector)
                    if element.is_displayed():
                        working_selector = selector
                        print(f"   ✅ WORKING: {selector}")
                        break
                    else:
                        print(f"   ❌ HIDDEN: {selector}")
                except:
                    print(f"   ❌ NOT FOUND: {selector}")
            
            if working_selector:
                print(f"\n🎉 FOUND WORKING SELECTOR: {working_selector}")
                return working_selector
            else:
                print(f"\n❌ No working selector found for top candidate")
        
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        try:
            helium.kill_browser()
        except:
            pass

if __name__ == "__main__":
    selector = find_search_selector()
    
    if selector:
        print(f"\n🔧 UPDATE NEEDED IN browser_agent.py:")
        print(f"Replace line ~242:")
        print(f'search_selectors = ["{selector}", "input[type=\'text\']"]')
        print(f"\nThis should fix the 'Could not find search interface' error")
    else:
        print(f"\n❌ Could not find a working search selector")
        print(f"Manual investigation may be needed") 