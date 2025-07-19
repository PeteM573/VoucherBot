#!/usr/bin/env python3
"""
Comprehensive test suite for handoff detection scenarios.
Tests various types of user inquiries and verifies correct responses.
"""

import pytest
from escalation.handoff_detector import HandoffDetector
from escalation.contact_directory import get_contact_info

class TestHandoffScenarios:
    """Test suite for various handoff scenarios."""
    
    @pytest.fixture
    def detector(self):
        """Create a HandoffDetector instance for testing."""
        return HandoffDetector()
    
    def test_direct_discrimination_cases(self, detector):
        """Test direct discrimination reports."""
        test_cases = [
            # Clear discrimination
            {
                "message": "The landlord said they don't take vouchers",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "Broker told me Section 8 not allowed here",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "Management company refuses HASA clients",
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, _ = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff == case["should_handoff"]
            assert reason == case["expected_reason"]
    
    def test_indirect_discrimination_cases(self, detector):
        """Test indirect or subtle discrimination reports."""
        test_cases = [
            {
                "message": "They keep saying the unit is no longer available when I mention my voucher",
                "context": {"voucher_type": "CityFHEPS", "borough": "Queens"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "Every time I mention Section 8, they stop responding to my calls",
                "context": {"voucher_type": "Section 8", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "They said they prefer working professionals only",
                "context": {"voucher_type": "HASA", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, _ = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff == case["should_handoff"]
            assert reason == case["expected_reason"]
    
    def test_direct_assistance_requests(self, detector):
        """Test direct requests for human assistance."""
        test_cases = [
            {
                "message": "Can I speak with a caseworker?",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "I need to talk to someone about my voucher",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "How do I get in touch with a housing specialist?",
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": True,
                "expected_reason": "user_request"
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, _ = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff == case["should_handoff"]
            assert reason == case["expected_reason"]
    
    def test_complex_assistance_requests(self, detector):
        """Test complex or multi-part assistance requests."""
        test_cases = [
            {
                "message": "I've been searching for weeks but need help understanding my rights and options",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "Can you help me file a complaint about discrimination and connect me with someone?",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "I'm having trouble with my application and need to speak with a specialist",
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": True,
                "expected_reason": "user_request"
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, _ = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff == case["should_handoff"]
            assert reason == case["expected_reason"]
    
    def test_non_handoff_cases(self, detector):
        """Test cases that should not trigger handoff."""
        test_cases = [
            {
                "message": "Can you show me apartments in Brooklyn?",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "should_handoff": False
            },
            {
                "message": "What's the maximum rent for Section 8?",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "should_handoff": False
            },
            {
                "message": "Are there any available units in the Bronx?",
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": False
            },
            {
                "message": "Help me find pet-friendly apartments",
                "context": {"voucher_type": "CityFHEPS", "borough": "Queens"},
                "should_handoff": False
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, _ = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff == case["should_handoff"]
    
    def test_contact_routing(self):
        """Test that contacts are routed correctly based on scenario."""
        test_cases = [
            # HASA discrimination cases should go to Housing Works
            {
                "voucher_type": "HASA",
                "borough": "Brooklyn",
                "is_discrimination": True,
                "expected_name": "Housing Works Legal Team"
            },
            # Section 8 discrimination should go to NYC Commission
            {
                "voucher_type": "Section 8",
                "borough": "Manhattan",
                "is_discrimination": True,
                "expected_name": "NYC Commission on Human Rights"
            },
            # Regular inquiries should go to borough offices
            {
                "voucher_type": "CityFHEPS",
                "borough": "brooklyn",
                "is_discrimination": False,
                "expected_name": "Brooklyn CityFHEPS Office"
            },
            # Unknown voucher types should get default HRA
            {
                "voucher_type": None,
                "borough": None,
                "is_discrimination": False,
                "expected_name": "HRA General Support"
            }
        ]
        
        for case in test_cases:
            contact_info = get_contact_info(
                voucher_type=case["voucher_type"],
                borough=case["borough"],
                is_discrimination=case["is_discrimination"]
            )
            assert contact_info["name"] == case["expected_name"]
    
    def test_message_formatting(self, detector):
        """Test that handoff messages are properly formatted for different scenarios."""
        test_cases = [
            # Discrimination case
            {
                "message": "Landlord won't take my voucher",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "expected_content": [
                    "housing discrimination",
                    "illegal in nyc",
                    "commission on human rights",
                    "division of human rights"
                ]
            },
            # Regular assistance request
            {
                "message": "Need to speak with someone",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "expected_content": [
                    "speak with a human caseworker",
                    "phone",
                    "email",
                    "address"
                ]
            }
        ]
        
        for case in test_cases:
            needs_handoff, reason, contact_info = detector.detect_handoff(case["message"], case["context"])
            assert needs_handoff is True
            
            formatted_msg = detector.format_handoff_message(reason, contact_info)
            
            for content in case["expected_content"]:
                assert content in formatted_msg.lower()
            
            # Verify contact info is included
            assert contact_info["phone"] in formatted_msg
            assert contact_info["email"] in formatted_msg
            assert contact_info["address"] in formatted_msg 