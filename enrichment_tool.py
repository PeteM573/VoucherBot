import json
from typing import Dict, List, Any, Optional
from smolagents import Tool
from nearest_subway_tool import nearest_subway_tool
from near_school_tool import near_school_tool
from violation_checker_agent import ViolationCheckerAgent
from datetime import datetime
import asyncio
import time

class EnrichmentTool(Tool):
    """
    Advanced tool to enrich housing listings with building violations, subway proximity, and school data.
    Combines multiple data sources to provide comprehensive listing information.
    """
    
    name = "enrich_listings"
    description = (
        "Enriches housing listings with building violation data, nearest subway station information, "
        "and nearby school data. Takes a list of listings and returns them with added safety, "
        "transit accessibility, and education access data."
    )
    
    inputs = {
        "listings": {
            "type": "string",
            "description": "JSON string containing a list of housing listings to enrich. Each listing should have 'address', 'latitude', 'longitude' fields."
        }
    }
    output_type = "string"
    
    def __init__(self):
        """Initialize the enrichment tool with violation checker."""
        super().__init__()
        self.violation_checker = ViolationCheckerAgent()
        self.is_initialized = True  # Add this attribute that smolagents might expect
        print("🔧 EnrichmentTool initialized with violation checking, subway proximity, and school data")
    
    def _extract_coordinates(self, listing: Dict) -> Optional[tuple]:
        """Extract latitude and longitude from listing data."""
        try:
            # Try different possible field names for coordinates
            lat_fields = ['latitude', 'lat', 'coords_lat', 'location_lat']
            lon_fields = ['longitude', 'lon', 'lng', 'coords_lon', 'location_lon']
            
            lat = None
            lon = None
            
            for field in lat_fields:
                if field in listing and listing[field] is not None:
                    lat = float(listing[field])
                    break
            
            for field in lon_fields:
                if field in listing and listing[field] is not None:
                    lon = float(listing[field])
                    break
            
            if lat is not None and lon is not None:
                return (lat, lon)
            
            # If no direct coordinates, try to extract from nested objects
            if 'location' in listing and isinstance(listing['location'], dict):
                location = listing['location']
                lat = location.get('latitude') or location.get('lat')
                lon = location.get('longitude') or location.get('lon')
                if lat is not None and lon is not None:
                    return (float(lat), float(lon))
            
            return None
            
        except (ValueError, TypeError, KeyError):
            return None
    
    def _get_building_violations(self, listing: Dict) -> Dict:
        """Get building violation data for a listing."""
        try:
            # Extract address for violation checking
            address = listing.get('address') or listing.get('title', '')
            
            if not address:
                return {
                    "violation_count": 0,
                    "risk_level": "Unknown",
                    "last_inspection": "N/A",
                    "error": "No address provided"
                }
            
            # Use violation checker agent
            violation_result_json = self.violation_checker.forward(address)
            violation_result = json.loads(violation_result_json) if violation_result_json else {}
            
            if isinstance(violation_result, dict):
                return {
                    "violation_count": violation_result.get("open_violations", 0),
                    "total_violations": violation_result.get("total_violations", 0),
                    "risk_level": self._calculate_risk_level(violation_result.get("open_violations", 0)),
                    "last_inspection": violation_result.get("last_inspection", "N/A"),
                    "building_class": violation_result.get("building_class", "Unknown")
                }
            else:
                return {
                    "violation_count": 0,
                    "risk_level": "Unknown",
                    "last_inspection": "N/A",
                    "error": "Unable to fetch violation data"
                }
                
        except Exception as e:
            return {
                "violation_count": 0,
                "risk_level": "Unknown", 
                "last_inspection": "N/A",
                "error": f"Violation check error: {str(e)}"
            }
    
    def _calculate_risk_level(self, violation_count: int) -> str:
        """Calculate risk level based on violation count."""
        if violation_count == 0:
            return "✅ Low Risk"
        elif violation_count <= 3:
            return "⚠️ Moderate Risk"
        else:
            return "🚨 High Risk"
    
    def _get_subway_info(self, listing: Dict) -> Dict:
        """Get nearest subway station information for a listing."""
        try:
            coordinates = self._extract_coordinates(listing)
            
            if not coordinates:
                return {
                    "nearest_station": "Unknown",
                    "subway_lines": "N/A",
                    "distance_miles": None,
                    "is_accessible": False,
                    "error": "No coordinates available"
                }
            
            lat, lon = coordinates
            
            # Use the nearest subway tool
            subway_result_json = nearest_subway_tool.forward(lat, lon)
            subway_result = json.loads(subway_result_json)
            
            if subway_result.get("status") == "success":
                data = subway_result.get("data", {})
                return {
                    "nearest_station": data.get("station_name", "Unknown"),
                    "subway_lines": data.get("lines", "N/A"),
                    "distance_miles": data.get("distance_miles", None),
                    "is_accessible": data.get("is_accessible", False),
                    "entrance_type": data.get("entrance_type", "Unknown")
                }
            else:
                return {
                    "nearest_station": "Unknown",
                    "subway_lines": "N/A", 
                    "distance_miles": None,
                    "is_accessible": False,
                    "error": subway_result.get("message", "Unknown error")
                }
                
        except Exception as e:
            return {
                "nearest_station": "Unknown",
                "subway_lines": "N/A",
                "distance_miles": None,
                "is_accessible": False,
                "error": f"Subway lookup error: {str(e)}"
            }
    
    def _calculate_transit_score(self, subway_info: Dict) -> int:
        """Calculate a transit accessibility score (0-100)."""
        try:
            distance = subway_info.get("distance_miles")
            if distance is None:
                return 0
            
            # Base score based on distance
            if distance <= 0.2:  # Within 2 blocks
                base_score = 100
            elif distance <= 0.5:  # Within 5 blocks
                base_score = 80
            elif distance <= 1.0:  # Within 1 mile
                base_score = 60
            elif distance <= 1.5:  # Within 1.5 miles
                base_score = 40
            else:
                base_score = 20
            
            # Bonus for accessibility
            if subway_info.get("is_accessible", False):
                base_score += 10
            
            # Bonus for multiple lines (indicates major hub)
            lines = subway_info.get("subway_lines", "")
            if lines and len(lines.split("/")) > 2:
                base_score += 5
            
            return min(base_score, 100)
            
        except Exception:
            return 0
    
    def _get_school_info(self, listing: Dict) -> Dict:
        """Get nearby school information for a listing."""
        try:
            coordinates = self._extract_coordinates(listing)
            
            if not coordinates:
                return {
                    "nearby_schools": [],
                    "closest_school_distance": None,
                    "school_types_available": [],
                    "error": "No coordinates available"
                }
            
            lat, lon = coordinates
            
            # Use the school tool
            school_result_json = near_school_tool.forward(lat, lon)
            school_result = json.loads(school_result_json)
            
            if school_result.get("status") == "success":
                schools = school_result.get("data", {}).get("schools", [])
                
                if schools:
                    school_types = list(set(school.get("school_type", "Unknown") for school in schools))
                    
                    return {
                        "nearby_schools": schools,
                        "closest_school_distance": schools[0].get("distance_miles") if schools else None,
                        "school_types_available": school_types,
                        "total_schools_found": len(schools)
                    }
                else:
                    return {
                        "nearby_schools": [],
                        "closest_school_distance": None,
                        "school_types_available": [],
                        "total_schools_found": 0
                    }
            else:
                return {
                    "nearby_schools": [],
                    "closest_school_distance": None,
                    "school_types_available": [],
                    "error": school_result.get("message", "Unknown error")
                }
                
        except Exception as e:
            return {
                "nearby_schools": [],
                "closest_school_distance": None,
                "school_types_available": [],
                "error": f"School lookup error: {str(e)}"
            }
    
    def _calculate_school_score(self, school_info: Dict) -> int:
        """Calculate a school accessibility score (0-100)."""
        try:
            schools = school_info.get("nearby_schools", [])
            if not schools:
                return 0
            
            closest_distance = school_info.get("closest_school_distance")
            if closest_distance is None:
                return 0
            
            # Base score based on distance to closest school
            if closest_distance <= 0.25:  # Within 1/4 mile
                base_score = 90
            elif closest_distance <= 0.5:  # Within 1/2 mile
                base_score = 75
            elif closest_distance <= 1.0:  # Within 1 mile
                base_score = 60
            elif closest_distance <= 1.5:  # Within 1.5 miles
                base_score = 40
            else:
                base_score = 20
            
            # Bonus for number of nearby schools
            school_count = len(schools)
            if school_count >= 3:
                base_score += 10
            elif school_count >= 2:
                base_score += 5
            
            # Bonus for school type variety
            school_types = school_info.get("school_types_available", [])
            if len(school_types) > 1:
                base_score += 5  # Bonus for variety
            
            return min(base_score, 100)
            
        except Exception:
            return 0
    
    def _enrich_single_listing(self, listing: Dict) -> Dict:
        """Enrich a single listing with all available data."""
        enriched_listing = listing.copy()
        
        print(f"🔍 Enriching listing: {listing.get('address', 'Unknown address')}")
        
        # Get building violations
        violation_info = self._get_building_violations(listing)
        enriched_listing["building_violations"] = violation_info
        
        # Get subway information
        subway_info = self._get_subway_info(listing)
        enriched_listing["subway_access"] = subway_info
        
        # Get school information
        school_info = self._get_school_info(listing)
        enriched_listing["school_access"] = school_info
        
        # Calculate composite scores
        enriched_listing["transit_score"] = self._calculate_transit_score(subway_info)
        enriched_listing["safety_score"] = self._calculate_safety_score(violation_info)
        enriched_listing["school_score"] = self._calculate_school_score(school_info)
        enriched_listing["overall_score"] = self._calculate_overall_score(
            enriched_listing["transit_score"],
            enriched_listing["safety_score"],
            enriched_listing["school_score"]
        )
        
        # Add enrichment metadata
        enriched_listing["enrichment_metadata"] = {
            "enriched_at": datetime.now().isoformat(),
            "data_sources": ["building_violations", "subway_stations", "school_locations"],
            "has_coordinates": self._extract_coordinates(listing) is not None,
            "has_address": bool(listing.get('address') or listing.get('title'))
        }
        
        return enriched_listing
    
    def _calculate_safety_score(self, violation_info: Dict) -> int:
        """Calculate safety score based on violation data (0-100)."""
        try:
            violation_count = violation_info.get("violation_count", 0)
            
            if violation_count == 0:
                return 100
            elif violation_count <= 2:
                return 80
            elif violation_count <= 5:
                return 60
            elif violation_count <= 10:
                return 40
            else:
                return 20
                
        except Exception:
            return 50  # Neutral score if we can't calculate
    
    def _calculate_overall_score(self, transit_score: int, safety_score: int, school_score: int = 0) -> int:
        """Calculate overall listing score combining transit, safety, and school access."""
        # Weight: 50% safety, 30% transit, 20% school access
        return int(0.5 * safety_score + 0.3 * transit_score + 0.2 * school_score)
    
    def forward(self, listings: str) -> str:
        """
        Enrich a list of housing listings with comprehensive data.
        
        Args:
            listings: JSON string containing list of listing dictionaries
            
        Returns:
            JSON string with enriched listings containing violation and subway data
        """
        # Parse JSON input
        try:
            if isinstance(listings, str):
                listings_data = json.loads(listings)
            else:
                listings_data = listings  # Handle direct list input for testing
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON input: {str(e)}")
            return json.dumps({"error": f"Invalid JSON input: {str(e)}", "data": []}, indent=2)
        
        if not isinstance(listings_data, list):
            print("❌ Error: listings must be a list")
            return json.dumps({"error": "listings must be a list", "data": []}, indent=2)
        
        if not listings_data:
            print("⚠️ Warning: Empty listings list provided")
            return json.dumps({"message": "Empty listings provided", "data": []}, indent=2)
        
        print(f"🚀 Starting enrichment of {len(listings_data)} listings...")
        start_time = time.time()
        
        enriched_listings = []
        
        for i, listing in enumerate(listings_data):
            try:
                print(f"📍 Processing listing {i+1}/{len(listings_data)}")
                enriched_listing = self._enrich_single_listing(listing)
                enriched_listings.append(enriched_listing)
                
            except Exception as e:
                print(f"❌ Error enriching listing {i+1}: {str(e)}")
                # Add the original listing with error information
                error_listing = listing.copy()
                error_listing["enrichment_error"] = str(e)
                error_listing["enrichment_metadata"] = {
                    "enriched_at": datetime.now().isoformat(),
                    "error": True
                }
                enriched_listings.append(error_listing)
        
        print(f"✅ Enrichment complete! Processed {len(enriched_listings)} listings")
        
        # Return as JSON string for smolagents compatibility
        result = {
            "status": "success",
            "message": f"Successfully enriched {len(enriched_listings)} listings",
            "data": enriched_listings,
            "summary": {
                "total_listings": len(listings_data),
                "successfully_enriched": len(enriched_listings),
                "processing_time": f"{time.time() - start_time:.2f}s"
            }
        }
        return json.dumps(result, indent=2, default=str)

# Create the tool instance
enrichment_tool = EnrichmentTool() 