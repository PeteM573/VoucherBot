#!/usr/bin/env python3
"""
Simple demo showing how to use ViolationCheckerAgent with real GeoClient BBL conversion.
This script demonstrates the improved accuracy when using real NYC GeoClient API.
"""

import os
import json
from dotenv import load_dotenv
from geo_client_bbl_tool import GeoClientBBLTool
from violation_checker_agent import ViolationCheckerAgent

# Load environment variables from .env file
load_dotenv()

def demo_real_geoclient():
    """Demo with real GeoClient API (if available)."""
    print("🏙️ NYC VIOLATION CHECKER - REAL GEOCLIENT DEMO")
    print("=" * 55)
    
    # Check for NYC GeoClient API key
    api_key = os.getenv('NYC_GEOCLIENT_API_KEY')
    
    if api_key:
        print("✅ NYC GeoClient API key found - using REAL BBL conversion")
        
        # Initialize with real GeoClient
        geoclient_tool = GeoClientBBLTool(api_key)
        violation_checker = ViolationCheckerAgent()
        violation_checker.set_geoclient_tool(geoclient_tool)
        
        demo_message = "🌍 USING REAL NYC GEOCLIENT API"
    else:
        print("⚠️ No API key found - using mock BBL conversion")
        print("To use real BBL conversion:")
        print("  export NYC_GEOCLIENT_API_KEY='your-api-key-here'")
        
        # Initialize without GeoClient (mock mode)
        violation_checker = ViolationCheckerAgent()
        
        demo_message = "🧪 USING MOCK BBL GENERATION"
    
    print(f"\n{demo_message}")
    print("-" * 55)
    
    # Test with a single address
    test_address = "350 East 62nd Street, Manhattan, NY"
    
    print(f"\n📍 Testing address: {test_address}")
    print("-" * 30)
    
    # Check violations
    result = violation_checker.forward(test_address)
    data = json.loads(result)
    
    # Display results
    print(f"\n📊 VIOLATION RESULTS:")
    print(f"   🏢 Building Violations: {data['violations']}")
    print(f"   🚦 Safety Risk Level: {data['risk_level']}")
    print(f"   📅 Last Inspection: {data['last_inspection']}")
    print(f"   📝 Summary: {data['summary']}")
    
    # Risk assessment
    risk = data['risk_level']
    if risk == '✅':
        print(f"\n✅ RECOMMENDATION: This appears to be a safe building")
        print(f"   No violations found in NYC records")
    elif risk == '⚠️':
        print(f"\n⚠️ RECOMMENDATION: Some violations present")
        print(f"   Review details before making a decision")
    else:
        print(f"\n🚨 RECOMMENDATION: High violation count")
        print(f"   Exercise caution - consider other options")
    
    return data

def demo_comparison():
    """Show comparison between mock and real BBL (when API key available)."""
    api_key = os.getenv('NYC_GEOCLIENT_API_KEY')
    
    if not api_key:
        print("\n💡 To see comparison with real BBL conversion:")
        print("   Set NYC_GEOCLIENT_API_KEY environment variable")
        return
    
    print(f"\n🔍 COMPARISON: MOCK vs REAL BBL")
    print("=" * 40)
    
    test_address = "123 Main Street, Brooklyn, NY"
    
    # Test with mock BBL
    mock_checker = ViolationCheckerAgent()
    mock_bbl = mock_checker._get_bbl_from_address_mock(test_address)
    
    # Test with real BBL
    geoclient_tool = GeoClientBBLTool(api_key)
    real_checker = ViolationCheckerAgent()
    real_checker.set_geoclient_tool(geoclient_tool)
    real_bbl = real_checker._get_bbl_from_address_real(test_address)
    
    print(f"Address: {test_address}")
    print(f"🧪 Mock BBL: {mock_bbl}")
    print(f"🌍 Real BBL: {real_bbl}")
    
    if mock_bbl != real_bbl:
        print("✅ Different BBLs - real API provides accurate data")
    else:
        print("⚠️ Same BBLs - coincidence or test data")

if __name__ == "__main__":
    # Run the demo
    demo_real_geoclient()
    
    # Show comparison if API key available
    demo_comparison()
    
    print(f"\n🎯 DEMO COMPLETE!")
    print("=" * 55) 