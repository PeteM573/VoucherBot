#!/usr/bin/env python3
"""
Integration tests for handoff detection system.
Tests interaction with other tools and ensures appropriate handoff decisions.
"""

import pytest
from escalation.handoff_detector import HandoffDetector, final_answer
from escalation.contact_directory import get_contact_info

class TestHandoffIntegration:
    """Test suite for handoff detection integration."""
    
    @pytest.fixture
    def detector(self):
        """Create a HandoffDetector instance for testing."""
        return HandoffDetector()
    
    @pytest.fixture
    def context(self):
        """Create a sample context for testing."""
        return {
            "voucher_type": "CityFHEPS",
            "borough": "Brooklyn"
        }
    
    def test_search_vs_handoff(self, detector, context):
        """Test that search-related queries don't trigger handoff."""
        search_queries = [
            # Basic searches
            "Find apartments in Brooklyn",
            "Show me places that accept Section 8",
            "Search for 2 bedroom units",
            "List CityFHEPS apartments",
            
            # Complex searches
            "Find 2 bedroom apartments in Manhattan under $2500 that accept Section 8",
            "Show me pet-friendly units in Brooklyn with CityFHEPS",
            "Looking for accessible apartments near trains that take HASA",
            "Search for available units with laundry and elevator",
            
            # Search with help terms
            "Help me find apartments",
            "I need help searching for places",
            "Can you help locate units?",
            "Assist me in finding housing",
            
            # Questions about search
            "How do I search for apartments?",
            "What should I look for in listings?",
            "Where can I find more listings?",
            "What areas should I search in?",
            
            # Search refinements
            "Can you narrow down the search?",
            "Show me different options",
            "Filter by price range",
            "Sort by location"
        ]
        
        for query in search_queries:
            needs_handoff, reason, contact_info = detector.detect_handoff(query, context)
            assert needs_handoff is False, f"Search query incorrectly triggered handoff: {query}"
            assert reason is None
            assert contact_info is None

    def test_mixed_intent_handling(self, detector, context):
        """Test handling of messages with both search and handoff intent."""
        mixed_queries = [
            # Should trigger handoff
            ("I've been searching but need to talk to someone about discrimination", True),
            ("Can't find anything, can I speak with a caseworker?", True),
            ("Looking at listings but landlords won't take my voucher", True),
            ("Tried searching but need help understanding my rights", True),
            ("Been looking all day but need to report discrimination", True),
            
            # Should not trigger handoff
            ("Help me search for better apartments", False),
            ("Need help finding more listings", False),
            ("Can you help me look in different areas?", False),
            ("Assist me with my apartment search", False),
            ("Help me understand the search results", False)
        ]
        
        for query, should_handoff in mixed_queries:
            needs_handoff, reason, contact_info = detector.detect_handoff(query, context)
            assert needs_handoff == should_handoff, f"Wrong handoff decision for: {query}"
            if should_handoff:
                assert reason in ["user_request", "discrimination_case"]
                assert contact_info is not None
            else:
                assert reason is None
                assert contact_info is None

    def test_discrimination_with_borough(self, detector):
        """Test discrimination cases with borough-specific routing."""
        test_cases = [
            # Manhattan cases
            {
                "message": "Landlord in Manhattan won't take my voucher",
                "context": {"voucher_type": "Section 8", "borough": "manhattan"},
                "expected_office": "Manhattan NYCHA Section 8 Office"
            },
            # Brooklyn cases
            {
                "message": "Broker in Brooklyn is discriminating",
                "context": {"voucher_type": "CityFHEPS", "borough": "brooklyn"},
                "expected_office": "Brooklyn CityFHEPS Office"
            },
            # Bronx cases
            {
                "message": "Agent in the Bronx keeps making excuses",
                "context": {"voucher_type": "HASA", "borough": "bronx"},
                "expected_office": "HIV/AIDS Services Administration"  # HASA doesn't have borough offices
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff is True
            assert reason == "discrimination_case"
            assert contact_info is not None
            if "Office" in case["expected_office"]:
                assert contact_info["name"] == case["expected_office"]

    def test_handoff_message_formatting(self, detector, context):
        """Test that handoff messages are properly formatted."""
        test_cases = [
            # User request
            {
                "message": "Can I speak with someone?",
                "expected_content": ["speak with a human caseworker", "phone", "email", "address"]
            },
            # Discrimination case
            {
                "message": "Landlord won't take my voucher",
                "expected_content": ["housing discrimination", "illegal in nyc", "commission on human rights"]
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(case["message"], context)
            assert needs_handoff is True
            
            # Format the message
            formatted_msg = detector.format_handoff_message(reason, contact_info)
            
            # Check required content
            for content in case["expected_content"]:
                assert content in formatted_msg.lower()
            
            # Check contact info inclusion
            assert contact_info["phone"] in formatted_msg
            assert contact_info["email"] in formatted_msg
            assert contact_info["address"] in formatted_msg

    def test_non_interference_with_tools(self, detector, context):
        """Test that handoff detection doesn't interfere with other tool operations."""
        tool_specific_queries = [
            # Search tool queries
            "Search for apartments in Brooklyn",
            "Find Section 8 units",
            "Look for 2 bedrooms",
            
            # Filter tool queries
            "Filter by price under $2000",
            "Show only pet-friendly units",
            "Filter to elevator buildings",
            
            # Sort tool queries
            "Sort by price",
            "Order by distance",
            "Sort newest first",
            
            # Map tool queries
            "Show on map",
            "Display locations",
            "View on map",
            
            # Save/favorite tool queries
            "Save this listing",
            "Add to favorites",
            "Bookmark this one"
        ]
        
        for query in tool_specific_queries:
            needs_handoff, reason, contact_info = detector.detect_handoff(query, context)
            assert needs_handoff is False, f"Tool query incorrectly triggered handoff: {query}"
            assert reason is None
            assert contact_info is None

    def test_contact_info_accuracy(self):
        """Test that contact information is accurate and complete."""
        test_cases = [
            # CityFHEPS
            {
                "voucher_type": "CityFHEPS",
                "borough": "brooklyn",
                "is_discrimination": False,
                "expected_name": "Brooklyn CityFHEPS Office"
            },
            # Section 8
            {
                "voucher_type": "Section 8",
                "borough": "manhattan",
                "is_discrimination": True,
                "expected_name": "NYC Commission on Human Rights"
            },
            # HASA
            {
                "voucher_type": "HASA",
                "borough": None,
                "is_discrimination": True,
                "expected_name": "Housing Works Legal Team"
            }
        ]
        
        for case in test_cases:
            contact_info = get_contact_info(
                voucher_type=case["voucher_type"],
                borough=case["borough"],
                is_discrimination=case["is_discrimination"]
            )
            
            assert contact_info["name"] == case["expected_name"]
            assert all(key in contact_info for key in ["phone", "email", "address", "hours"])
            assert all(contact_info[key] for key in ["phone", "email", "address", "hours"]) 