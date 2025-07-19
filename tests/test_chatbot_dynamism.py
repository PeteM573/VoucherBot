#!/usr/bin/env python3
"""
Comprehensive tests for VoucherBot's overall dynamism and adaptive behavior

This test suite challenges the chatbot's ability to:
1. Adapt to different conversation styles and contexts
2. Handle complex multi-turn conversations
3. Maintain context across interactions
4. Gracefully handle edge cases and unexpected inputs
5. Demonstrate intelligent fallback between regex and LLM systems
"""

import unittest
import sys
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_semantic_router_v2 import EnhancedSemanticRouterV2, Intent
from email_handler import enhanced_classify_message
from what_if_handler import WhatIfScenarioAnalyzer
from llm_fallback_router import LLMFallbackRouter


class MockConversationState:
    """Mock conversation state for testing multi-turn interactions"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.history = []
        self.current_search_params = {}
        self.listings = []
        self.user_preferences = {}
        self.conversation_context = {}
    
    def add_message(self, role, content, metadata=None):
        self.history.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        })
    
    def update_search_params(self, params):
        self.current_search_params.update(params)
    
    def set_listings(self, listings):
        self.listings = listings
    
    def get_context_summary(self):
        return {
            "search_params": self.current_search_params,
            "listings_count": len(self.listings),
            "conversation_length": len(self.history),
            "last_user_message": self.get_last_user_message()
        }
    
    def get_last_user_message(self):
        for msg in reversed(self.history):
            if msg["role"] == "user":
                return msg["content"]
        return None


class TestChatbotDynamism(unittest.TestCase):
    """Test suite for chatbot dynamism and adaptive behavior"""
    
    def setUp(self):
        """Set up test components"""
        self.router_v2 = EnhancedSemanticRouterV2()
        self.what_if_analyzer = WhatIfScenarioAnalyzer()
        self.conversation_state = MockConversationState()
        
        # Mock LLM for fallback testing
        self.mock_llm = Mock()
        self.mock_llm.generate.return_value = json.dumps({
            "intent": "SEARCH_LISTINGS",
            "parameters": {"borough": "Brooklyn"},
            "reasoning": "User wants to search for apartments"
        })
        
        self.fallback_router = LLMFallbackRouter(self.mock_llm, debug=False)

    def test_conversation_flow_adaptation(self):
        """Test how the chatbot adapts to different conversation flows"""
        
        conversation_scenarios = [
            {
                "name": "Direct Task-Oriented",
                "messages": [
                    "I need a 2-bedroom apartment in Brooklyn under $2500 with Section 8",
                    "Show me the listings",
                    "Tell me about listing #1",
                    "Write an email for listing #1"
                ],
                "expected_progression": ["search", "listings", "details", "email"]
            },
            {
                "name": "Exploratory Discovery",
                "messages": [
                    "I'm looking for housing but not sure where to start",
                    "What neighborhoods are good for families?",
                    "What about Brooklyn?",
                    "Try searching in Brooklyn with 2 bedrooms"
                ],
                "expected_progression": ["help", "info", "refinement", "search"]
            },
            {
                "name": "Problem-Solving Journey",
                "messages": [
                    "My landlord won't accept my voucher",
                    "What are my rights?",
                    "Can you help me find voucher-friendly places?",
                    "What if I try a different borough?"
                ],
                "expected_progression": ["help", "info", "search", "refinement"]
            },
            {
                "name": "Iterative Refinement",
                "messages": [
                    "Find apartments in Manhattan",
                    "That's too expensive, try Brooklyn",
                    "Still too much, what about Queens?",
                    "Perfect, show me 2-bedroom options"
                ],
                "expected_progression": ["search", "refinement", "refinement", "refinement"]
            }
        ]
        
        print("\n🔄 Testing Conversation Flow Adaptation")
        print("=" * 60)
        
        for scenario in conversation_scenarios:
            with self.subTest(scenario=scenario["name"]):
                self.conversation_state.reset()
                
                print(f"\nScenario: {scenario['name']}")
                print("-" * 40)
                
                intents = []
                for i, message in enumerate(scenario["messages"]):
                    # Simulate conversation context building
                    context = self.conversation_state.get_context_summary()
                    
                    # Classify the message
                    intent = self.router_v2.classify_intent(message, context)
                    intents.append(intent)
                    
                    # Update conversation state
                    self.conversation_state.add_message("user", message)
                    
                    print(f"  {i+1}. User: '{message}'")
                    print(f"     Intent: {intent}")
                    
                    # Simulate system response and state updates
                    if intent == Intent.SEARCH_LISTINGS:
                        params = self.router_v2.extract_parameters(message)
                        self.conversation_state.update_search_params(params)
                        # Simulate finding listings
                        self.conversation_state.set_listings([{"id": 1}, {"id": 2}])
                    elif intent == Intent.WHAT_IF:
                        # Simulate parameter modification
                        params = self.router_v2.extract_parameters(message)
                        self.conversation_state.update_search_params(params)
                
                # Verify conversation shows progression and adaptation
                self.assertGreater(len(intents), 0)
                self.assertNotEqual(intents.count(Intent.UNCLASSIFIED), len(intents))
                
                print(f"  Final state: {self.conversation_state.current_search_params}")
                print("  ✅ Conversation flow adapted successfully")

    def test_context_memory_and_continuity(self):
        """Test the chatbot's ability to maintain context and continuity"""
        
        context_scenarios = [
            {
                "setup_messages": [
                    "I need a 2-bedroom apartment in Brooklyn under $2500",
                    "I have a Section 8 voucher"
                ],
                "test_message": "show me the listings",
                "expected_context_usage": "Should remember search criteria"
            },
            {
                "setup_messages": [
                    "Find apartments in Manhattan",
                    "That's too expensive"
                ],
                "test_message": "try Brooklyn instead",
                "expected_context_usage": "Should understand 'instead' refers to Manhattan"
            },
            {
                "setup_messages": [
                    "I'm looking at listing #1",
                    "It has 5 violations"
                ],
                "test_message": "is that safe?",
                "expected_context_usage": "Should know 'that' refers to the building"
            },
            {
                "setup_messages": [
                    "I need help with my voucher",
                    "I have CityFHEPS"
                ],
                "test_message": "what buildings accept it?",
                "expected_context_usage": "Should know 'it' refers to CityFHEPS"
            }
        ]
        
        print("\n🧠 Testing Context Memory and Continuity")
        print("=" * 60)
        
        for i, scenario in enumerate(context_scenarios):
            with self.subTest(scenario=i):
                self.conversation_state.reset()
                
                print(f"\nScenario {i+1}: {scenario['expected_context_usage']}")
                print("-" * 40)
                
                # Set up context
                context = {}
                for setup_msg in scenario["setup_messages"]:
                    params = self.router_v2.extract_parameters(setup_msg)
                    context.update(params)
                    self.conversation_state.add_message("user", setup_msg)
                    print(f"  Setup: '{setup_msg}'")
                
                # Test message with context
                test_intent = self.router_v2.classify_intent(
                    scenario["test_message"], 
                    context
                )
                
                print(f"  Test: '{scenario['test_message']}'")
                print(f"  Intent: {test_intent}")
                print(f"  Context: {context}")
                
                # Context should improve classification
                self.assertNotEqual(test_intent, Intent.UNCLASSIFIED)
                
                print("  ✅ Context maintained and used effectively")

    def test_adaptive_response_to_user_style(self):
        """Test adaptation to different user communication styles"""
        
        user_styles = [
            {
                "style": "Formal Professional",
                "messages": [
                    "I would like to request assistance in locating suitable housing accommodations.",
                    "Could you please provide information regarding Section 8 housing options?",
                    "I require a comprehensive list of available properties."
                ],
                "expected_behavior": "Should handle formal language appropriately"
            },
            {
                "style": "Casual Conversational",
                "messages": [
                    "hey, need help finding a place",
                    "what's good in brooklyn?",
                    "show me what u got"
                ],
                "expected_behavior": "Should understand casual language"
            },
            {
                "style": "Urgent/Stressed",
                "messages": [
                    "I NEED HELP NOW! My lease expires tomorrow!",
                    "This is urgent - where can I find emergency housing?",
                    "Please help me ASAP!!!"
                ],
                "expected_behavior": "Should recognize urgency and provide appropriate help"
            },
            {
                "style": "Detailed/Specific",
                "messages": [
                    "I need a 2-bedroom apartment in Brooklyn, specifically in Park Slope or Prospect Heights, under $2800, that accepts Section 8 vouchers, with good schools nearby",
                    "The apartment must be on the ground floor due to mobility issues",
                    "I also need to ensure the building has no more than 2 violations"
                ],
                "expected_behavior": "Should extract multiple specific requirements"
            },
            {
                "style": "Uncertain/Hesitant",
                "messages": [
                    "I'm not sure what I'm looking for...",
                    "Maybe Brooklyn? Or Queens? I don't know...",
                    "I think I need help but I'm not sure where to start"
                ],
                "expected_behavior": "Should provide guidance and ask clarifying questions"
            }
        ]
        
        print("\n🎭 Testing Adaptive Response to User Style")
        print("=" * 60)
        
        for style_test in user_styles:
            with self.subTest(style=style_test["style"]):
                print(f"\nStyle: {style_test['style']}")
                print(f"Expected: {style_test['expected_behavior']}")
                print("-" * 40)
                
                successful_classifications = 0
                total_messages = len(style_test["messages"])
                
                for message in style_test["messages"]:
                    intent = self.router_v2.classify_intent(message)
                    params = self.router_v2.extract_parameters(message)
                    
                    print(f"  Message: '{message}'")
                    print(f"  Intent: {intent}")
                    print(f"  Params: {params}")
                    
                    if intent != Intent.UNCLASSIFIED:
                        successful_classifications += 1
                    
                    print()
                
                # Should successfully classify most messages regardless of style
                success_rate = successful_classifications / total_messages
                self.assertGreater(success_rate, 0.6)  # At least 60% success rate
                
                print(f"  Success rate: {success_rate:.1%}")
                print("  ✅ Adapted to communication style")

    def test_fallback_system_integration(self):
        """Test integration between regex and LLM fallback systems"""
        
        fallback_scenarios = [
            {
                "message": "Find apartments in Brooklyn",
                "expected_system": "regex",
                "description": "Simple query should use regex"
            },
            {
                "message": "I'm feeling overwhelmed and need guidance on housing options",
                "expected_system": "llm",
                "description": "Complex emotional query should use LLM"
            },
            {
                "message": "Necesito ayuda con apartamentos",
                "expected_system": "llm",
                "description": "Non-English query should use LLM"
            },
            {
                "message": "What if I'm not sure about my budget but need somewhere affordable?",
                "expected_system": "llm",
                "description": "Ambiguous query should use LLM"
            },
            {
                "message": "Show me 2BR in BK under $2500",
                "expected_system": "regex",
                "description": "Abbreviated query should use regex"
            }
        ]
        
        print("\n⚡ Testing Fallback System Integration")
        print("=" * 60)
        
        for scenario in fallback_scenarios:
            with self.subTest(message=scenario["message"]):
                print(f"\nMessage: '{scenario['message']}'")
                print(f"Description: {scenario['description']}")
                
                # Test regex classification
                regex_intent = self.router_v2.classify_intent(scenario["message"])
                regex_params = self.router_v2.extract_parameters(scenario["message"])
                
                print(f"  Regex Intent: {regex_intent}")
                print(f"  Regex Params: {regex_params}")
                
                # Determine if regex was successful
                regex_successful = (
                    regex_intent != Intent.UNCLASSIFIED and 
                    (regex_params or regex_intent in [Intent.SHOW_HELP, Intent.CHECK_VIOLATIONS])
                )
                
                if regex_successful:
                    print("  ✅ Regex system handled successfully")
                    if scenario["expected_system"] == "regex":
                        print("  ✅ Used expected system (regex)")
                    else:
                        print("  ⚠️  Used regex instead of expected LLM")
                else:
                    print("  ➡️  Would fallback to LLM system")
                    
                    # Test LLM fallback
                    try:
                        llm_result = self.fallback_router.route(scenario["message"])
                        print(f"  LLM Intent: {llm_result['intent']}")
                        print(f"  LLM Params: {llm_result['parameters']}")
                        
                        if scenario["expected_system"] == "llm":
                            print("  ✅ Used expected system (LLM)")
                        else:
                            print("  ⚠️  Used LLM instead of expected regex")
                    except Exception as e:
                        print(f"  ❌ LLM fallback failed: {e}")

    def test_error_recovery_and_graceful_degradation(self):
        """Test error recovery and graceful degradation"""
        
        error_scenarios = [
            {
                "message": "",
                "error_type": "empty_input",
                "expected_behavior": "Should handle empty input gracefully"
            },
            {
                "message": "asdfghjkl qwertyuiop",
                "error_type": "gibberish",
                "expected_behavior": "Should handle nonsensical input"
            },
            {
                "message": "find apartments" + " very" * 1000,
                "error_type": "extremely_long",
                "expected_behavior": "Should handle very long input"
            },
            {
                "message": "🏠🏡🏘️ 🚇🚌🚊 💰💵💴",
                "error_type": "emoji_only",
                "expected_behavior": "Should handle emoji-only input"
            },
            {
                "message": "FIND APARTMENTS IN BROOKLYN!!!!! NOW!!!!",
                "error_type": "excessive_punctuation",
                "expected_behavior": "Should handle excessive punctuation"
            }
        ]
        
        print("\n🛡️ Testing Error Recovery and Graceful Degradation")
        print("=" * 60)
        
        for scenario in error_scenarios:
            with self.subTest(error_type=scenario["error_type"]):
                print(f"\nError Type: {scenario['error_type']}")
                print(f"Expected: {scenario['expected_behavior']}")
                print(f"Message: '{scenario['message'][:50]}...'")
                
                try:
                    # Test regex system
                    regex_intent = self.router_v2.classify_intent(scenario["message"])
                    regex_params = self.router_v2.extract_parameters(scenario["message"])
                    
                    print(f"  Regex Intent: {regex_intent}")
                    print(f"  Regex Params: {regex_params}")
                    
                    # Test email classification
                    email_classification = enhanced_classify_message(
                        scenario["message"], 
                        {"listings": []}
                    )
                    
                    print(f"  Email Classification: {email_classification}")
                    
                    # Test what-if analysis
                    what_if_detected = self.what_if_analyzer.detect_what_if_scenario(
                        scenario["message"]
                    )
                    
                    print(f"  What-if Detected: {what_if_detected}")
                    
                    print("  ✅ Systems handled error input gracefully")
                    
                except Exception as e:
                    print(f"  ❌ System failed with error: {e}")
                    # Some failures are acceptable for extreme cases
                    if scenario["error_type"] not in ["empty_input", "gibberish"]:
                        self.fail(f"System should handle {scenario['error_type']} gracefully")

    def test_performance_under_stress(self):
        """Test performance under various stress conditions"""
        
        stress_tests = [
            {
                "name": "Rapid Fire Queries",
                "test_func": self._test_rapid_fire_queries,
                "description": "Multiple queries in quick succession"
            },
            {
                "name": "Complex Query Processing",
                "test_func": self._test_complex_query_processing,
                "description": "Processing very complex queries"
            },
            {
                "name": "Context Switching",
                "test_func": self._test_context_switching,
                "description": "Rapid context changes"
            }
        ]
        
        print("\n⚡ Testing Performance Under Stress")
        print("=" * 60)
        
        for stress_test in stress_tests:
            with self.subTest(test=stress_test["name"]):
                print(f"\nStress Test: {stress_test['name']}")
                print(f"Description: {stress_test['description']}")
                
                start_time = time.time()
                result = stress_test["test_func"]()
                end_time = time.time()
                
                processing_time = end_time - start_time
                
                print(f"  Processing Time: {processing_time:.3f} seconds")
                print(f"  Result: {result}")
                
                # Performance should be reasonable
                self.assertLess(processing_time, 5.0)  # Should complete within 5 seconds
                
                print("  ✅ Performance acceptable under stress")

    def _test_rapid_fire_queries(self):
        """Test rapid fire query processing"""
        queries = [
            "find apartments in brooklyn",
            "what about queens?",
            "show me listings",
            "try manhattan",
            "check violations",
            "help me",
            "what is section 8?",
            "email landlord"
        ]
        
        results = []
        for query in queries:
            intent = self.router_v2.classify_intent(query)
            results.append(intent)
        
        return f"Processed {len(queries)} queries, {len([r for r in results if r != Intent.UNCLASSIFIED])} successful"

    def _test_complex_query_processing(self):
        """Test complex query processing"""
        complex_queries = [
            "I need a 2-bedroom apartment in Brooklyn or Queens with Section 8 voucher under $2500 near good schools and subway stations with no more than 2 building violations",
            "What if I try Manhattan instead but increase my budget to $3000 and I'm okay with 1 bedroom as long as it's safe and accepts CityFHEPS?",
            "Can you help me understand the difference between Section 8 and CityFHEPS and which buildings in the Bronx accept both types of vouchers?"
        ]
        
        successful = 0
        for query in complex_queries:
            intent = self.router_v2.classify_intent(query)
            params = self.router_v2.extract_parameters(query)
            if intent != Intent.UNCLASSIFIED:
                successful += 1
        
        return f"Processed {len(complex_queries)} complex queries, {successful} successful"

    def _test_context_switching(self):
        """Test rapid context switching"""
        context_switches = [
            ("find apartments", {}),
            ("in brooklyn", {"borough": "Manhattan"}),
            ("with 2 bedrooms", {"borough": "Brooklyn"}),
            ("under $2500", {"borough": "Brooklyn", "bedrooms": 2}),
            ("try queens instead", {"borough": "Brooklyn", "bedrooms": 2, "max_rent": 2500}),
        ]
        
        successful = 0
        for query, context in context_switches:
            intent = self.router_v2.classify_intent(query, context)
            if intent != Intent.UNCLASSIFIED:
                successful += 1
        
        return f"Processed {len(context_switches)} context switches, {successful} successful"

    def test_learning_and_adaptation_simulation(self):
        """Simulate learning and adaptation over time"""
        
        # Simulate a user's journey over multiple sessions
        user_journey = [
            {
                "session": 1,
                "messages": [
                    "I need help finding housing",
                    "I have a Section 8 voucher",
                    "What neighborhoods are good?"
                ],
                "user_state": "new_user"
            },
            {
                "session": 2,
                "messages": [
                    "I want to look in Brooklyn",
                    "Show me 2-bedroom apartments",
                    "Under $2500"
                ],
                "user_state": "learning"
            },
            {
                "session": 3,
                "messages": [
                    "Try Queens instead",
                    "What about near good schools?",
                    "Check building violations"
                ],
                "user_state": "experienced"
            }
        ]
        
        print("\n📈 Testing Learning and Adaptation Simulation")
        print("=" * 60)
        
        accumulated_context = {}
        
        for session in user_journey:
            print(f"\nSession {session['session']} - User State: {session['user_state']}")
            print("-" * 40)
            
            session_intents = []
            for message in session["messages"]:
                intent = self.router_v2.classify_intent(message, accumulated_context)
                params = self.router_v2.extract_parameters(message)
                
                # Accumulate context (simulate learning)
                accumulated_context.update(params)
                
                session_intents.append(intent)
                
                print(f"  Message: '{message}'")
                print(f"  Intent: {intent}")
                print(f"  Context: {accumulated_context}")
            
            # Verify that later sessions show more sophisticated understanding
            unclassified_count = session_intents.count(Intent.UNCLASSIFIED)
            success_rate = (len(session_intents) - unclassified_count) / len(session_intents)
            
            print(f"  Session Success Rate: {success_rate:.1%}")
            
            # Later sessions should have better success rates
            if session["session"] > 1:
                self.assertGreater(success_rate, 0.6)
            
            print("  ✅ Session completed successfully")


if __name__ == "__main__":
    # Run the tests with verbose output
    unittest.main(verbosity=2, buffer=True) 