#!/usr/bin/env python3
"""
Balanced Address Extraction Fix
Shows the best available location information to users
Prioritizes complete addresses but falls back to useful approximations
"""

def balanced_address_extraction():
    """
    Balanced extraction that shows users the best available location info.
    Never returns N/A if there's any useful location information.
    """
    return """
    function extractBestLocationInfo() {
        let allLocations = [];
        let debug = { strategies: [], fallbacks: [] };
        
        // Function to score location usefulness (more permissive than before)
        function scoreLocation(location) {
            if (!location || location.length < 3) return 0;
            
            let score = 0;
            let addr = location.toLowerCase();
            
            // Perfect: Full address with house number + street + borough + zip
            if (/\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)\s*,?\s*(?:bronx|brooklyn|manhattan|queens|staten island)\s*,?\s*ny\s+\d{5}/.test(addr)) {
                score = 10;
            }
            // Excellent: Partial address with house number + street + borough
            else if (/\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)\s*,?\s*(?:bronx|brooklyn|manhattan|queens|staten island)/.test(addr)) {
                score = 9;
            }
            // Very Good: Street with house number (missing borough)
            else if (/\d+\s+[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)/.test(addr)) {
                score = 8;
            }
            // Good: Intersection with specific streets
            else if ((addr.includes('near') || addr.includes('&') || addr.includes(' and ')) && 
                     /(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)/.test(addr)) {
                score = 7;
            }
            // Fair: Street name + borough (no house number)
            else if (/[a-z\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|place|pl|lane|ln)\s*,?\s*(?:bronx|brooklyn|manhattan|queens|staten island)/.test(addr)) {
                score = 6;
            }
            // Useful: Neighborhood/area + borough
            else if (/(?:bronx|brooklyn|manhattan|queens|staten island)/.test(addr) && 
                     !/all (bronx|brooklyn|manhattan|queens|staten island) areas/.test(addr) &&
                     addr.length > 10 && addr.length < 100) {
                score = 5;
            }
            // Basic: Just intersection description
            else if (addr.includes('near') && addr.length > 8) {
                score = 4;
            }
            // Minimal: Borough-specific area (better than nothing)
            else if (/(?:bronx|brooklyn|manhattan|queens|staten island)/.test(addr) && addr.length > 5) {
                score = 3;
            }
            
            return score;
        }
        
        // Strategy 1: Look for ALL text that might contain location info
        function findAllLocationMentions() {
            let found = [];
            let searchTexts = [];
            
            // Get main content areas
            let contentAreas = [
                document.querySelector('#postingbody'),
                document.querySelector('.postingbody'),
                document.querySelector('.section-content'),
                document.querySelector('.postingtitle'),
                document.querySelector('#titletextonly')
            ];
            
            // Get map address (often most reliable)
            let mapEl = document.querySelector('.mapaddress') || 
                       document.querySelector('[class*="map-address"]');
            if (mapEl) {
                searchTexts.push(mapEl.textContent);
            }
            
            // Get all text content
            for (let area of contentAreas) {
                if (area && area.textContent) {
                    searchTexts.push(area.textContent);
                }
            }
            
            // Get attribute groups
            let attrGroups = document.querySelectorAll('.attrgroup');
            for (let group of attrGroups) {
                if (group.textContent) {
                    searchTexts.push(group.textContent);
                }
            }
            
            // Extract location info from all text
            for (let text of searchTexts) {
                if (!text) continue;
                
                // Pattern 1: Complete addresses
                let completeMatches = text.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)[^,]*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)[^,]*,?\s*NY\s*\d{0,5}/gi);
                if (completeMatches) {
                    completeMatches.forEach(addr => {
                        found.push({
                            location: addr.trim(),
                            source: 'complete_address',
                            quality: scoreLocation(addr)
                        });
                    });
                }
                
                // Pattern 2: Partial addresses
                let partialMatches = text.match(/\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Place|Pl|Lane|Ln)[^,]*,?\s*(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi);
                if (partialMatches) {
                    partialMatches.forEach(addr => {
                        found.push({
                            location: addr.trim(),
                            source: 'partial_address',
                            quality: scoreLocation(addr)
                        });
                    });
                }
                
                // Pattern 3: Street intersections
                let intersectionMatches = text.match(/[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)\s+(?:near|and|&)\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd)/gi);
                if (intersectionMatches) {
                    intersectionMatches.forEach(addr => {
                        found.push({
                            location: addr.trim(),
                            source: 'intersection',
                            quality: scoreLocation(addr)
                        });
                    });
                }
                
                // Pattern 4: Neighborhood mentions
                let neighborhoodMatches = text.match(/(?:near|in|around|at)\s+[A-Za-z\s]{3,30}(?:Bronx|Brooklyn|Manhattan|Queens|Staten Island)/gi);
                if (neighborhoodMatches) {
                    neighborhoodMatches.forEach(addr => {
                        let cleaned = addr.replace(/^(?:near|in|around|at)\s+/i, '').trim();
                        if (cleaned.length > 8) {
                            found.push({
                                location: cleaned,
                                source: 'neighborhood',
                                quality: scoreLocation(cleaned)
                            });
                        }
                    });
                }
            }
            
            return found;
        }
        
        // Strategy 2: Check for Google Maps or other external location sources
        function findExternalLocationSources() {
            let found = [];
            
            // Check iframes for maps
            let iframes = document.querySelectorAll('iframe');
            for (let iframe of iframes) {
                if (iframe.src && iframe.src.includes('maps')) {
                    let urlMatch = iframe.src.match(/q=([^&]+)/);
                    if (urlMatch) {
                        let addr = decodeURIComponent(urlMatch[1]);
                        found.push({
                            location: addr,
                            source: 'google_maps',
                            quality: scoreLocation(addr)
                        });
                    }
                }
            }
            
            return found;
        }
        
        // Execute all strategies
        allLocations = allLocations.concat(findAllLocationMentions());
        allLocations = allLocations.concat(findExternalLocationSources());
        
        // Remove duplicates and very poor quality locations
        let uniqueLocations = [];
        let seen = new Set();
        
        for (let loc of allLocations) {
            let normalized = loc.location.toLowerCase().replace(/[^\w\s]/g, '').trim();
            if (!seen.has(normalized) && loc.quality > 0 && loc.location.length > 3) {
                // Skip overly generic entries
                if (!loc.location.toLowerCase().includes('all bronx areas') && 
                    !loc.location.toLowerCase().includes('all brooklyn areas') &&
                    !loc.location.toLowerCase().includes('all manhattan areas') &&
                    !loc.location.toLowerCase().includes('all queens areas')) {
                    seen.add(normalized);
                    uniqueLocations.push(loc);
                }
            }
        }
        
        // Sort by quality (best first)
        uniqueLocations.sort((a, b) => b.quality - a.quality);
        
        debug.strategies = uniqueLocations;
        debug.total_found = uniqueLocations.length;
        debug.best_quality = uniqueLocations.length > 0 ? uniqueLocations[0].quality : 0;
        
        // Select best location
        let bestLocation = null;
        if (uniqueLocations.length > 0) {
            bestLocation = uniqueLocations[0].location;
            
            // Add quality indicator for user
            let quality = uniqueLocations[0].quality;
            if (quality >= 8) {
                // Complete address - no indicator needed
                bestLocation = bestLocation;
            } else if (quality >= 6) {
                // Good partial address
                bestLocation = bestLocation;
            } else if (quality >= 4) {
                // Approximate location
                bestLocation = `~${bestLocation}`;
            }
        }
        
        return {
            location: bestLocation,
            debug: debug,
            all_candidates: uniqueLocations
        };
    }
    
    return extractBestLocationInfo();
    """

def apply_balanced_extraction():
    """Apply balanced address extraction to browser agent."""
    import browser_agent
    
    original_function = browser_agent._get_detailed_data_with_enhanced_address
    
    def balanced_extraction(url):
        """Balanced version that shows best available location info."""
        try:
            import helium
            
            print(f"🎯 Balanced location extraction for {url}")
            helium.go_to(url)
            browser_agent._smart_delay(2, 3)
            
            # Use balanced extraction
            extraction_script = balanced_address_extraction()
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
            location = result.get('location')
            if location:
                # Apply light normalization (don't be too aggressive)
                location = browser_agent._normalize_address(location)
                print(f"📍 Found location: {location}")
            else:
                location = 'N/A'
                print(f"❌ No location information found")
            
            final_result = {
                'address': location,
                'price': additional_data.get('price', 'N/A'),
                'description': additional_data.get('description', 'N/A'),
                'title': additional_data.get('title', 'N/A'),
                'debug': result.get('debug', {}),
                'all_candidates': result.get('all_candidates', [])
            }
            
            # Enhanced logging
            if final_result.get('debug'):
                debug = final_result['debug']
                print(f"📊 Found {debug.get('total_found', 0)} location candidates")
                print(f"🏆 Best quality: {debug.get('best_quality', 0)}/10")
                
                if debug.get('strategies'):
                    print(f"🎯 Top candidates:")
                    for i, candidate in enumerate(debug['strategies'][:3], 1):
                        print(f"   {i}. {candidate['location']} (Q:{candidate['quality']}, {candidate['source']})")
            
            return final_result
            
        except Exception as e:
            print(f"Balanced extraction failed for {url}: {e}")
            return original_function(url)
    
    browser_agent._get_detailed_data_with_enhanced_address = balanced_extraction
    print("✅ Applied balanced address extraction to browser agent")

if __name__ == "__main__":
    print("🎯 Balanced Address Extraction Fix")
    print("Shows users the best available location information, even if approximate") 