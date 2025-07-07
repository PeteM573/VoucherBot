import requests
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from smolagents import Tool
from geopy.distance import geodesic
import math

class NearSchoolTool(Tool):
    """
    Advanced tool to find the nearest NYC public schools to a given coordinate.
    Features:
    - Real-time NYC Open Data API integration
    - Intelligent caching with periodic cleanup
    - Distance calculations using geodesic distance
    - School type and grade level information
    - Walking time estimates
    - Thread-safe operations
    """
    
    name = "find_nearest_school"
    description = (
        "Finds the nearest NYC public schools to a given latitude and longitude coordinate. "
        "Returns school names, grades served, distance in miles, walking times, and school type information. "
        "Uses real-time NYC Open Data and intelligent caching for optimal performance."
    )
    
    inputs = {
        "lat": {
            "type": "number",
            "description": "Latitude coordinate of the location (e.g., 40.7589)"
        },
        "lon": {
            "type": "number", 
            "description": "Longitude coordinate of the location (e.g., -73.9851)"
        },
        "school_type": {
            "type": "string",
            "description": "Optional filter for specific school types: 'elementary', 'middle', 'high', or 'all' (default: 'all')",
            "nullable": True
        }
    }
    output_type = "string"
    
    # NYC Open Data API endpoint for schools
    SCHOOLS_API_URL = "https://data.cityofnewyork.us/resource/wg9x-4ke6.json"
    
    def __init__(self):
        """Initialize the tool with caching and background cleanup."""
        super().__init__()
        # Cache configuration
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_lock = threading.Lock()
        self._CACHE_DURATION = timedelta(hours=24)  # 24-hour cache
        self._MAX_CACHE_SIZE = 1000  # Prevent unlimited growth
        
        # API data cache
        self._schools_cache = None
        self._schools_cache_time = None
        self._SCHOOLS_CACHE_DURATION = timedelta(hours=12)  # Refresh every 12 hours
        
        # Performance tracking
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "api_calls": 0,
            "total_requests": 0
        }
        
        # Add this attribute that smolagents might expect
        self.is_initialized = True
        
        # Start background cache cleaner
        self._start_cache_cleaner()
        
        print("🏫 NearSchoolTool initialized with advanced caching")
    
    def _start_cache_cleaner(self):
        """Start background thread for periodic cache cleanup."""
        def clean_cache_periodically():
            while True:
                time.sleep(3600)  # Check every hour
                self._clean_expired_cache()
                self._enforce_cache_size_limit()
        
        cleaner_thread = threading.Thread(
            target=clean_cache_periodically,
            daemon=True,
            name="SchoolCacheCleaner"
        )
        cleaner_thread.start()
        print("🧹 Cache cleaner thread started")
    
    def _clean_expired_cache(self):
        """Remove expired cache entries."""
        now = datetime.now()
        with self._cache_lock:
            expired_keys = [
                key for key, timestamp in self._cache_timestamp.items()
                if now - timestamp > self._CACHE_DURATION
            ]
            
            for key in expired_keys:
                del self._cache[key]
                del self._cache_timestamp[key]
            
            if expired_keys:
                print(f"🧹 Cleaned {len(expired_keys)} expired cache entries")
    
    def _enforce_cache_size_limit(self):
        """Enforce maximum cache size by removing oldest entries."""
        with self._cache_lock:
            if len(self._cache) > self._MAX_CACHE_SIZE:
                # Sort by timestamp and remove oldest entries
                sorted_items = sorted(
                    self._cache_timestamp.items(),
                    key=lambda x: x[1]
                )
                
                # Remove oldest 20% of entries
                remove_count = len(sorted_items) // 5
                for key, _ in sorted_items[:remove_count]:
                    del self._cache[key]
                    del self._cache_timestamp[key]
                
                print(f"🧹 Removed {remove_count} oldest cache entries (size limit)")
    
    def _cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key with reasonable precision for geographic clustering."""
        # Round to 4 decimal places (~11 meters precision)
        # This allows nearby requests to share cache entries
        return f"{round(lat, 4)}:{round(lon, 4)}"
    
    def _fetch_schools(self) -> List[Dict]:
        """Fetch and cache school data from NYC Open Data API."""
        now = datetime.now()
        
        # Check if we have valid cached data
        if (self._schools_cache and self._schools_cache_time and 
            now - self._schools_cache_time < self._SCHOOLS_CACHE_DURATION):
            return self._schools_cache
        
        try:
            print("🌐 Fetching fresh school data from NYC Open Data API...")
            
            # Build query parameters for optimal data
            params = {
                "$select": "location_name,grades_text,latitude,longitude,location_category_description,primary_address_line_1,borough_block_lot,status_descriptions",
                "$where": "latitude IS NOT NULL AND longitude IS NOT NULL AND status_descriptions='Open'",
                "$limit": "5000"  # Ensure we get all schools
            }
            
            response = requests.get(self.SCHOOLS_API_URL, params=params, timeout=30)
            response.raise_for_status()
            
            schools_data = response.json()
            
            # Filter and process the data
            processed_schools = []
            for school in schools_data:
                try:
                    lat = float(school.get('latitude', 0))
                    lon = float(school.get('longitude', 0))
                    
                    # Basic validation for NYC coordinates
                    if not (40.4 <= lat <= 40.9 and -74.3 <= lon <= -73.7):
                        continue
                    
                    # Clean up grades formatting
                    grades = school.get('grades_text', 'N/A')
                    if grades and grades != 'N/A':
                        # Convert comma-separated grades to readable format
                        grades_list = [g.strip() for g in grades.split(',')]
                        if len(grades_list) > 1:
                            grades = f"{grades_list[0]}-{grades_list[-1]}"
                        else:
                            grades = grades_list[0]
                    
                    processed_schools.append({
                        'school_name': school.get('location_name', 'Unknown School'),
                        'grades': grades,
                        'latitude': lat,
                        'longitude': lon,
                        'school_type': school.get('location_category_description', 'Unknown'),
                        'address': school.get('primary_address_line_1', 'Unknown'),
                        'bbl': school.get('borough_block_lot', 'Unknown')
                    })
                    
                except (ValueError, TypeError):
                    continue  # Skip malformed entries
            
            # Cache the processed data
            self._schools_cache = processed_schools
            self._schools_cache_time = now
            self._stats["api_calls"] += 1
            
            print(f"✅ Loaded {len(processed_schools)} active schools")
            return processed_schools
            
        except Exception as e:
            print(f"❌ Error fetching school data: {str(e)}")
            # Return cached data if available, even if expired
            if self._schools_cache:
                print("📦 Using cached school data due to API error")
                return self._schools_cache
            else:
                raise Exception(f"Unable to fetch school data and no cache available: {str(e)}")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate geodesic distance between two points in miles."""
        try:
            distance = geodesic((lat1, lon1), (lat2, lon2)).miles
            return round(distance, 2)
        except Exception:
            # Fallback to Haversine formula if geodesic fails
            return self._haversine_distance(lat1, lon1, lat2, lon2)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Fallback Haversine formula for distance calculation."""
        R = 3959  # Earth's radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return round(R * c, 2)
    
    def _filter_schools_by_type(self, schools: List[Dict], school_type: str) -> List[Dict]:
        """Filter schools by type (elementary, middle, high)."""
        if not school_type or school_type.lower() == 'all':
            return schools
        
        school_type = school_type.lower()
        filtered_schools = []
        
        for school in schools:
            school_category = school.get('school_type', '').lower()
            
            # Map school types to user-friendly categories
            if school_type == 'elementary':
                if any(keyword in school_category for keyword in ['elementary', 'primary', 'k-8']):
                    filtered_schools.append(school)
            elif school_type == 'middle' or school_type == 'junior':
                if any(keyword in school_category for keyword in ['middle', 'junior', 'intermediate']):
                    filtered_schools.append(school)
            elif school_type == 'high':
                if 'high' in school_category and 'school' in school_category:
                    filtered_schools.append(school)
        
        return filtered_schools
    
    def _find_nearest_schools(self, lat: float, lon: float, schools: List[Dict], school_type: str = 'all', limit: int = 3) -> List[Dict]:
        """Find the nearest schools from the list, returns top N schools."""
        if not schools:
            raise Exception("No school data available")
        
        # Filter by school type if specified
        filtered_schools = self._filter_schools_by_type(schools, school_type)
        
        if not filtered_schools and school_type != 'all':
            # If no schools found for specific type, return message
            return []
        
        school_distances = []
        
        for school in filtered_schools:
            try:
                distance = self._calculate_distance(
                    lat, lon,
                    school['latitude'], school['longitude']
                )
                
                school_info = school.copy()
                school_info['distance_miles'] = distance
                # Calculate walking time (assuming 3 mph walking speed)
                school_info['walking_time_minutes'] = round(distance * 20)  # 20 minutes per mile at 3 mph
                school_distances.append(school_info)
                    
            except Exception:
                continue  # Skip schools with calculation errors
        
        if not school_distances:
            if school_type != 'all':
                return []  # No schools of specified type found
            else:
                raise Exception("Unable to calculate distances to any schools")
        
        # Sort by distance and return top N schools
        school_distances.sort(key=lambda x: x['distance_miles'])
        return school_distances[:limit]
    
    def _format_output(self, schools: List[Dict], lat: float, lon: float, school_type: str = 'all') -> Dict:
        """Format the output with comprehensive school information."""
        if not schools and school_type != 'all':
            return {
                "status": "success",
                "data": {
                    "schools": [],
                    "message": f"No {school_type} schools found within reasonable distance",
                    "searched_for": school_type,
                    "suggestion": "Try searching for 'all' school types or a different area"
                },
                "metadata": {
                    "source": "NYC Open Data - School Locations",
                    "timestamp": datetime.now().isoformat(),
                    "query_location": {"lat": lat, "lon": lon},
                    "school_type_filter": school_type,
                    "cache_hit": self._stats["cache_hits"] > 0
                }
            }
        
        # Create user-friendly summary
        summary_text = f"Found {len(schools)} nearby schools"
        if school_type != 'all':
            summary_text += f" ({school_type} schools)"
        
        return {
            "status": "success",
            "data": {
                "schools": [{
                    "school_name": school['school_name'],
                    "grades": school['grades'],
                    "school_type": school['school_type'],
                    "distance_miles": school['distance_miles'],
                    "walking_time_minutes": school['walking_time_minutes'],
                    "address": school['address'],
                    "coordinates": {
                        "latitude": school['latitude'],
                        "longitude": school['longitude']
                    }
                } for school in schools],
                "summary": summary_text,
                "closest_school": {
                    "name": schools[0]['school_name'] if schools else None,
                    "distance": schools[0]['distance_miles'] if schools else None,
                    "walking_time": schools[0]['walking_time_minutes'] if schools else None
                } if schools else None
            },
            "metadata": {
                "source": "NYC Open Data - School Locations",
                "timestamp": datetime.now().isoformat(),
                "query_location": {"lat": lat, "lon": lon},
                "school_type_filter": school_type,
                "cache_hit": self._stats["cache_hits"] > 0
            },
            "performance": {
                "cache_hits": self._stats["cache_hits"],
                "cache_misses": self._stats["cache_misses"],
                "total_schools_checked": len(self._schools_cache) if self._schools_cache else 0
            }
        }
    
    def forward(self, lat: float, lon: float, school_type: str = 'all') -> str:
        """
        Find the nearest schools to the given coordinates.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            school_type: Filter for school type ('elementary', 'middle', 'high', or 'all')
            
        Returns:
            JSON string with nearest schools information
        """
        self._stats["total_requests"] += 1
        
        # Input validation
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            error_result = {
                "status": "error",
                "message": "Invalid coordinates: lat and lon must be numbers",
                "data": None
            }
            return json.dumps(error_result, indent=2)
        
        # NYC bounds check
        if not (40.4 <= lat <= 40.9 and -74.3 <= lon <= -73.7):
            error_result = {
                "status": "error", 
                "message": "Coordinates outside NYC area",
                "data": None
            }
            return json.dumps(error_result, indent=2)
        
        cache_key = self._cache_key(lat, lon)
        cache_key_with_type = f"{cache_key}:{school_type}"
        
        # Check cache first
        with self._cache_lock:
            if (cache_key_with_type in self._cache and 
                datetime.now() - self._cache_timestamp[cache_key_with_type] <= self._CACHE_DURATION):
                self._stats["cache_hits"] += 1
                cached_result = self._cache[cache_key_with_type]
                cached_result["metadata"]["cache_hit"] = True
                filter_text = f" ({school_type} schools)" if school_type != 'all' else ""
                print(f"📦 Cache hit for coordinates ({lat}, {lon}){filter_text}")
                return json.dumps(cached_result, indent=2)
        
        # Cache miss - calculate new result
        self._stats["cache_misses"] += 1
        filter_text = f" ({school_type} schools)" if school_type != 'all' else ""
        print(f"🔍 Finding nearest schools{filter_text} for ({lat}, {lon})")
        
        try:
            # Fetch school data
            schools = self._fetch_schools()
            
            # Find nearest schools
            nearest_schools = self._find_nearest_schools(lat, lon, schools, school_type)
            
            # Format output
            result = self._format_output(nearest_schools, lat, lon, school_type)
            
            # Cache the result (include school_type in cache key for filtering)
            cache_key_with_type = f"{cache_key}:{school_type}"
            with self._cache_lock:
                self._cache[cache_key_with_type] = result
                self._cache_timestamp[cache_key_with_type] = datetime.now()
            
            if nearest_schools:
                print(f"🏫 Found {len(nearest_schools)} nearby {school_type} schools" if school_type != 'all' else f"🏫 Found {len(nearest_schools)} nearby schools")
            else:
                print(f"🏫 No {school_type} schools found in the area")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Error finding nearest schools: {str(e)}",
                "data": None,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "query_location": {"lat": lat, "lon": lon}
                }
            }
            print(f"❌ Error: {str(e)}")
            return json.dumps(error_result, indent=2)
    
    def get_cache_stats(self) -> Dict:
        """Get current cache statistics for monitoring."""
        with self._cache_lock:
            return {
                "cache_size": len(self._cache),
                "max_cache_size": self._MAX_CACHE_SIZE,
                "cache_duration_hours": self._CACHE_DURATION.total_seconds() / 3600,
                "schools_cached": len(self._schools_cache) if self._schools_cache else 0,
                "performance": self._stats.copy()
            }

# Create the tool instance
near_school_tool = NearSchoolTool() 