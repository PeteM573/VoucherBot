import requests
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from smolagents import Tool
from geopy.distance import geodesic
import math

class NearestSubwayTool(Tool):
    """
    Advanced tool to find the nearest NYC subway station to a given coordinate.
    Features:
    - Real-time NYC Open Data API integration
    - Intelligent caching with periodic cleanup
    - Distance calculations using geodesic distance
    - ADA accessibility information
    - Multi-line station support
    - Thread-safe operations
    """
    
    name = "find_nearest_subway"
    description = (
        "Finds the nearest NYC subway station to a given latitude and longitude coordinate. "
        "Returns station name, subway lines, distance in miles, and accessibility information. "
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
        }
    }
    output_type = "string"
    
    # NYC Open Data API endpoint for subway entrances
    SUBWAY_API_URL = "https://data.ny.gov/resource/i9wp-a4ja.json"
    
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
        self._stations_cache = None
        self._stations_cache_time = None
        self._STATIONS_CACHE_DURATION = timedelta(hours=6)  # Refresh every 6 hours
        
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
        
        print("🚇 NearestSubwayTool initialized with advanced caching")
    
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
            name="SubwayCacheCleaner"
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
    
    def _fetch_subway_stations(self) -> List[Dict]:
        """Fetch and cache subway station data from NYC Open Data API."""
        now = datetime.now()
        
        # Check if we have valid cached data
        if (self._stations_cache and self._stations_cache_time and 
            now - self._stations_cache_time < self._STATIONS_CACHE_DURATION):
            return self._stations_cache
        
        try:
            print("🌐 Fetching fresh subway data from NYC Open Data API...")
            
            # Build query parameters for optimal data
            params = {
                "$select": "stop_name,daytime_routes,entrance_latitude,entrance_longitude,entrance_type,station_id",
                "$where": "entrance_latitude IS NOT NULL AND entrance_longitude IS NOT NULL AND entry_allowed='YES'",
                "$limit": "5000"  # Ensure we get all stations
            }
            
            response = requests.get(self.SUBWAY_API_URL, params=params, timeout=30)
            response.raise_for_status()
            
            stations_data = response.json()
            
            # Filter and process the data
            processed_stations = []
            for station in stations_data:
                try:
                    lat = float(station.get('entrance_latitude', 0))
                    lon = float(station.get('entrance_longitude', 0))
                    
                    # Basic validation
                    if not (40.4 <= lat <= 40.9 and -74.3 <= lon <= -73.7):
                        continue  # Skip invalid NYC coordinates
                    
                    processed_stations.append({
                        'station_name': station.get('stop_name', 'Unknown Station'),
                        'lines': station.get('daytime_routes', 'N/A'),
                        'latitude': lat,
                        'longitude': lon,
                        'entrance_type': station.get('entrance_type', 'Unknown'),
                        'station_id': station.get('station_id', 'Unknown')
                    })
                    
                except (ValueError, TypeError):
                    continue  # Skip malformed entries
            
            # Cache the processed data
            self._stations_cache = processed_stations
            self._stations_cache_time = now
            self._stats["api_calls"] += 1
            
            print(f"✅ Loaded {len(processed_stations)} subway stations")
            return processed_stations
            
        except Exception as e:
            print(f"❌ Error fetching subway data: {str(e)}")
            # Return cached data if available, even if expired
            if self._stations_cache:
                print("📦 Using cached subway data due to API error")
                return self._stations_cache
            else:
                raise Exception(f"Unable to fetch subway data and no cache available: {str(e)}")
    
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
    
    def _find_nearest_station(self, lat: float, lon: float, stations: List[Dict]) -> Dict:
        """Find the nearest station from the list."""
        if not stations:
            raise Exception("No subway stations data available")
        
        nearest_station = None
        min_distance = float('inf')
        
        for station in stations:
            try:
                distance = self._calculate_distance(
                    lat, lon,
                    station['latitude'], station['longitude']
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = station.copy()
                    nearest_station['distance_miles'] = distance
                    
            except Exception:
                continue  # Skip stations with calculation errors
        
        if not nearest_station:
            raise Exception("Unable to calculate distances to any stations")
        
        return nearest_station
    
    def _format_output(self, station: Dict, lat: float, lon: float) -> Dict:
        """Format the output with comprehensive station information."""
        # Determine accessibility (simplified heuristic)
        is_accessible = "elevator" in station.get('entrance_type', '').lower()
        
        # Clean up lines formatting
        lines = station.get('lines', 'N/A')
        if lines and lines != 'N/A':
            # Format multiple lines nicely
            lines = lines.replace(' ', '/') if ' ' in lines else lines
        
        return {
            "status": "success",
            "data": {
                "station_name": station.get('station_name', 'Unknown Station'),
                "lines": lines,
                "distance_miles": station.get('distance_miles', 0.0),
                "is_accessible": is_accessible,
                "entrance_type": station.get('entrance_type', 'Unknown'),
                "coordinates": {
                    "latitude": station.get('latitude'),
                    "longitude": station.get('longitude')
                }
            },
            "metadata": {
                "source": "NYC Open Data - Subway Entrances",
                "timestamp": datetime.now().isoformat(),
                "query_location": {"lat": lat, "lon": lon},
                "cache_hit": self._stats["cache_hits"] > 0
            },
            "performance": {
                "cache_hits": self._stats["cache_hits"],
                "cache_misses": self._stats["cache_misses"],
                "total_stations_checked": len(self._stations_cache) if self._stations_cache else 0
            }
        }
    
    def forward(self, lat: float, lon: float) -> Dict:
        """
        Find the nearest subway station to the given coordinates.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Dictionary with nearest station information
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
        
        # Check cache first
        with self._cache_lock:
            if (cache_key in self._cache and 
                datetime.now() - self._cache_timestamp[cache_key] <= self._CACHE_DURATION):
                self._stats["cache_hits"] += 1
                cached_result = self._cache[cache_key]
                cached_result["metadata"]["cache_hit"] = True
                print(f"📦 Cache hit for coordinates ({lat}, {lon})")
                return json.dumps(cached_result, indent=2)
        
        # Cache miss - calculate new result
        self._stats["cache_misses"] += 1
        print(f"🔍 Finding nearest subway station for ({lat}, {lon})")
        
        try:
            # Fetch subway stations data
            stations = self._fetch_subway_stations()
            
            # Find nearest station
            nearest_station = self._find_nearest_station(lat, lon, stations)
            
            # Format output
            result = self._format_output(nearest_station, lat, lon)
            
            # Cache the result
            with self._cache_lock:
                self._cache[cache_key] = result
                self._cache_timestamp[cache_key] = datetime.now()
            
            print(f"🚇 Found: {result['data']['station_name']} ({result['data']['distance_miles']} miles)")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Error finding nearest subway station: {str(e)}",
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
                "stations_cached": len(self._stations_cache) if self._stations_cache else 0,
                "performance": self._stats.copy()
            }

# Create the tool instance
nearest_subway_tool = NearestSubwayTool() 