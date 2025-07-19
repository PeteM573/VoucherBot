import requests
from smolagents import Tool
import hashlib

class GeoClientBBLTool(Tool):
    name = "geoclient_bbl"
    description = "Returns the BBL (Borough, Block, Lot) for a given NYC address using the GeoClient V2 API."
    inputs = {
        "houseNumber": {"type": "string", "description": "The house number of the address."},
        "street": {"type": "string", "description": "The street name of the address."},
        "borough": {"type": "string", "description": "The borough name (e.g., Manhattan, Bronx, Brooklyn, Queens, Staten Island)."}
    }
    output_type = "string"

    def __init__(self, api_key: str, use_mock: bool = False):
        super().__init__()
        self.api_key = api_key
        self.endpoint = "https://api.nyc.gov/geoclient/v2/address"
        self.use_mock = use_mock

    def _generate_mock_bbl(self, address: str) -> str:
        """Generate a realistic-looking mock BBL for testing purposes."""
        # Create a hash of the address for consistency
        hash_obj = hashlib.md5(address.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Extract parts for BBL components
        borough_map = {
            'manhattan': '1',
            'bronx': '2', 
            'brooklyn': '3',
            'queens': '4',
            'staten island': '5'
        }
        
        borough_code = borough_map.get(address.split(',')[-1].strip().lower(), '1')
        
        # Generate block and lot from hash
        block = str(int(hash_hex[:4], 16) % 9999 + 1).zfill(5)
        lot = str(int(hash_hex[4:8], 16) % 999 + 1).zfill(4)
        
        return f"{borough_code}{block}{lot}"

    def forward(self, houseNumber: str, street: str, borough: str) -> str:
        # If using mock mode, return mock BBL
        if self.use_mock:
            address = f"{houseNumber} {street}, {borough}"
            mock_bbl = self._generate_mock_bbl(address)
            return f"MOCK_BBL_{mock_bbl} (API not accessible - using mock data for testing)"

        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json"
        }

        params = {
            "houseNumber": houseNumber,
            "street": street,
            "borough": borough
        }

        try:
            response = requests.get(self.endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 401:
                # Auto-fallback to mock mode if API access fails
                address = f"{houseNumber} {street}, {borough}"
                mock_bbl = self._generate_mock_bbl(address)
                return (f"API_ACCESS_ERROR: 401 Access Denied. Using mock BBL for testing: MOCK_{mock_bbl}\n"
                       f"To fix: Verify subscription at https://api-portal.nyc.gov/\n"
                       f"For now, this mock BBL can be used for testing purposes.")
            
            if response.status_code == 403:
                # Auto-fallback to mock mode if API access fails
                address = f"{houseNumber} {street}, {borough}"
                mock_bbl = self._generate_mock_bbl(address)
                return (f"API_ACCESS_ERROR: 403 Forbidden. Using mock BBL for testing: MOCK_{mock_bbl}\n"
                       f"To fix: Check API permissions and subscription status.\n"
                       f"For now, this mock BBL can be used for testing purposes.")
            
            response.raise_for_status()
            data = response.json()

            if "address" not in data:
                return "Error: No 'address' field in response."

            address_data = data["address"]
            return_code = address_data.get("geosupportReturnCode", "")
            if return_code not in ["00", "01"]:
                reason = address_data.get("message", "Unknown error")
                return f"Geosupport rejected the address: {reason}"

            bbl = address_data.get("bbl")
            if not bbl:
                return "BBL not found in the response."
            return bbl

        except Exception as e:
            # Auto-fallback to mock mode for any error
            address = f"{houseNumber} {street}, {borough}"
            mock_bbl = self._generate_mock_bbl(address)
            return (f"API_ERROR: {str(e)}\n"
                   f"Using mock BBL for testing: MOCK_{mock_bbl}\n"
                   f"This allows you to continue testing while resolving API access.")

# Helper function to create the tool with mock mode enabled
def create_geoclient_tool_with_fallback(api_key: str = None):
    """Create a geoclient tool that falls back to mock mode if API access fails."""
    if not api_key:
        return GeoClientBBLTool("dummy_key", use_mock=True)
    else:
        return GeoClientBBLTool(api_key, use_mock=False) 