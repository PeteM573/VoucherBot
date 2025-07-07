#!/usr/bin/env python3
"""
Comprehensive Address Extraction Fix
Handles Google Maps, JavaScript content, and all address sources
"""

def comprehensive_address_extraction():
    """
    Most comprehensive address extraction script that checks ALL possible sources.
    """
    return """
    function extractAllAddresses() {
        let allAddresses = [];
        let debug = { sources: {}, raw_content: {} };
        
        // Function to score address quality
        function scoreAddress(addr) {
            if (!addr || addr.length < 5) return 0;
            
            let score = 0;
            // Full address with house number + street + borough + state + zip
            if (/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)\s*,?\s*NY\s+\d{5}/.test(addr)) {
                score = 10;
            }
            // Partial address with house number + street + borough
            else if (/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/.test(addr)) {
                score = 8;
            }
            // Street with house number
            else if (/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)/.test(addr)) {
                score = 6;
            }
            // Intersection
            else if (addr.includes('near') || addr.includes('&') || addr.includes(' and ')) {
                score = 4;
            }
            // Generic area
            else if (/bronx|brooklyn|manhattan|queens|staten/i.test(addr)) {
                score = 2;
            }
            
            return score;
        }
        
        // 1. Check all text elements for addresses
        function scanAllTextElements() {
            let found = [];
            let allElements = document.querySelectorAll('*');
            
            for (let el of allElements) {
                if (el.children.length === 0 && el.textContent.trim()) {
                    let text = el.textContent.trim();
                    
                    // Full address patterns
                    let fullMatches = text.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)\s*,?\s*NY\s*\d{5}?/gi);
                    if (fullMatches) {
                        fullMatches.forEach(addr => {
                            found.push({
                                address: addr.trim(),
                                source: 'text_scan_full',
                                element: el.tagName.toLowerCase(),
                                quality: scoreAddress(addr)
                            });
                        });
                    }
                    
                    // Partial address patterns  
                    let partialMatches = text.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi);
                    if (partialMatches) {
                        partialMatches.forEach(addr => {
                            found.push({
                                address: addr.trim(),
                                source: 'text_scan_partial',
                                element: el.tagName.toLowerCase(),
                                quality: scoreAddress(addr)
                            });
                        });
                    }
                }
            }
            
            return found;
        }
        
        // 2. Check all data attributes and hidden content
        function scanDataAttributes() {
            let found = [];
            let allElements = document.querySelectorAll('*');
            
            for (let el of allElements) {
                // Check all attributes
                for (let attr of el.attributes || []) {
                    if (attr.value && attr.value.length > 10) {
                        let matches = attr.value.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi);
                        if (matches) {
                            matches.forEach(addr => {
                                found.push({
                                    address: addr.trim(),
                                    source: 'data_attribute',
                                    attribute: attr.name,
                                    quality: scoreAddress(addr)
                                });
                            });
                        }
                    }
                }
            }
            
            return found;
        }
        
        // 3. Check iframe content (Google Maps)
        function scanIframes() {
            let found = [];
            let iframes = document.querySelectorAll('iframe');
            
            for (let iframe of iframes) {
                if (iframe.src && (iframe.src.includes('maps') || iframe.src.includes('google'))) {
                    // Extract from Google Maps URL parameters
                    let url = iframe.src;
                    
                    // Look for address in URL parameters
                    let addressMatch = url.match(/q=([^&]+)/);
                    if (addressMatch) {
                        let addr = decodeURIComponent(addressMatch[1]);
                        if (scoreAddress(addr) > 0) {
                            found.push({
                                address: addr,
                                source: 'google_maps_url',
                                quality: scoreAddress(addr)
                            });
                        }
                    }
                    
                    // Look for coordinates that might be converted
                    let coordMatch = url.match(/[@!](-?\d+\.\d+),(-?\d+\.\d+)/);
                    if (coordMatch) {
                        found.push({
                            address: `Coordinates: ${coordMatch[1]}, ${coordMatch[2]}`,
                            source: 'google_maps_coords',
                            quality: 3
                        });
                    }
                }
            }
            
            return found;
        }
        
        // 4. Check meta tags and structured data
        function scanMetaData() {
            let found = [];
            
            // Check meta tags
            let metaTags = document.querySelectorAll('meta[property], meta[name]');
            for (let meta of metaTags) {
                if (meta.content && meta.content.length > 10) {
                    let matches = meta.content.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi);
                    if (matches) {
                        matches.forEach(addr => {
                            found.push({
                                address: addr.trim(),
                                source: 'meta_tag',
                                property: meta.getAttribute('property') || meta.getAttribute('name'),
                                quality: scoreAddress(addr)
                            });
                        });
                    }
                }
            }
            
            // Check JSON-LD structured data
            let scripts = document.querySelectorAll('script[type="application/ld+json"]');
            for (let script of scripts) {
                try {
                    let data = JSON.parse(script.textContent);
                    let dataStr = JSON.stringify(data);
                    let matches = dataStr.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)\s*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi);
                    if (matches) {
                        matches.forEach(addr => {
                            found.push({
                                address: addr.trim(),
                                source: 'structured_data',
                                quality: scoreAddress(addr)
                            });
                        });
                    }
                } catch (e) {
                    // Invalid JSON, skip
                }
            }
            
            return found;
        }
        
        // 5. Wait for and check dynamic content
        function scanDynamicContent() {
            return new Promise((resolve) => {
                let found = [];
                let checkCount = 0;
                let maxChecks = 10;
                
                function checkForNewAddresses() {
                    checkCount++;
                    
                    // Look for any new address-containing elements
                    let newElements = document.querySelectorAll('[data-address], .address, .location, .geo');
                    for (let el of newElements) {
                        if (el.textContent && el.textContent.trim()) {
                            let addr = el.textContent.trim();
                            if (scoreAddress(addr) > 0) {
                                found.push({
                                    address: addr,
                                    source: 'dynamic_content',
                                    quality: scoreAddress(addr)
                                });
                            }
                        }
                    }
                    
                    if (checkCount < maxChecks) {
                        setTimeout(checkForNewAddresses, 200);
                    } else {
                        resolve(found);
                    }
                }
                
                checkForNewAddresses();
            });
        }
        
        // Execute all scanning methods
        try {
            // Immediate scans
            allAddresses = allAddresses.concat(scanAllTextElements());
            allAddresses = allAddresses.concat(scanDataAttributes());
            allAddresses = allAddresses.concat(scanIframes());
            allAddresses = allAddresses.concat(scanMetaData());
            
            // Store debug info
            debug.sources = {
                text_scan: allAddresses.filter(a => a.source.includes('text_scan')).length,
                data_attributes: allAddresses.filter(a => a.source === 'data_attribute').length,
                google_maps: allAddresses.filter(a => a.source.includes('google_maps')).length,
                meta_data: allAddresses.filter(a => a.source.includes('meta')).length
            };
            
            // Remove duplicates and sort by quality
            let uniqueAddresses = [];
            let seen = new Set();
            
            for (let addr of allAddresses) {
                let normalized = addr.address.toLowerCase().replace(/[^\w\s]/g, '');
                if (!seen.has(normalized) && addr.address.length > 5) {
                    seen.add(normalized);
                    uniqueAddresses.push(addr);
                }
            }
            
            uniqueAddresses.sort((a, b) => b.quality - a.quality);
            
            debug.total_candidates = uniqueAddresses.length;
            debug.best_quality = uniqueAddresses.length > 0 ? uniqueAddresses[0].quality : 0;
            debug.all_candidates = uniqueAddresses;
            
            let bestAddress = uniqueAddresses.length > 0 ? uniqueAddresses[0].address : null;
            
            return {
                address: bestAddress,
                debug: debug,
                all_candidates: uniqueAddresses
            };
            
        } catch (error) {
            debug.error = error.toString();
            return {
                address: null,
                debug: debug,
                all_candidates: []
            };
        }
    }
    
    return extractAllAddresses();
    """

def apply_comprehensive_extraction():
    """Apply comprehensive address extraction to browser agent."""
    import browser_agent
    
    original_function = browser_agent._get_detailed_data_with_enhanced_address
    
    def comprehensive_extraction(url):
        """Enhanced version with comprehensive address extraction."""
        try:
            import helium
            
            print(f"🔍 Comprehensive address extraction for {url}")
            helium.go_to(url)
            browser_agent._smart_delay(3, 4)  # Wait longer for dynamic content
            
            # Use comprehensive extraction
            extraction_script = comprehensive_address_extraction()
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
            
            # Combine results
            final_result = {
                'address': result.get('address') or 'N/A',
                'price': additional_data.get('price', 'N/A'),
                'description': additional_data.get('description', 'N/A'),
                'title': additional_data.get('title', 'N/A'),
                'debug': result.get('debug', {}),
                'all_candidates': result.get('all_candidates', [])
            }
            
            # Enhanced logging
            if final_result.get('debug'):
                debug = final_result['debug']
                print(f"📊 Comprehensive scan found {debug.get('total_candidates', 0)} total candidates")
                print(f"🔍 Sources: {debug.get('sources', {})}")
                print(f"🏆 Best quality: {debug.get('best_quality', 0)}")
                
                if debug.get('all_candidates'):
                    print(f"🎯 Top 5 candidates:")
                    for i, candidate in enumerate(debug['all_candidates'][:5], 1):
                        print(f"   {i}. {candidate['address']} (Q:{candidate['quality']}, {candidate['source']})")
            
            # Validate best address
            if final_result.get('address') and final_result['address'] != 'N/A':
                final_result['address'] = browser_agent._normalize_address(final_result['address'])
                if browser_agent._validate_address(final_result['address']):
                    print(f"✅ Best address: {final_result['address']}")
                else:
                    print(f"❌ Address validation failed: {final_result['address']}")
                    final_result['address'] = 'N/A'
            
            return final_result
            
        except Exception as e:
            print(f"Comprehensive extraction failed for {url}: {e}")
            return original_function(url)
    
    browser_agent._get_detailed_data_with_enhanced_address = comprehensive_extraction
    print("✅ Applied comprehensive address extraction to browser agent")

if __name__ == "__main__":
    print("🔧 Comprehensive Address Extraction Fix")
    print("Scans ALL possible address sources including Google Maps and dynamic content") 