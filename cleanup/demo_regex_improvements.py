#!/usr/bin/env python3
"""
Demo: Regex Pattern Improvements

This script demonstrates the improvements achieved through comprehensive
regex testing and enhancement.
"""

from semantic_router import EnhancedSemanticRouter as V1Router
from enhanced_semantic_router_v2 import EnhancedSemanticRouterV2 as V2Router

def demo_improvements():
    """Demonstrate the improvements between V1 and V2"""
    
    v1_router = V1Router()
    v2_router = V2Router()
    
    # Test cases that show clear improvements
    demo_cases = [
        "Look in Staten Island",
        "Try 2 bedrooms", 
        "Check Brooklyn yo",
        "Search in Manhattan",
        "How about BK with 2 bedrooms?",
        "Check SI",
        "Try Manhattan 3br",
        "Look around Queens",
        "Check studio",
        "With Section 8",
    ]
    
    print("🎯 REGEX PATTERN IMPROVEMENTS DEMONSTRATION")
    print("=" * 70)
    print(f"{'Query':<35} {'V1 Result':<15} {'V2 Result':<15} {'Status'}")
    print("-" * 70)
    
    improvements = 0
    total = len(demo_cases)
    
    for query in demo_cases:
        # Test V1
        try:
            v1_intent, v1_params, _ = v1_router.process_message(query)
            v1_success = v1_intent.value != "unclassified" and bool(v1_params)
            v1_result = "✅ Pass" if v1_success else "❌ Fail"
        except:
            v1_result = "❌ Error"
            v1_success = False
        
        # Test V2
        try:
            v2_intent, v2_params, _ = v2_router.process_message(query)
            v2_success = v2_intent.value != "unclassified" and bool(v2_params)
            v2_result = "✅ Pass" if v2_success else "❌ Fail"
        except:
            v2_result = "❌ Error"
            v2_success = False
        
        # Determine status
        if not v1_success and v2_success:
            status = "🎉 FIXED"
            improvements += 1
        elif v1_success and v2_success:
            status = "✅ Good"
        elif v1_success and not v2_success:
            status = "⚠️  Regressed"
        else:
            status = "❌ Still failing"
        
        print(f"{query[:34]:<35} {v1_result:<15} {v2_result:<15} {status}")
    
    print("-" * 70)
    print(f"📊 SUMMARY: {improvements}/{total} cases improved by V2")
    print(f"🎯 Improvement Rate: {improvements/total*100:.1f}%")
    
    # Show detailed examples
    print(f"\n📋 DETAILED EXAMPLES")
    print("=" * 50)
    
    examples = [
        "Look in Staten Island",
        "How about BK with 2 bedrooms?",
        "Check studio"
    ]
    
    for example in examples:
        print(f"\n🔍 Query: '{example}'")
        
        # V1 results
        v1_intent, v1_params, v1_response = v1_router.process_message(example)
        print(f"   V1: {v1_intent.value} | {v1_params} | '{v1_response}'")
        
        # V2 results  
        v2_intent, v2_params, v2_response = v2_router.process_message(example)
        print(f"   V2: {v2_intent.value} | {v2_params} | '{v2_response}'")

if __name__ == "__main__":
    demo_improvements() 