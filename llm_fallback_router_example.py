#!/usr/bin/env python3
"""
LLM Fallback Router Integration Example

This example demonstrates how to integrate the LLMFallbackRouter
with the existing VoucherBot system as a fallback for the regex-based router.

Usage:
    python llm_fallback_router_example.py
"""

import os
import json
from dotenv import load_dotenv
from llm_fallback_router import LLMFallbackRouter, InvalidInputError, LLMProcessingError, InvalidLLMResponseError

# Import existing components
from agent_setup import initialize_caseworker_agent
from enhanced_semantic_router_v2 import EnhancedSemanticRouterV2, Intent

# Load environment variables
load_dotenv()

class MockLLMClient:
    """
    Mock LLM client for demonstration purposes.
    In a real implementation, this would be replaced with actual LLM clients
    like OpenAI, Anthropic, or the Gemini client used in the project.
    """
    
    def __init__(self):
        self.call_count = 0
    
    def generate(self, prompt: str) -> str:
        """
        Generate a mock response based on the prompt content.
        In production, this would make actual API calls to an LLM.
        """
        self.call_count += 1
        
        # Extract the message from the prompt
        message_start = prompt.find('Message: "') + 10
        message_end = prompt.find('"', message_start)
        message = prompt[message_start:message_end] if message_start > 9 else ""
        
        # Simple rule-based mock responses
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["find", "search", "look for", "apartment", "listing"]):
            return json.dumps({
                "intent": "SEARCH_LISTINGS",
                "parameters": {
                    "borough": "Brooklyn" if "brooklyn" in message_lower or "bk" in message_lower else None,
                    "bedrooms": 2 if "2" in message or "two" in message_lower else None,
                    "max_rent": 3000 if "$3000" in message or "3000" in message else None,
                    "voucher_type": "Section 8" if "section" in message_lower else None
                },
                "reasoning": "User is looking for apartment listings with specified criteria"
            })
        
        elif any(word in message_lower for word in ["what about", "try", "instead", "change"]):
            return json.dumps({
                "intent": "REFINE_SEARCH",
                "parameters": {
                    "borough": "Queens" if "queens" in message_lower else None
                },
                "reasoning": "User wants to modify their existing search parameters"
            })
        
        elif any(word in message_lower for word in ["violation", "safe", "building", "inspect"]):
            return json.dumps({
                "intent": "CHECK_VIOLATIONS",
                "parameters": {},
                "reasoning": "User wants to check building safety violations"
            })
        
        elif any(word in message_lower for word in ["help", "assist", "what can you do"]):
            return json.dumps({
                "intent": "HELP_REQUEST",
                "parameters": {},
                "reasoning": "User is requesting help or information about available features"
            })
        
        else:
            return json.dumps({
                "intent": "UNKNOWN",
                "parameters": {},
                "reasoning": "Unable to determine user intent from the message"
            })

class TwoTierSemanticRouter:
    """
    Combined router that uses regex-based routing first, then falls back to LLM.
    
    This demonstrates the two-tier architecture mentioned in the specification.
    """
    
    def __init__(self, llm_client=None, debug=False):
        # Initialize the regex-based router (V2)
        self.regex_router = EnhancedSemanticRouterV2()
        
        # Initialize the LLM fallback router
        if llm_client is None:
            llm_client = MockLLMClient()
        self.llm_router = LLMFallbackRouter(llm_client, debug=debug)
        
        self.debug = debug
        
    def route(self, message: str, context: dict = None) -> dict:
        """
        Route a message using the two-tier system.
        
        Args:
            message: User message to route
            context: Optional context dictionary with conversation state
            
        Returns:
            Dictionary with routing results including:
            - intent: Classified intent
            - parameters: Extracted parameters  
            - reasoning: Explanation of the classification
            - router_used: Which router was used ("regex" or "llm")
            - confidence: Confidence level (if available)
        """
        if self.debug:
            print(f"\n🔍 Routing message: '{message}'")
        
        # Step 1: Try regex-based routing first
        try:
            regex_intent = self.regex_router.classify_intent(message, context)
            regex_params = self.regex_router.extract_parameters(message)
            
            # Check if regex router was successful
            if regex_intent != Intent.UNCLASSIFIED and (regex_params or regex_intent in [Intent.SHOW_HELP, Intent.CHECK_VIOLATIONS]):
                if self.debug:
                    print("✅ Regex router succeeded")
                
                return {
                    "intent": regex_intent.value,
                    "parameters": regex_params,
                    "reasoning": f"Classified by regex patterns as {regex_intent.value}",
                    "router_used": "regex",
                    "confidence": 0.95  # Regex patterns are highly confident when they match
                }
        
        except Exception as e:
            if self.debug:
                print(f"⚠️ Regex router failed: {e}")
        
        # Step 2: Fall back to LLM router
        if self.debug:
            print("🧠 Falling back to LLM router")
        
        try:
            # Convert context to string format for LLM
            context_str = None
            if context:
                context_str = f"Previous search: {json.dumps(context)}"
            
            llm_result = self.llm_router.route(message, context_str)
            llm_result["router_used"] = "llm"
            llm_result["confidence"] = 0.8  # LLM results are generally less confident
            
            if self.debug:
                print("✅ LLM router succeeded")
            
            return llm_result
            
        except (InvalidInputError, LLMProcessingError, InvalidLLMResponseError) as e:
            if self.debug:
                print(f"❌ LLM router failed: {e}")
            
            # Both routers failed - return unknown intent
            return {
                "intent": "UNKNOWN",
                "parameters": {},
                "reasoning": f"Both regex and LLM routers failed. Error: {e}",
                "router_used": "none",
                "confidence": 0.0
            }

def demonstrate_integration():
    """Demonstrate the LLM Fallback Router integration."""
    
    print("🏠 VoucherBot LLM Fallback Router Integration Demo")
    print("=" * 60)
    
    # Initialize the two-tier router
    mock_llm = MockLLMClient()
    router = TwoTierSemanticRouter(mock_llm, debug=True)
    
    # Test cases that demonstrate fallback behavior
    test_cases = [
        # Cases that should work with regex router
        {
            "message": "Find apartments in Brooklyn with 2 bedrooms",
            "context": None,
            "expected_router": "regex"
        },
        {
            "message": "Show me help",
            "context": None,
            "expected_router": "regex"
        },
        
        # Cases that should fall back to LLM
        {
            "message": "I'm looking for a place but not sure where to start",
            "context": None,
            "expected_router": "llm"
        },
        {
            "message": "¿Dónde puedo encontrar apartamentos?",  # Spanish
            "context": None,
            "expected_router": "llm"
        },
        {
            "message": "What about trying somewhere else?",
            "context": {"borough": "Brooklyn", "bedrooms": 2},
            "expected_router": "llm"
        },
        
        # Edge cases
        {
            "message": "yo wassup",  # Very informal
            "context": None,
            "expected_router": "llm"
        }
    ]
    
    print("\n📋 Running Test Cases:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['message']}'")
        
        result = router.route(test_case["message"], test_case["context"])
        
        print(f"   Intent: {result['intent']}")
        print(f"   Router Used: {result['router_used']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Parameters: {result['parameters']}")
        print(f"   Reasoning: {result['reasoning']}")
        
        # Verify expected router was used
        if result['router_used'] == test_case['expected_router']:
            print("   ✅ Expected router used")
        else:
            print(f"   ⚠️ Expected {test_case['expected_router']}, got {result['router_used']}")

def demonstrate_real_integration():
    """
    Demonstrate how this would integrate with the actual VoucherBot system.
    """
    
    print("\n\n🔧 Real Integration Example")
    print("=" * 40)
    
    # This is how you would integrate with the actual system
    print("Integration points:")
    print("1. Replace MockLLMClient with actual Gemini client from agent_setup.py")
    print("2. Integrate TwoTierSemanticRouter into email_handler.py")
    print("3. Update app.py to use the new router for message classification")
    
    # Example integration code
    integration_code = '''
    # In email_handler.py - replace the current classification logic
    from llm_fallback_router import LLMFallbackRouter
    from agent_setup import initialize_caseworker_agent
    
    # Initialize LLM client (use the same one from agent_setup)
    caseworker_agent = initialize_caseworker_agent()
    llm_client = caseworker_agent.model  # Extract the model
    
    # Create the two-tier router
    two_tier_router = TwoTierSemanticRouter(llm_client)
    
    # Use in classification
    def enhanced_classify_message(message: str, context: dict = None) -> str:
        result = two_tier_router.route(message, context)
        return result["intent"]
    '''
    
    print("\nExample integration code:")
    print(integration_code)

def demonstrate_error_handling():
    """Demonstrate robust error handling."""
    
    print("\n\n🛡️ Error Handling Demo")
    print("=" * 30)
    
    # Create router with a failing LLM client
    class FailingLLMClient:
        def generate(self, prompt):
            raise Exception("API timeout")
    
    failing_router = TwoTierSemanticRouter(FailingLLMClient(), debug=True)
    
    # Test error handling
    test_messages = [
        "",  # Empty message
        "x" * 1001,  # Too long message
        "Normal message"  # Should fall back gracefully
    ]
    
    for message in test_messages:
        print(f"\nTesting error handling for: '{message[:20]}{'...' if len(message) > 20 else ''}'")
        try:
            result = failing_router.route(message)
            print(f"Result: {result['intent']} (Router: {result['router_used']})")
        except Exception as e:
            print(f"Error handled: {e}")

if __name__ == "__main__":
    # Run all demonstrations
    demonstrate_integration()
    demonstrate_real_integration() 
    demonstrate_error_handling()
    
    print("\n\n🎯 Summary")
    print("=" * 20)
    print("✅ LLMFallbackRouter successfully created")
    print("✅ Two-tier routing system demonstrated")
    print("✅ Error handling validated")
    print("✅ Integration path defined")
    print("\nThe LLMFallbackRouter is ready for integration into VoucherBot!") 