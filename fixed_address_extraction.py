#!/usr/bin/env python3
"""
Fixed Address Extraction - Prioritizes Real Address Sources
Based on debug findings: .mapaddress and JSON structured data contain the real addresses
"""

def fixed_address_extraction():
    """
    Fixed extraction that finds real addresses from proper sources.
    Avoids title contamination by prioritizing mapaddress and structured data.
    """
    return """
    function extractRealAddress() {
        let candidates = [];
        let debug = { sources: {}, title_avoided: false };
        
        // Function to score address quality
        function scoreAddress(addr, source) {
            if (!addr || addr.length < 3) return 0;
            
            let score = 0;
            let text = addr.toLowerCase().trim();
            
            // Boost score based on reliable source
            let sourceBonus = 0;
            if (source === 'structured_data') sourceBonus = 5;
            else if (source === 'mapaddress') sourceBonus = 4;
            else if (source === 'body_text') sourceBonus = 2;
            else if (source === 'title') sourceBonus = -10; // AVOID TITLES
            
            // Score the content quality
            if (/\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)\s*,?\s*(?:bronx|brooklyn|manhattan|queens|staten island)\s*,?\s*ny\s+\d{5}/.test(text)) {
                score = 10 + sourceBonus;
            }
            else if (/\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)\s*,?\s*(?:bronx|brooklyn|manhattan|queens|staten island)/.test(text)) {
                score = 9 + sourceBonus;
            }
            else if (/\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)/.test(text)) {
                score = 8 + sourceBonus;
            }
            else if (/[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)\s*,?\s*(?:bronx|brooklyn|manhattan|queens|staten island)/.test(text)) {
                score = 6 + sourceBonus;
            }
            else if (text.includes('near') && /(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)/.test(text)) {
                score = 5 + sourceBonus;
            }
            else if (/(?:bronx|brooklyn|manhattan|queens|staten island)/.test(text) && 
                     !text.includes('all ') && !text.includes('newly renovated') && 
                     !text.includes('bedroom') && text.length > 8 && text.length < 60) {
                score = 4 + sourceBonus;
            }
            
            // Penalty for title-like content
            if (text.includes('br apt') || text.includes('bedroom') || text.includes('renovated') || 
                text.includes('$') || text.includes('/') || text.includes('newly')) {
                score -= 15;
            }
            
            return Math.max(0, score);
        }
        
        // Strategy 1: Extract from JSON-LD structured data (highest priority)
        function extractFromStructuredData() {
            let found = [];
            let scripts = document.querySelectorAll('script[type*="json"]');
            
            for (let script of scripts) {
                try {
                    let data = JSON.parse(script.textContent);
                    
                    // Look for address objects
                    function findAddresses(obj) {
                        if (typeof obj !== 'object' || obj === null) return;
                        
                        if (obj.streetAddress) {
                            let addr = obj.streetAddress;
                            if (obj.addressLocality) addr += ', ' + obj.addressLocality;
                            if (obj.addressRegion) addr += ', ' + obj.addressRegion;
                            if (obj.postalCode) addr += ' ' + obj.postalCode;
                            
                            found.push({
                                address: addr.trim(),
                                source: 'structured_data',
                                quality: scoreAddress(addr, 'structured_data')
                            });
                        }
                        
                        // Recursively search nested objects
                        for (let key in obj) {
                            if (typeof obj[key] === 'object') {
                                findAddresses(obj[key]);
                            }
                        }
                    }
                    
                    findAddresses(data);
                } catch (e) {
                    // Invalid JSON, skip
                }
            }
            
            return found;
        }
        
        // Strategy 2: Extract from mapaddress element (second highest priority)
        function extractFromMapAddress() {
            let found = [];
            let mapSelectors = [
                '.mapaddress',
                '[class*="mapaddress"]',
                '.postingtitle .mapaddress'
            ];
            
            for (let selector of mapSelectors) {
                let elements = document.querySelectorAll(selector);
                for (let el of elements) {
                    if (el.textContent && el.textContent.trim()) {
                        let addr = el.textContent.trim();
                        found.push({
                            address: addr,
                            source: 'mapaddress',
                            quality: scoreAddress(addr, 'mapaddress')
                        });
                    }
                }
            }
            
            return found;
        }
        
        // Strategy 3: Extract from body text (careful to avoid title contamination)
        function extractFromBodyText() {
            let found = [];
            let bodySelectors = ['#postingbody', '.postingbody', '.section-content'];
            
            for (let selector of bodySelectors) {
                let elements = document.querySelectorAll(selector);
                for (let el of elements) {
                    if (el.textContent && el.textContent.trim()) {
                        let text = el.textContent;
                        
                        // Look for address patterns
                        let patterns = [
                            /\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)\s*,?\s*NY\s*\d{0,5}/gi,
                            /\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi,
                            /(?:Near|At|On)\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)\s*(?:and|&|near)\s*[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)/gi
                        ];
                        
                        for (let pattern of patterns) {
                            let matches = text.match(pattern);
                            if (matches) {
                                matches.forEach(addr => {
                                    found.push({
                                        address: addr.trim(),
                                        source: 'body_text',
                                        quality: scoreAddress(addr, 'body_text')
                                    });
                                });
                            }
                        }
                    }
                }
            }
            
            return found;
        }
        
        // Strategy 4: Extract from title ONLY as last resort (with penalties)
        function extractFromTitle() {
            let found = [];
            let titleEl = document.querySelector('.postingtitle') || 
                         document.querySelector('#titletextonly');
            
            if (titleEl && titleEl.textContent) {
                let titleText = titleEl.textContent;
                
                // Look for parenthetical location info like "(Fordham Vicinity)"
                let locMatch = titleText.match(/\(([^)]+(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)[^)]*)\)/i);
                if (locMatch) {
                    let location = locMatch[1].trim();
                    if (!location.includes('bedroom') && !location.includes('br ') && 
                        !location.includes('renovated') && location.length > 5) {
                        found.push({
                            address: location,
                            source: 'title_location',
                            quality: scoreAddress(location, 'title')
                        });
                    }
                }
                
                // Avoid extracting the main title as address
                debug.title_avoided = true;
            }
            
            return found;
        }
        
        // Execute strategies in priority order
        candidates = candidates.concat(extractFromStructuredData());
        candidates = candidates.concat(extractFromMapAddress());
        candidates = candidates.concat(extractFromBodyText());
        candidates = candidates.concat(extractFromTitle());
        
        // Remove duplicates and filter out poor quality
        let uniqueCandidates = [];
        let seen = new Set();
        
        for (let candidate of candidates) {
            let normalized = candidate.address.toLowerCase().replace(/[^\w\s]/g, '');
            if (!seen.has(normalized) && candidate.quality > 0) {
                seen.add(normalized);
                uniqueCandidates.push(candidate);
            }
        }
        
        // Sort by quality (highest first)
        uniqueCandidates.sort((a, b) => b.quality - a.quality);
        
        debug.total_candidates = uniqueCandidates.length;
        debug.candidates = uniqueCandidates;
        debug.best_quality = uniqueCandidates.length > 0 ? uniqueCandidates[0].quality : 0;
        
        // Select best address
        let bestAddress = null;
        if (uniqueCandidates.length > 0 && uniqueCandidates[0].quality > 3) {
            bestAddress = uniqueCandidates[0].address;
            
            // Clean up the address
            bestAddress = bestAddress.replace(/^(Near|At|On)\s+/i, '');
            bestAddress = bestAddress.trim();
        }
        
        return {
            address: bestAddress,
            debug: debug,
            all_candidates: uniqueCandidates
        };
    }
    
    return extractRealAddress();
    """

def apply_fixed_extraction():
    """Apply the fixed address extraction to browser agent."""
    import browser_agent
    
    original_function = browser_agent._get_detailed_data_with_enhanced_address
    
    def fixed_extraction(url):
        """Fixed version that finds real addresses and avoids title contamination."""
        try:
            import helium
            
            print(f"🔧 Fixed address extraction for {url}")
            helium.go_to(url)
            browser_agent._smart_delay(2, 3)
            
            # Use fixed extraction script
            extraction_script = fixed_address_extraction()
            result = helium.get_driver().execute_script(extraction_script)
            
            # Get additional data
            additional_script = """
            return {
                price: (document.querySelector('.price') || 
                       document.querySelector('[class*="price"]') || 
                       {textContent: 'N/A'}).textContent.trim(),
                description: (document.querySelector('#postingbody') || 
                             document.querySelector('.postingbody') ||
                             {textContent: 'N/A'}).textContent.trim(),
                title: (document.querySelector('.postingtitle') ||
                       {textContent: 'N/A'}).textContent.trim()
            };
            """
            additional_data = helium.get_driver().execute_script(additional_script)
            
            # Process results
            address = result.get('address')
            if address:
                # Light normalization
                address = browser_agent._normalize_address(address)
                print(f"📍 Found address: {address}")
            else:
                address = 'N/A'
                print(f"❌ No address found")
            
            final_result = {
                'address': address,
                'price': additional_data.get('price', 'N/A'),
                'description': additional_data.get('description', 'N/A'),
                'title': additional_data.get('title', 'N/A'),
                'debug': result.get('debug', {}),
                'all_candidates': result.get('all_candidates', [])
            }
            
            # Enhanced logging
            if final_result.get('debug'):
                debug = final_result['debug']
                print(f"📊 Found {debug.get('total_candidates', 0)} address candidates")
                print(f"🏆 Best quality: {debug.get('best_quality', 0)}/10")
                print(f"🚫 Title avoided: {debug.get('title_avoided', False)}")
                
                if debug.get('candidates'):
                    print(f"🎯 Top candidates:")
                    for i, candidate in enumerate(debug['candidates'][:3], 1):
                        print(f"   {i}. {candidate['address']} (Q:{candidate['quality']}, {candidate['source']})")
            
            return final_result
            
        except Exception as e:
            print(f"Fixed extraction failed for {url}: {e}")
            return original_function(url)
    
    browser_agent._get_detailed_data_with_enhanced_address = fixed_extraction
    print("✅ Applied fixed address extraction to browser agent")

if __name__ == "__main__":
    print("🔧 Fixed Address Extraction")
    print("Prioritizes mapaddress and structured data, avoids title contamination") 