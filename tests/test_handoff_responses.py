import pytest
from escalation.handoff_detector import HandoffDetector
from typing import Dict, List, Tuple

class TestHandoffResponses:
    """Test specific handoff responses for various input scenarios."""

    @pytest.fixture
    def detector(self):
        """Create a fresh HandoffDetector instance for each test."""
        return HandoffDetector()

    def verify_handoff_response(self, detector: HandoffDetector, message: str, 
                              context: Dict, expected_handoff: bool, 
                              expected_reason: str = None) -> None:
        """Helper method to verify handoff detection results."""
        needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
        
        assert needs_handoff == expected_handoff, \
            f"Expected handoff={expected_handoff} but got {needs_handoff} for message: {message}"
        
        if expected_handoff:
            assert reason == expected_reason, \
                f"Expected reason='{expected_reason}' but got '{reason}' for message: {message}"
            assert contact_info is not None, \
                f"Expected contact info but got None for message: {message}"
            assert all(key in contact_info for key in ['name', 'phone', 'email']), \
                f"Missing required contact info fields for message: {message}"

    def test_direct_discrimination_responses(self, detector):
        """Test responses for direct discrimination scenarios."""
        test_cases = [
            {
                "message": "The landlord said they don't accept Section 8",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "Building management refuses to take my CityFHEPS voucher",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "Broker told me HASA vouchers are not allowed here",
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            }
        ]
        
        for case in test_cases:
            self.verify_handoff_response(
                detector,
                case["message"],
                case["context"],
                case["should_handoff"],
                case["expected_reason"]
            )

    def test_indirect_discrimination_responses(self, detector):
        """Test responses for indirect/subtle discrimination scenarios."""
        test_cases = [
            {
                "message": "Every time I mention my voucher, they say the unit was just rented",
                "context": {"voucher_type": "Section 8", "borough": "Queens"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "They stop responding to my calls after I mention CityFHEPS",
                "context": {"voucher_type": "CityFHEPS", "borough": "Staten Island"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "The agent said they're only looking for working professionals",
                "context": {"voucher_type": "HASA", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            }
        ]
        
        for case in test_cases:
            self.verify_handoff_response(
                detector,
                case["message"],
                case["context"],
                case["should_handoff"],
                case["expected_reason"]
            )

    def test_assistance_request_responses(self, detector):
        """Test responses for various assistance request scenarios."""
        test_cases = [
            {
                "message": "Can I speak with a housing specialist about my voucher?",
                "context": {"voucher_type": "Section 8", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "I need help understanding my rights as a voucher holder",
                "context": {"voucher_type": "CityFHEPS", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "How do I get in touch with a caseworker?",
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": True,
                "expected_reason": "user_request"
            }
        ]
        
        for case in test_cases:
            self.verify_handoff_response(
                detector,
                case["message"],
                case["context"],
                case["should_handoff"],
                case["expected_reason"]
            )

    def test_complex_request_responses(self, detector):
        """Test responses for complex/multi-part request scenarios."""
        test_cases = [
            {
                "message": "I need help filing a discrimination complaint and understanding my options",
                "context": {"voucher_type": "Section 8", "borough": "Manhattan"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            },
            {
                "message": "Can you help me understand my rights and connect me with a specialist?",
                "context": {"voucher_type": "CityFHEPS", "borough": "Brooklyn"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "I've been searching for weeks and need to speak with someone about my application",
                "context": {"voucher_type": "HASA", "borough": "Queens"},
                "should_handoff": True,
                "expected_reason": "user_request"
            }
        ]
        
        for case in test_cases:
            self.verify_handoff_response(
                detector,
                case["message"],
                case["context"],
                case["should_handoff"],
                case["expected_reason"]
            )

    def test_non_handoff_responses(self, detector):
        """Test responses for cases that should not trigger handoff."""
        test_cases = [
            {
                "message": "Can you help me find apartments in Brooklyn?",
                "context": {"voucher_type": "Section 8", "borough": "Brooklyn"},
                "should_handoff": False
            },
            {
                "message": "What's the rent for this apartment?",
                "context": {"voucher_type": "CityFHEPS", "borough": "Manhattan"},
                "should_handoff": False
            },
            {
                "message": "Are there any 2-bedroom units available?",
                "context": {"voucher_type": "HASA", "borough": "Queens"},
                "should_handoff": False
            },
            {
                "message": "Show me apartments near subway stations",
                "context": {"voucher_type": "Section 8", "borough": "Bronx"},
                "should_handoff": False
            }
        ]
        
        for case in test_cases:
            self.verify_handoff_response(
                detector,
                case["message"],
                case["context"],
                case["should_handoff"]
            )

    def test_edge_case_responses(self, detector):
        """Test responses for edge cases and boundary conditions."""
        test_cases = [
            {
                "message": "",  # Empty message
                "context": {"voucher_type": "Section 8", "borough": "Brooklyn"},
                "should_handoff": False
            },
            {
                "message": "I need help",  # Ambiguous request
                "context": {"voucher_type": "CityFHEPS", "borough": "Manhattan"},
                "should_handoff": False
            },
            {
                "message": "URGENT! Need to speak with someone immediately!!!",  # Emphatic request
                "context": {"voucher_type": "HASA", "borough": "Bronx"},
                "should_handoff": True,
                "expected_reason": "user_request"
            },
            {
                "message": "The landlord... you know... when I mentioned the voucher...",  # Implicit discrimination
                "context": {"voucher_type": "Section 8", "borough": "Queens"},
                "should_handoff": True,
                "expected_reason": "discrimination_case"
            }
        ]
        
        for case in test_cases:
            self.verify_handoff_response(
                detector,
                case["message"],
                case["context"],
                case["should_handoff"],
                case.get("expected_reason")
            )

    def test_message_formatting(self, detector):
        """Test that handoff messages are properly formatted."""
        message = "The landlord refused my voucher"
        context = {"voucher_type": "Section 8", "borough": "Manhattan"}
        
        needs_handoff, reason, contact_info = detector.detect_handoff(message, context)
        formatted_message = detector.format_handoff_message(reason, contact_info)
        
        # Verify message structure and content
        assert "**" in formatted_message, "Formatted message should contain bold text markers"
        assert "Phone:" in formatted_message, "Formatted message should contain contact phone"
        assert "Email:" in formatted_message, "Formatted message should contain contact email"
        assert "Address:" in formatted_message, "Formatted message should contain address"
        assert formatted_message.strip(), "Formatted message should not be empty"
        
        if reason == "discrimination_case":
            assert "discrimination" in formatted_message.lower(), \
                "Discrimination case message should mention discrimination"
            assert "NYC Commission on Human Rights" in formatted_message, \
                "Discrimination message should include Human Rights Commission contact"
        else:
            assert "caseworker" in formatted_message.lower(), \
                "User request message should mention caseworker" 