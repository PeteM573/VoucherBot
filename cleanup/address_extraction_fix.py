#!/usr/bin/env python3
"""
Improved Address Extraction Fix for Browser Agent
Prioritizes complete addresses over intersection descriptions
"""

def improved_address_extraction_script():
    """
    Enhanced JavaScript to extract addresses with better prioritization.
    Prioritizes complete addresses with house numbers and zip codes.
    """
    return """
    function extractBestAddress() {
        let addresses = [];
        let debug = { strategies: [], quality_scores: [] };
        
        // Strategy 1: Look for COMPLETE addresses first (house number + street + borough + zip)
        function findCompleteAddresses() {
            let found = [];
            
            // Look in posting body text for complete addresses
            let bodyEl = document.querySelector('#postingbody') || 
                        document.querySelector('.postingbody') ||
                        document.querySelector('.section-content');
            
            if (bodyEl) {
                let text = bodyEl.textContent;
                // Pattern for complete addresses: number + street + borough + NY + zip
                let completePattern = /(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)\s*,?\s*NY\s+\d{5})/gi;
                let matches = text.match(completePattern);
                if (matches) {
                    found = found.concat(matches.map(m => ({
                        address: m.trim(),
                        source: 'body_complete',
                        quality: 10
                    })));
                }
            }
            
            // Look in attributes for complete addresses  
            let attrGroups = document.querySelectorAll('.attrgroup');
            for (let group of attrGroups) {
                let text = group.textContent;
                let completePattern = /(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)\s*,?\s*NY\s+\d{5})/gi;
                let matches = text.match(completePattern);
                if (matches) {
                    found = found.concat(matches.map(m => ({
                        address: m.trim(),
                        source: 'attrs_complete',
                        quality: 9
                    })));
                }
            }
            
            return found;
        }
        
        // Strategy 2: Look for partial addresses (house number + street + borough)
        function findPartialAddresses() {
            let found = [];
            
            let bodyEl = document.querySelector('#postingbody') || 
                        document.querySelector('.postingbody') ||
                        document.querySelector('.section-content');
            
            if (bodyEl) {
                let text = bodyEl.textContent;
                // Pattern for partial addresses: number + street + borough
                let partialPattern = /(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island))/gi;
                let matches = text.match(partialPattern);
                if (matches) {
                    found = found.concat(matches.map(m => ({
                        address: m.trim(),
                        source: 'body_partial',
                        quality: 7
                    })));
                }
            }
            
            return found;
        }
        
        // Strategy 3: Enhanced title parsing (look for addresses in parentheses or after symbols)
        function findTitleAddresses() {
            let found = [];
            let titleEl = document.querySelector('.postingtitle') ||
                         document.querySelector('#titletextonly');
            
            if (titleEl) {
                let titleText = titleEl.textContent;
                debug.titleText = titleText;
                
                // Look for complete addresses in title
                let completePattern = /(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)\s*,?\s*NY\s*\d{5}?)/gi;
                let matches = titleText.match(completePattern);
                if (matches) {
                    found = found.concat(matches.map(m => ({
                        address: m.trim(),
                        source: 'title_complete',
                        quality: 8
                    })));
                }
                
                // Look for addresses in parentheses or after symbols
                let addressMatch = titleText.match(/[\(\$\-]\s*([^\(\$]+(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)[^\)]*)/i);
                if (addressMatch) {
                    found.push({
                        address: addressMatch[1].trim(),
                        source: 'title_parentheses',
                        quality: 5
                    });
                }
            }
            
            return found;
        }
        
        // Strategy 4: Map address (LOWEST priority - often just intersections)
        function findMapAddresses() {
            let found = [];
            let mapAddress = document.querySelector('.mapaddress') ||
                            document.querySelector('[class*="map-address"]') ||
                            document.querySelector('.postingtitle .mapaddress');
            
            if (mapAddress && mapAddress.textContent.trim()) {
                let addr = mapAddress.textContent.trim();
                // Check if it's a complete address or just intersection
                let quality = addr.includes('near') ? 3 : 
                             /\d+/.test(addr) ? 6 : 4;
                             
                found.push({
                    address: addr,
                    source: 'mapaddress',
                    quality: quality
                });
            }
            
            return found;
        }
        
        // Execute all strategies
        addresses = addresses.concat(findCompleteAddresses());
        addresses = addresses.concat(findPartialAddresses());
        addresses = addresses.concat(findTitleAddresses());
        addresses = addresses.concat(findMapAddresses());
        
        // Remove duplicates and sort by quality
        let uniqueAddresses = [];
        let seen = new Set();
        
        for (let addr of addresses) {
            let normalized = addr.address.toLowerCase().replace(/[^\w\s]/g, '');
            if (!seen.has(normalized)) {
                seen.add(normalized);
                uniqueAddresses.push(addr);
            }
        }
        
        // Sort by quality (highest first)
        uniqueAddresses.sort((a, b) => b.quality - a.quality);
        
        debug.strategies = uniqueAddresses;
        debug.total_found = uniqueAddresses.length;
        debug.best_quality = uniqueAddresses.length > 0 ? uniqueAddresses[0].quality : 0;
        
        let bestAddress = uniqueAddresses.length > 0 ? uniqueAddresses[0].address : null;
        
        return {
            address: bestAddress,
            debug: debug,
            all_candidates: uniqueAddresses
        };
    }
    
    return extractBestAddress();
    """

def apply_improved_address_extraction():
    """Apply the improved address extraction to browser_agent.py"""
    import browser_agent
    
    # Store the original function
    original_function = browser_agent._get_detailed_data_with_enhanced_address
    
    def enhanced_address_extraction(url):
        """Enhanced version with improved address extraction."""
        try:
            import helium
            import json
            
            print(f"🔍 Enhanced address extraction for {url}")
            helium.go_to(url)
            browser_agent._smart_delay(2, 3)
            
            # Use improved extraction script
            extraction_script = improved_address_extraction_script()
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
                location_info: (document.querySelector('.postingtitle small') ||
                               document.querySelector('.location') ||
                               {textContent: null}).textContent
            };
            """
            additional_data = helium.get_driver().execute_script(additional_script)
            
            # Combine results
            final_result = {
                'address': result.get('address') or 'N/A',
                'price': additional_data.get('price', 'N/A'),
                'description': additional_data.get('description', 'N/A'),
                'location_info': additional_data.get('location_info'),
                'debug': result.get('debug', {}),
                'all_candidates': result.get('all_candidates', [])
            }
            
            # Log debug info
            if final_result.get('debug'):
                debug = final_result['debug']
                print(f"📊 Found {debug.get('total_found', 0)} address candidates")
                print(f"🏆 Best quality score: {debug.get('best_quality', 0)}")
                for i, candidate in enumerate(debug.get('strategies', [])[:3], 1):
                    print(f"   {i}. {candidate['address']} (quality: {candidate['quality']}, source: {candidate['source']})")
            
            # Validate and normalize
            if final_result.get('address') and final_result['address'] != 'N/A':
                final_result['address'] = browser_agent._normalize_address(final_result['address'])
                if browser_agent._validate_address(final_result['address']):
                    print(f"✅ Best address: {final_result['address']}")
                else:
                    print(f"❌ Address validation failed: {final_result['address']}")
                    final_result['address'] = 'N/A'
            
            return final_result
            
        except Exception as e:
            print(f"Enhanced extraction failed for {url}: {e}")
            return original_function(url)
    
    # Replace the function
    browser_agent._get_detailed_data_with_enhanced_address = enhanced_address_extraction
    print("✅ Applied improved address extraction to browser agent")

if __name__ == "__main__":
    print("🔧 Improved Address Extraction Fix")
    print("This fix prioritizes complete addresses over intersection descriptions")
    print("Call apply_improved_address_extraction() to activate") 