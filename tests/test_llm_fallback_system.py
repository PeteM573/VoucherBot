#!/usr/bin/env python3
"""
Comprehensive tests for LLM Fallback System in VoucherBot

This test suite is designed to challenge the LLM fallback system's ability
to handle complex, ambiguous, and edge case queries that the regex-based
system cannot process effectively.
"""

import unittest
import sys
import os
import json
import time
from unittest.mock import Mock, patch

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_fallback_router import (
    LLMFallbackRouter, 
    InvalidInputError, 
    LLMProcessingError, 
    InvalidLLMResponseError,
    IntentType,
    RouterResponse
)


class MockLLMClient:
    """Enhanced mock LLM client for comprehensive testing"""
    
    def __init__(self, response_mode="normal", fail_mode=None, delay=0):
        self.response_mode = response_mode
        self.fail_mode = fail_mode
        self.delay = delay
        self.call_count = 0
        self.call_history = []
        
    def generate(self, prompt: str) -> str:
        """Generate mock responses based on test configuration"""
        self.call_count += 1
        self.call_history.append(prompt)
        
        if self.delay > 0:
            time.sleep(self.delay)
            
        if self.fail_mode == "exception":
            raise Exception("Mock LLM client failure")
        elif self.fail_mode == "invalid_json":
            return "This is not valid JSON"
        elif self.fail_mode == "malformed_response":
            return '{"intent": "INVALID_INTENT", "parameters": "not_a_dict"}'
        elif self.fail_mode == "timeout":
            time.sleep(10)  # Simulate timeout
            return self._generate_normal_response(prompt)
        elif self.fail_mode == "partial_response":
            return '{"intent": "SEARCH_LISTINGS"'  # Incomplete JSON
        
        return self._generate_normal_response(prompt)
    
    def _generate_normal_response(self, prompt: str) -> str:
        """Generate realistic mock responses based on prompt content"""
        # Extract message from prompt
        message_start = prompt.find('Message: "') + 10
        message_end = prompt.find('"', message_start)
        message = prompt[message_start:message_end] if message_start > 9 else ""
        
        message_lower = message.lower()
        
        # Sophisticated pattern matching for realistic responses
        if any(phrase in message_lower for phrase in ["find", "search", "looking for", "need apartment"]):
            return json.dumps({
                "intent": "SEARCH_LISTINGS",
                "parameters": {
                    "borough": self._extract_borough(message_lower),
                    "bedrooms": self._extract_bedrooms(message_lower),
                    "max_rent": self._extract_rent(message_lower),
                    "voucher_type": self._extract_voucher(message_lower)
                },
                "reasoning": "User is requesting to search for apartment listings with specific criteria"
            })
        
        elif any(phrase in message_lower for phrase in ["what if", "try", "instead", "change to"]):
            return json.dumps({
                "intent": "REFINE_SEARCH",
                "parameters": {
                    "borough": self._extract_borough(message_lower),
                    "bedrooms": self._extract_bedrooms(message_lower),
                    "max_rent": self._extract_rent(message_lower),
                    "voucher_type": self._extract_voucher(message_lower)
                },
                "reasoning": "User wants to modify their existing search parameters"
            })
        
        elif any(phrase in message_lower for phrase in ["violation", "safe", "building", "inspect"]):
            return json.dumps({
                "intent": "CHECK_VIOLATIONS",
                "parameters": {},
                "reasoning": "User wants to check building safety violations"
            })
        
        elif any(phrase in message_lower for phrase in ["help", "assist", "what can", "how do"]):
            return json.dumps({
                "intent": "HELP_REQUEST",
                "parameters": {},
                "reasoning": "User is requesting help or information"
            })
        
        elif any(phrase in message_lower for phrase in ["what is", "explain", "tell me about"]) and \
             any(voucher in message_lower for voucher in ["section 8", "hasa", "cityfheps", "voucher"]):
            return json.dumps({
                "intent": "ASK_VOUCHER_SUPPORT",
                "parameters": {
                    "voucher_type": self._extract_voucher(message_lower)
                },
                "reasoning": "User is asking for information about voucher programs"
            })
        
        else:
            return json.dumps({
                "intent": "UNKNOWN",
                "parameters": {},
                "reasoning": "Unable to determine clear intent from the message"
            })
    
    def _extract_borough(self, message: str) -> str:
        """Extract borough from message"""
        boroughs = {
            "brooklyn": "Brooklyn", "bk": "Brooklyn",
            "manhattan": "Manhattan", "mnh": "Manhattan",
            "queens": "Queens", "qns": "Queens",
            "bronx": "Bronx", "bx": "Bronx",
            "staten island": "Staten Island", "si": "Staten Island"
        }
        
        for key, value in boroughs.items():
            if key in message:
                return value
        return None
    
    def _extract_bedrooms(self, message: str) -> int:
        """Extract bedroom count from message"""
        import re
        bedroom_match = re.search(r'(\d+)\s*(?:bed|br|bedroom)', message)
        if bedroom_match:
            return int(bedroom_match.group(1))
        elif "studio" in message:
            return 0
        return None
    
    def _extract_rent(self, message: str) -> int:
        """Extract rent amount from message"""
        import re
        rent_match = re.search(r'\$(\d+(?:,\d{3})*)', message)
        if rent_match:
            return int(rent_match.group(1).replace(',', ''))
        return None
    
    def _extract_voucher(self, message: str) -> str:
        """Extract voucher type from message"""
        if "section 8" in message or "section-8" in message:
            return "Section 8"
        elif "cityfheps" in message or "city fheps" in message:
            return "CityFHEPS"
        elif "hasa" in message:
            return "HASA"
        elif "voucher" in message:
            return "Housing Voucher"
        return None


class TestLLMFallbackSystem(unittest.TestCase):
    """Comprehensive test suite for LLM fallback system"""
    
    def setUp(self):
        """Set up test components"""
        self.mock_llm = MockLLMClient()
        self.router = LLMFallbackRouter(self.mock_llm, debug=True)
        
    def test_basic_functionality(self):
        """Test basic LLM fallback functionality"""
        
        test_cases = [
            {
                "message": "I need to find a 2-bedroom apartment in Brooklyn under $2500",
                "expected_intent": "SEARCH_LISTINGS",
                "expected_params": ["borough", "bedrooms", "max_rent"]
            },
            {
                "message": "What if I try Queens instead?",
                "expected_intent": "REFINE_SEARCH",
                "expected_params": ["borough"]
            },
            {
                "message": "Can you help me understand Section 8?",
                "expected_intent": "ASK_VOUCHER_SUPPORT",
                "expected_params": ["voucher_type"]
            },
            {
                "message": "I need help with this system",
                "expected_intent": "HELP_REQUEST",
                "expected_params": []
            }
        ]
        
        print("\n🧠 Testing Basic LLM Fallback Functionality")
        print("=" * 60)
        
        for test_case in test_cases:
            with self.subTest(message=test_case["message"]):
                result = self.router.route(test_case["message"])
                
                print(f"Message: '{test_case['message']}'")
                print(f"  Intent: {result['intent']}")
                print(f"  Parameters: {result['parameters']}")
                print(f"  Reasoning: {result['reasoning']}")
                
                self.assertEqual(result["intent"], test_case["expected_intent"])
                
                # Check that expected parameters are present (if any)
                for param in test_case["expected_params"]:
                    self.assertIn(param, result["parameters"])
                    self.assertIsNotNone(result["parameters"][param])
                
                print("  ✅ Test passed")
                print()

    def test_complex_ambiguous_queries(self):
        """Test LLM's ability to handle complex and ambiguous queries"""
        
        complex_queries = [
            {
                "message": "I'm not sure what I'm looking for but I need somewhere to live",
                "description": "Vague housing request"
            },
            {
                "message": "My current situation is complicated and I need housing assistance",
                "description": "Complex personal situation"
            },
            {
                "message": "Can you help me figure out what kind of apartment I can afford with my voucher?",
                "description": "Multi-part question with implicit search intent"
            },
            {
                "message": "I've been looking everywhere but nothing seems right, maybe you can suggest something different",
                "description": "Frustration with search refinement request"
            },
            {
                "message": "The landlord said something about my voucher not being accepted, what should I do?",
                "description": "Problem-solving request with voucher context"
            },
            {
                "message": "I heard Brooklyn is good but expensive, what about other places that might work?",
                "description": "Comparative analysis request"
            },
            {
                "message": "My caseworker mentioned some options but I'm confused about the differences",
                "description": "Information clarification request"
            },
            {
                "message": "Is it worth looking in Manhattan or should I focus on outer boroughs?",
                "description": "Strategic advice request"
            }
        ]
        
        print("\n🌀 Testing Complex and Ambiguous Queries")
        print("=" * 60)
        
        for query_info in complex_queries:
            with self.subTest(message=query_info["message"]):
                result = self.router.route(query_info["message"])
                
                print(f"Query: '{query_info['message']}'")
                print(f"Description: {query_info['description']}")
                print(f"  Intent: {result['intent']}")
                print(f"  Parameters: {result['parameters']}")
                print(f"  Reasoning: {result['reasoning']}")
                
                # These should not be UNKNOWN if LLM is working properly
                self.assertNotEqual(result["intent"], "UNKNOWN", 
                                  f"LLM failed to classify complex query: {query_info['message']}")
                
                # Reasoning should be provided
                self.assertIsNotNone(result["reasoning"])
                self.assertNotEqual(result["reasoning"].strip(), "")
                
                print("  ✅ Successfully handled complex query")
                print()

    def test_multilingual_support(self):
        """Test LLM's multilingual capabilities"""
        
        multilingual_queries = [
            {
                "message": "Necesito encontrar un apartamento en Brooklyn",
                "language": "es",
                "expected_intent": "SEARCH_LISTINGS",
                "description": "Spanish apartment search"
            },
            {
                "message": "¿Qué es Section 8?",
                "language": "es", 
                "expected_intent": "ASK_VOUCHER_SUPPORT",
                "description": "Spanish voucher information request"
            },
            {
                "message": "我需要在布鲁克林找房子",
                "language": "zh",
                "expected_intent": "SEARCH_LISTINGS",
                "description": "Chinese apartment search"
            },
            {
                "message": "আমার ব্রুকলিনে একটি অ্যাপার্টমেন্ট দরকার",
                "language": "bn",
                "expected_intent": "SEARCH_LISTINGS", 
                "description": "Bengali apartment search"
            },
            {
                "message": "Help me find housing - ayuda por favor",
                "language": "mixed",
                "expected_intent": "SEARCH_LISTINGS",
                "description": "Mixed language request"
            }
        ]
        
        print("\n🌍 Testing Multilingual Support")
        print("=" * 60)
        
        for query_info in multilingual_queries:
            with self.subTest(message=query_info["message"]):
                result = self.router.route(
                    query_info["message"], 
                    language=query_info["language"]
                )
                
                print(f"Query: '{query_info['message']}'")
                print(f"Language: {query_info['language']}")
                print(f"Description: {query_info['description']}")
                print(f"  Intent: {result['intent']}")
                print(f"  Parameters: {result['parameters']}")
                print(f"  Reasoning: {result['reasoning']}")
                
                # Should handle multilingual queries appropriately
                self.assertNotEqual(result["intent"], "UNKNOWN", 
                                  f"LLM failed to handle multilingual query: {query_info['message']}")
                
                print("  ✅ Successfully handled multilingual query")
                print()

    def test_context_awareness(self):
        """Test LLM's ability to use context for better classification"""
        
        context_tests = [
            {
                "message": "try something else",
                "context": '{"borough": "Brooklyn", "bedrooms": 2, "max_rent": 2500}',
                "expected_intent": "REFINE_SEARCH",
                "description": "Vague refinement with search context"
            },
            {
                "message": "what about Manhattan?",
                "context": '{"last_search": "Brooklyn apartments", "results": 5}',
                "expected_intent": "REFINE_SEARCH",
                "description": "Borough change with search history"
            },
            {
                "message": "show me more",
                "context": '{"current_listings": 3, "total_available": 15}',
                "expected_intent": "SEARCH_LISTINGS",
                "description": "Continuation request with listings context"
            },
            {
                "message": "that's too expensive",
                "context": '{"last_shown_rent": 3000, "user_budget": 2500}',
                "expected_intent": "REFINE_SEARCH",
                "description": "Budget feedback with price context"
            }
        ]
        
        print("\n🧠 Testing Context Awareness")
        print("=" * 60)
        
        for test_case in context_tests:
            with self.subTest(message=test_case["message"]):
                result = self.router.route(test_case["message"], test_case["context"])
                
                print(f"Message: '{test_case['message']}'")
                print(f"Context: {test_case['context']}")
                print(f"Description: {test_case['description']}")
                print(f"  Intent: {result['intent']}")
                print(f"  Parameters: {result['parameters']}")
                print(f"  Reasoning: {result['reasoning']}")
                
                # Context should improve classification
                self.assertNotEqual(result["intent"], "UNKNOWN",
                                  f"LLM failed to use context for: {test_case['message']}")
                
                print("  ✅ Successfully used context")
                print()

    def test_error_handling_and_recovery(self):
        """Test LLM fallback system's error handling and recovery"""
        
        error_scenarios = [
            {
                "fail_mode": "invalid_json",
                "description": "Invalid JSON response from LLM"
            },
            {
                "fail_mode": "malformed_response", 
                "description": "Malformed response structure"
            },
            {
                "fail_mode": "partial_response",
                "description": "Incomplete JSON response"
            },
            {
                "fail_mode": "exception",
                "description": "LLM client exception"
            }
        ]
        
        print("\n🚨 Testing Error Handling and Recovery")
        print("=" * 60)
        
        for scenario in error_scenarios:
            with self.subTest(fail_mode=scenario["fail_mode"]):
                # Create router with failing mock LLM
                failing_llm = MockLLMClient(fail_mode=scenario["fail_mode"])
                failing_router = LLMFallbackRouter(failing_llm, debug=True)
                
                print(f"Scenario: {scenario['description']}")
                
                with self.assertRaises((LLMProcessingError, InvalidLLMResponseError)):
                    failing_router.route("Find apartments in Brooklyn")
                
                print("  ✅ Properly raised expected exception")
                print()

    def test_retry_mechanism(self):
        """Test the retry mechanism for failed LLM calls"""
        
        print("\n🔄 Testing Retry Mechanism")
        print("=" * 60)
        
        # Create a mock that fails twice then succeeds
        class RetryTestLLM:
            def __init__(self):
                self.attempt_count = 0
                
            def generate(self, prompt):
                self.attempt_count += 1
                if self.attempt_count <= 2:
                    raise Exception(f"Attempt {self.attempt_count} failed")
                return json.dumps({
                    "intent": "SEARCH_LISTINGS",
                    "parameters": {"borough": "Brooklyn"},
                    "reasoning": f"Succeeded on attempt {self.attempt_count}"
                })
        
        retry_llm = RetryTestLLM()
        retry_router = LLMFallbackRouter(retry_llm, debug=True, max_retries=3)
        
        result = retry_router.route("Find apartments in Brooklyn")
        
        print(f"Total attempts made: {retry_llm.attempt_count}")
        print(f"Final result: {result}")
        
        self.assertEqual(retry_llm.attempt_count, 3)
        self.assertEqual(result["intent"], "SEARCH_LISTINGS")
        
        print("  ✅ Retry mechanism worked correctly")
        print()

    def test_performance_under_load(self):
        """Test LLM fallback performance under various load conditions"""
        
        print("\n⚡ Testing Performance Under Load")
        print("=" * 60)
        
        # Test with different response delays
        delay_tests = [
            {"delay": 0, "description": "Instant response"},
            {"delay": 0.1, "description": "Fast response (100ms)"},
            {"delay": 0.5, "description": "Moderate response (500ms)"},
            {"delay": 1.0, "description": "Slow response (1s)"}
        ]
        
        for delay_test in delay_tests:
            with self.subTest(delay=delay_test["delay"]):
                delayed_llm = MockLLMClient(delay=delay_test["delay"])
                delayed_router = LLMFallbackRouter(delayed_llm, debug=False)
                
                start_time = time.time()
                result = delayed_router.route("Find apartments in Brooklyn")
                end_time = time.time()
                
                actual_time = end_time - start_time
                expected_time = delay_test["delay"]
                
                print(f"Test: {delay_test['description']}")
                print(f"  Expected delay: {expected_time}s")
                print(f"  Actual time: {actual_time:.3f}s")
                print(f"  Result: {result['intent']}")
                
                # Allow for some overhead but should be close to expected
                self.assertGreaterEqual(actual_time, expected_time)
                self.assertLess(actual_time, expected_time + 0.5)  # Max 500ms overhead
                
                print("  ✅ Performance within acceptable range")
                print()

    def test_parameter_normalization(self):
        """Test parameter normalization and validation"""
        
        normalization_tests = [
            {
                "input_params": {"borough": "bk", "bedrooms": "2", "max_rent": "2,500"},
                "expected_borough": "Brooklyn",
                "expected_bedrooms": 2,
                "expected_rent": 2500,
                "description": "Abbreviation and string normalization"
            },
            {
                "input_params": {"borough": "staten island", "voucher_type": "section 8"},
                "expected_borough": "Staten Island", 
                "expected_voucher": "Section 8",
                "description": "Multi-word and voucher normalization"
            },
            {
                "input_params": {"borough": "manhattan", "bedrooms": 0},
                "expected_borough": "Manhattan",
                "expected_bedrooms": 0,
                "description": "Studio apartment (0 bedrooms)"
            }
        ]
        
        print("\n🔧 Testing Parameter Normalization")
        print("=" * 60)
        
        for test_case in normalization_tests:
            with self.subTest(description=test_case["description"]):
                # Create a custom mock response with test parameters
                class CustomMockLLM:
                    def generate(self, prompt):
                        return json.dumps({
                            "intent": "SEARCH_LISTINGS",
                            "parameters": test_case["input_params"],
                            "reasoning": "Test normalization"
                        })
                
                custom_router = LLMFallbackRouter(CustomMockLLM())
                result = custom_router.route("Test message")
                
                print(f"Test: {test_case['description']}")
                print(f"  Input params: {test_case['input_params']}")
                print(f"  Normalized params: {result['parameters']}")
                
                # Check normalization
                if "expected_borough" in test_case:
                    self.assertEqual(result["parameters"]["borough"], test_case["expected_borough"])
                
                if "expected_bedrooms" in test_case:
                    self.assertEqual(result["parameters"]["bedrooms"], test_case["expected_bedrooms"])
                
                if "expected_rent" in test_case:
                    self.assertEqual(result["parameters"]["max_rent"], test_case["expected_rent"])
                
                if "expected_voucher" in test_case:
                    self.assertEqual(result["parameters"]["voucher_type"], test_case["expected_voucher"])
                
                print("  ✅ Parameters normalized correctly")
                print()

    def test_edge_cases_and_boundary_conditions(self):
        """Test edge cases and boundary conditions"""
        
        edge_cases = [
            {
                "message": "",
                "description": "Empty message"
            },
            {
                "message": "   ",
                "description": "Whitespace only"
            },
            {
                "message": "a" * 10000,
                "description": "Very long message"
            },
            {
                "message": "🏠🏡🏘️🏚️🏗️",
                "description": "Emoji only"
            },
            {
                "message": "!@#$%^&*()_+{}[]|\\:;\"'<>?,./",
                "description": "Special characters only"
            },
            {
                "message": "find apartments" + "\n" * 100,
                "description": "Message with many newlines"
            }
        ]
        
        print("\n🔧 Testing Edge Cases and Boundary Conditions")
        print("=" * 60)
        
        for edge_case in edge_cases:
            with self.subTest(message=edge_case["description"]):
                try:
                    if edge_case["message"] == "":
                        # Empty message should raise InvalidInputError
                        with self.assertRaises(InvalidInputError):
                            self.router.route(edge_case["message"])
                        print(f"Test: {edge_case['description']}")
                        print("  ✅ Correctly raised InvalidInputError for empty message")
                    else:
                        result = self.router.route(edge_case["message"])
                        print(f"Test: {edge_case['description']}")
                        print(f"  Intent: {result['intent']}")
                        print(f"  Parameters: {result['parameters']}")
                        print("  ✅ Handled edge case without error")
                    
                except Exception as e:
                    print(f"Test: {edge_case['description']}")
                    print(f"  ❌ Unexpected error: {e}")
                    self.fail(f"Edge case caused unexpected error: {e}")
                
                print()

    def test_regression_scenarios(self):
        """Test known regression scenarios and previously problematic queries"""
        
        regression_tests = [
            {
                "message": "I live in Brooklyn but work in Manhattan",
                "description": "Multiple borough mentions",
                "expected_behavior": "Should not extract both boroughs"
            },
            {
                "message": "My 3 kids need a place to live",
                "description": "Family size vs bedroom count",
                "expected_behavior": "Should not extract '3' as bedrooms"
            },
            {
                "message": "I make $50,000 per year",
                "description": "Annual income vs monthly rent",
                "expected_behavior": "Should not extract as max_rent"
            },
            {
                "message": "Section 8 is a good program",
                "description": "Informational statement vs request",
                "expected_behavior": "Should not be SEARCH_LISTINGS"
            },
            {
                "message": "What if I told you I need help?",
                "description": "Hypothetical vs what-if scenario",
                "expected_behavior": "Should be HELP_REQUEST, not REFINE_SEARCH"
            }
        ]
        
        print("\n🔍 Testing Regression Scenarios")
        print("=" * 60)
        
        for test_case in regression_tests:
            with self.subTest(message=test_case["message"]):
                result = self.router.route(test_case["message"])
                
                print(f"Message: '{test_case['message']}'")
                print(f"Description: {test_case['description']}")
                print(f"Expected behavior: {test_case['expected_behavior']}")
                print(f"  Intent: {result['intent']}")
                print(f"  Parameters: {result['parameters']}")
                print(f"  Reasoning: {result['reasoning']}")
                
                # Verify the specific expected behavior
                if "Multiple borough mentions" in test_case["description"]:
                    # Should not extract both Brooklyn and Manhattan
                    borough = result["parameters"].get("borough")
                    if borough:
                        self.assertIn(borough, ["Brooklyn", "Manhattan"])
                        print(f"  ✅ Correctly extracted single borough: {borough}")
                    else:
                        print("  ✅ Correctly extracted no borough")
                
                elif "Family size vs bedroom count" in test_case["description"]:
                    # Should not extract 3 as bedrooms
                    bedrooms = result["parameters"].get("bedrooms")
                    self.assertNotEqual(bedrooms, 3)
                    print("  ✅ Correctly did not extract family size as bedrooms")
                
                elif "Annual income vs monthly rent" in test_case["description"]:
                    # Should not extract 50000 as max_rent
                    max_rent = result["parameters"].get("max_rent")
                    self.assertNotEqual(max_rent, 50000)
                    print("  ✅ Correctly did not extract annual income as rent")
                
                elif "Informational statement vs request" in test_case["description"]:
                    # Should not be SEARCH_LISTINGS
                    self.assertNotEqual(result["intent"], "SEARCH_LISTINGS")
                    print("  ✅ Correctly did not classify as search request")
                
                elif "Hypothetical vs what-if scenario" in test_case["description"]:
                    # Should be HELP_REQUEST, not REFINE_SEARCH
                    self.assertEqual(result["intent"], "HELP_REQUEST")
                    print("  ✅ Correctly classified as help request")
                
                print()


if __name__ == "__main__":
    # Run the tests with verbose output
    unittest.main(verbosity=2, buffer=True) 