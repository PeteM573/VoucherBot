import requests
import json
import time
from typing import Dict, Optional, Tuple
from smolagents import Tool
from functools import lru_cache

class GeocodingTool(Tool):
    """
    Tool to convert addresses to latitude/longitude coordinates using free geocoding services.
    Enables other tools like subway proximity to work with address data.
    """
    
    name = "geocode_address"
    description = (
        "Converts a street address to latitude and longitude coordinates. "
        "Takes an address string and returns coordinates that can be used "
        "with other location-based tools like subway proximity finder."
    )
    
    inputs = {
        "address": {
            "type": "string",
            "description": "Street address to convert to coordinates (e.g., 'Nelson Ave near East 181st, Bronx, NY')"
        }
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the geocoding tool with rate limiting."""
        super().__init__()
        self._last_request_time = 0
        self._rate_limit_delay = 1.0  # 1 second between requests to be respectful
        self.is_initialized = True  # Add this attribute that smolagents might expect
        print("🌍 GeocodingTool initialized with rate limiting")
    
    @lru_cache(maxsize=500)
    def _cached_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Cached geocoding function to avoid repeated API calls for same address.
        Uses LRU cache to store up to 500 recent results.
        """
        return self._geocode_with_nominatim(address)
    
    def _rate_limit(self):
        """Implement rate limiting to be respectful to free services."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _geocode_with_nominatim(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode address using OpenStreetMap Nominatim service (free).
        Returns (latitude, longitude) tuple or None if geocoding fails.
        """
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Nominatim API endpoint
            url = "https://nominatim.openstreetmap.org/search"
            
            # Parameters for better NYC results
            params = {
                "q": address,
                "format": "json",
                "addressdetails": 1,
                "limit": 1,
                "countrycodes": "us",
                "bounded": 1,
                "viewbox": "-74.3,40.4,-73.7,40.9",  # NYC bounding box
            }
            
            headers = {
                "User-Agent": "VoucherBot-Geocoder/1.0 (Housing Search Application)"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            results = response.json()
            
            if results and len(results) > 0:
                result = results[0]
                lat = float(result["lat"])
                lon = float(result["lon"])
                
                # Validate coordinates are in NYC area
                if 40.4 <= lat <= 40.9 and -74.3 <= lon <= -73.7:
                    return (lat, lon)
                else:
                    print(f"⚠️ Coordinates outside NYC: {lat}, {lon}")
                    return None
            else:
                print(f"❌ No geocoding results for: {address}")
                return None
                
        except Exception as e:
            print(f"❌ Geocoding error for '{address}': {str(e)}")
            return None
    
    def _format_output(self, address: str, coordinates: Optional[Tuple[float, float]]) -> Dict:
        """Format the geocoding output with comprehensive information."""
        if coordinates:
            lat, lon = coordinates
            return {
                "status": "success",
                "data": {
                    "address": address,
                    "latitude": lat,
                    "longitude": lon,
                    "coordinates": f"{lat},{lon}"
                },
                "metadata": {
                    "service": "OpenStreetMap Nominatim",
                    "timestamp": time.time(),
                    "cached": self._cached_geocode.cache_info().currsize > 0 if hasattr(self._cached_geocode, 'cache_info') else False
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Could not geocode address: {address}",
                "data": None,
                "metadata": {
                    "service": "OpenStreetMap Nominatim",
                    "timestamp": time.time()
                }
            }
    
    def _smart_address_variants(self, address: str) -> list:
        """
        Generate smart address variants for fuzzy addresses like 'E 181st St near clinton ave'.
        Returns a list of address variants to try, ordered by likely success.
        """
        import re
        
        variants = [address]  # Always try original first
        
        # Extract street info
        street_patterns = [
            r'(E\s+\d+(?:st|nd|rd|th)\s+St)',  # E 181st St
            r'(W\s+\d+(?:st|nd|rd|th)\s+St)',  # W 192nd St
            r'(\d+(?:st|nd|rd|th)\s+St)',      # 181st St
            r'([A-Za-z]+\s+Ave)',              # Grand Ave, Clinton Ave
            r'([A-Za-z]+\s+Avenue)',           # Grand Avenue
        ]
        
        # Extract borough
        borough_match = re.search(r'(Bronx|Brooklyn|Manhattan|Queens|Staten Island),?\s*NY', address, re.IGNORECASE)
        borough = borough_match.group(1) if borough_match else ""
        
        # Find streets in the address
        found_streets = []
        for pattern in street_patterns:
            matches = re.findall(pattern, address, re.IGNORECASE)
            found_streets.extend(matches)
        
        # Create variants with different combinations
        if found_streets and borough:
            for street in found_streets:
                # Try just the street with borough
                variants.append(f"{street}, {borough}, NY")
                
                # Try with zip codes for common areas
                if "181" in street and "Bronx" in borough:
                    variants.extend([
                        f"{street}, {borough}, NY 10453",  # Common Bronx zip
                        f"{street}, {borough}, NY 10457",
                        f"{street}, {borough}, NY 10468"
                    ])
                elif "192" in street and "Bronx" in borough:
                    variants.extend([
                        f"{street}, {borough}, NY 10468",  # Kingsbridge area
                        f"{street}, {borough}, NY 10463"
                    ])
        
        # If it's a "near" address, try the main street
        if " near " in address.lower():
            main_part = address.split(" near ")[0].strip()
            if borough:
                variants.append(f"{main_part}, {borough}, NY")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant.lower() not in seen:
                seen.add(variant.lower())
                unique_variants.append(variant)
        
        return unique_variants

    def forward(self, address: str) -> str:
        """
        Convert an address to latitude/longitude coordinates with smart fallback.
        
        Args:
            address: Street address to geocode
            
        Returns:
            JSON string with coordinates or error information
        """
        if not address or not isinstance(address, str):
            error_result = {
                "status": "error",
                "message": "Invalid address: must be a non-empty string",
                "data": None
            }
            return json.dumps(error_result, indent=2)
        
        # Clean up the address
        original_address = address.strip()
        
        print(f"🌍 Geocoding address: {original_address}")
        
        try:
            # Generate smart address variants
            address_variants = self._smart_address_variants(original_address)
            
            coordinates = None
            successful_variant = None
            
            # Try each variant until one works
            for i, variant in enumerate(address_variants):
                if i > 0:  # Don't print for the first (original) attempt
                    print(f"🔄 Trying variant: {variant}")
                
                coordinates = self._cached_geocode(variant)
                if coordinates:
                    successful_variant = variant
                    break
            
            # Format and return result
            if coordinates:
                lat, lon = coordinates
                result = {
                    "status": "success",
                    "data": {
                        "address": original_address,
                        "successful_variant": successful_variant,
                        "latitude": lat,
                        "longitude": lon,
                        "coordinates": f"{lat},{lon}"
                    },
                    "metadata": {
                        "service": "OpenStreetMap Nominatim",
                        "timestamp": time.time(),
                        "variants_tried": len(address_variants),
                        "cached": self._cached_geocode.cache_info().currsize > 0 if hasattr(self._cached_geocode, 'cache_info') else False
                    }
                }
                print(f"✅ Geocoded: {original_address} → ({lat}, {lon}) via '{successful_variant}'")
            else:
                result = {
                    "status": "error", 
                    "message": f"Could not geocode address after trying {len(address_variants)} variants",
                    "data": {
                        "original_address": original_address,
                        "variants_tried": address_variants
                    },
                    "metadata": {
                        "service": "OpenStreetMap Nominatim",
                        "timestamp": time.time(),
                        "variants_tried": len(address_variants)
                    }
                }
                print(f"❌ Failed to geocode: {original_address} (tried {len(address_variants)} variants)")
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Geocoding error: {str(e)}",
                "data": None,
                "metadata": {
                    "timestamp": time.time(),
                    "address": original_address
                }
            }
            print(f"❌ Geocoding exception: {str(e)}")
            return json.dumps(error_result, indent=2)

# Create the tool instance
geocoding_tool = GeocodingTool() 