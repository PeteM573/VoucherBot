#!/usr/bin/env python3
"""
Test suite for the human handoff detection system.
"""

import pytest
from escalation.handoff_detector import HandoffDetector, final_answer
from escalation.contact_directory import get_contact_info

class TestHandoffDetector:
    """Test suite for HandoffDetector class."""
    
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
    
    def test_user_request_triggers(self, detector, context):
        """Test user-driven handoff triggers with various phrasings."""
        test_cases = [
            # Direct requests
            "Can I talk to a caseworker?",
            "I need to speak with someone",
            "This is too confusing",
            "I need help from a human",
            
            # Agency-specific requests
            "How do I contact HRA?",
            "Can you give me the phone number for NYCHA?",
            "What's the number for DSS?",
            "Where is the HASA office?",
            
            # Indirect/polite requests
            "Would it be possible to speak with someone?",
            "I'd like to talk to a person about this",
            "Could you connect me with a caseworker?",
            
            # Frustration indicators
            "I don't understand any of this",
            "This is way too complicated",
            "I'm really confused about the process",
            
            # Location-based requests
            "Where can I go in person?",
            "Is there an office I can visit?",
            "Which location should I go to?",
            
            # Time-sensitive requests
            "I need to speak to someone right away",
            "Can I talk to a caseworker today?",
            "When can I meet with someone?",
            
            # Multi-part requests
            "This is confusing, can I talk to someone who can explain it?",
            "I need help with my application, is there someone I can speak to?",
            "The website isn't working, how do I talk to support?"
        ]
        
        for message in test_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
            assert needs_handoff is True, f"Failed to detect handoff for: {message}"
            assert reason == "user_request"
            assert contact_info is not None
            assert contact_info["name"] == "CityFHEPS (HRA) Support"
    
    def test_case_based_triggers(self, detector, context):
        """Test case-based handoff triggers with various scenarios."""
        test_cases = [
            # Direct discrimination
            "The landlord won't accept my voucher",
            "They said they don't take Section 8",
            "The broker refused my CityFHEPS",
            
            # Indirect discrimination
            "They said the apartment is no longer available after I mentioned Section 8",
            "The agent stopped responding when I brought up my voucher",
            "They keep making excuses after I mentioned HASA",
            
            # Legal questions
            "Is this discrimination?",
            "What are my rights as a voucher holder?",
            "Can they legally refuse my voucher?",
            "Do I need a lawyer for this?",
            
            # Reporting questions
            "How do I file a complaint?",
            "Where can I report housing discrimination?",
            "Who do I contact about voucher discrimination?",
            
            # Mixed scenarios
            "The broker said no vouchers but my friend with cash was accepted",
            "They're charging more rent because I have a voucher",
            "The requirements changed after I mentioned Section 8",
            
            # Specific situations
            "Landlord says voucher amount is too low",
            "They want extra money under the table",
            "Building says they're not 'voucher approved'",
            
            # Multiple issues
            "Landlord won't accept voucher and wants cash deposit",
            "They're discriminating and asking for illegal fees",
            "No vouchers accepted and they won't give it in writing"
        ]
        
        for message in test_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
            assert needs_handoff is True, f"Failed to detect discrimination for: {message}"
            assert reason == "discrimination_case"
            assert contact_info is not None
    
    def test_non_handoff_messages(self, detector, context):
        """Test messages that should not trigger handoff."""
        test_cases = [
            # General inquiries
            "Show me apartments in Brooklyn",
            "What's the maximum rent for CityFHEPS?",
            "How many bedrooms can I get?",
            "Tell me about Section 8",
            
            # Availability questions
            "Are there any units available?",
            "What neighborhoods should I look in?",
            "Do you have any pet-friendly listings?",
            "Show me apartments near trains",
            
            # Process questions
            "How does the voucher work?",
            "What documents do I need?",
            "How long does approval take?",
            "Can I use my voucher in any borough?",
            
            # Specific searches
            "Find 2 bedroom apartments in Queens",
            "Show me places under $2000",
            "Are there units with utilities included?",
            "Look for apartments with laundry",
            
            # Mixed queries
            "What's the voucher amount for a 2 bedroom?",
            "Do these apartments accept Section 8?",
            "Can I afford this apartment with CityFHEPS?",
            
            # Information requests
            "What's the income limit for Section 8?",
            "How much is the CityFHEPS bonus?",
            "When does my voucher expire?"
        ]
        
        for message in test_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
            assert needs_handoff is False, f"Incorrectly triggered handoff for: {message}"
            assert reason is None
            assert contact_info is None
    
    def test_contact_info_by_voucher(self):
        """Test contact info retrieval for different voucher types and variations."""
        test_cases = [
            # Standard names
            ("CityFHEPS", "CityFHEPS (HRA) Support"),
            ("Section 8", "NYCHA Section 8 Customer Contact Center"),
            ("HASA", "HIV/AIDS Services Administration"),
            
            # Common variations
            ("CITYFHEPS", "CityFHEPS (HRA) Support"),
            ("FHEPS", "CityFHEPS (HRA) Support"),
            ("section8", "NYCHA Section 8 Customer Contact Center"),
            ("Section-8", "NYCHA Section 8 Customer Contact Center"),
            
            # Edge cases
            ("city fheps", "CityFHEPS (HRA) Support"),
            ("SECTION EIGHT", "NYCHA Section 8 Customer Contact Center"),
            ("H.A.S.A.", "HIV/AIDS Services Administration"),
            
            # Invalid/unknown types
            ("Unknown", "NYC Housing Connect Support"),
            ("", "NYC Housing Connect Support"),
            (None, "NYC Housing Connect Support")
        ]
        
        for voucher_type, expected_name in test_cases:
            contact_info = get_contact_info(voucher_type=voucher_type)
            assert contact_info is not None
            assert contact_info["name"] == expected_name, f"Wrong contact for: {voucher_type}"
            assert all(key in contact_info for key in ["phone", "email", "address", "hours"])
    
    def test_message_formatting(self, detector):
        """Test handoff message formatting with different scenarios."""
        # Test user request formatting
        contact_info = get_contact_info("CityFHEPS")
        user_msg = detector.format_handoff_message("user_request", contact_info)
        
        assert "speak with a human caseworker" in user_msg
        assert contact_info["phone"] in user_msg
        assert contact_info["email"] in user_msg
        assert contact_info["address"] in user_msg
        assert contact_info["hours"] in user_msg
        assert "I'm still here if you need help" in user_msg
        
        # Test discrimination case formatting
        disc_msg = detector.format_handoff_message("discrimination_case", contact_info)
        
        assert "housing discrimination" in disc_msg
        assert "illegal in NYC" in disc_msg
        assert "NYC Commission on Human Rights" in disc_msg
        assert "212-416-0197" in disc_msg
        assert "NYS Division of Human Rights" in disc_msg
        assert "1-888-392-3644" in disc_msg
        assert contact_info["phone"] in disc_msg
        assert contact_info["email"] in disc_msg
    
    def test_integration_with_search(self, detector, context):
        """Test integration with search functionality and mixed scenarios."""
        # Search messages with potential trigger words (should not trigger)
        search_with_triggers = [
            "Find apartments that accept Section 8",
            "Search for CityFHEPS units in Brooklyn",
            "Show me places where I can talk to the landlord",
            "Looking for buildings with on-site management office",
            "Need apartments with easy application process",
            "Want to see units with helpful staff",
            "Search for places with good communication",
            "Find apartments with responsive management"
        ]
        
        for message in search_with_triggers:
            needs_handoff, reason, _ = detector.detect_handoff(message, context)
            assert needs_handoff is False, f"Search incorrectly triggered handoff: {message}"
        
        # Handoff messages with search terms (should trigger)
        handoff_with_search = [
            "I need to talk to someone about searching in Brooklyn",
            "This apartment search is too confusing",
            "Can I speak with a caseworker about available units?",
            "The landlord won't accept my voucher for this apartment",
            "Need help understanding how to search with my voucher",
            "Is it discrimination if they remove the listing after I mention Section 8?",
            "Can someone explain these apartment requirements to me?",
            "I'm confused about which units I can apply for"
        ]
        
        for message in handoff_with_search:
            needs_handoff, reason, _ = detector.detect_handoff(message, context)
            assert needs_handoff is True, f"Handoff not detected for: {message}"
    
    def test_edge_cases(self, detector, context):
        """Test edge cases and boundary conditions."""
        edge_cases = [
            # Informal/colloquial requests
            "yo can i talk to someone?",
            "need human asap!!",
            "this is whack, get me a real person",
            "bruh i need help fr",
            "can't deal w/this anymore need human",
            
            # Mixed intent messages
            "looking for apartments but need to talk to someone first",
            "can't find anything, can someone help?",
            "searching is confusing, need human assistance",
            "tried searching but need to speak with a caseworker",
            "want to look in brooklyn but need help understanding the process",
            
            # Compound discrimination cases
            "they said no section 8 and then deleted the listing",
            "broker ghosted after voucher mention and relisted higher",
            "landlord changed requirements after i mentioned cityfheps",
            "they keep making excuses since i told them about my voucher",
            "first they said yes but changed their mind after section 8 came up",
            
            # Multi-language snippets
            "necesito hablar con alguien",
            "需要人工帮助",
            "besoin de parler à quelqu'un",
            "нужна помощь человека",
            "مساعدة من شخص حقيقي",
            
            # Ambiguous cases
            "help with application",
            "need assistance please",
            "having trouble with this",
            "not sure what to do",
            "this isn't working",
            
            # Emotional/urgent requests
            "frustrated!!!",
            "getting nowhere!!",
            "HELP!!",
            "so confused!!!",
            "urgent help needed",
            
            # Subtle discrimination indicators
            "they keep changing the requirements",
            "price went up after mentioning voucher",
            "suddenly not available anymore",
            "they're giving me the runaround",
            "keeps making excuses about paperwork"
        ]
        
        for message in edge_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
            assert needs_handoff is True, f"Failed to detect handoff for edge case: {message}"
            assert reason in ["user_request", "discrimination_case"]
            assert contact_info is not None
            assert contact_info["name"] == "CityFHEPS (HRA) Support"

        # Test non-handoff edge cases
        non_handoff_edge_cases = [
            # Search-related help
            "help me find apartments",
            "help with searching",
            "help finding places",
            "need help looking",
            "assist with search",
            
            # General questions
            "what help can i get?",
            "how does this help?",
            "is help available?",
            "where can help be found?",
            
            # Ambiguous but search-related
            "looking for help with search",
            "need assistance finding places",
            "help me understand the listings",
            "assistance with apartment search",
            "help navigating options"
        ]
        
        for message in non_handoff_edge_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
            assert needs_handoff is False, f"Incorrectly triggered handoff for non-handoff edge case: {message}"
            assert reason is None
            assert contact_info is None
    
    def test_final_answer_format(self):
        """Test final answer formatting."""
        response = "Test response"
        result = final_answer(response)
        
        assert isinstance(result, dict)
        assert "response" in result
        assert "metadata" in result
        assert result["metadata"]["requires_human_handoff"] is True
        assert result["metadata"]["handoff_type"] == "caseworker" 