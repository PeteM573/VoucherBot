import unittest
from email_handler import enhanced_classify_message

class TestMessageClassification(unittest.TestCase):
    def setUp(self):
        """Set up test data before each test"""
        self.empty_state = {}
        self.state_with_listings = {
            "listings": [
                {
                    "address": "123 Test Ave, Bronx, NY 10457",
                    "price": "$2,000",
                    "url": "https://test.com/listing1",
                    "risk_level": "✅",
                    "building_violations": 0,
                    "title": "Nice Bronx Apartment"
                },
                {
                    "address": "456 Sample St, Brooklyn, NY 11201",
                    "price": "$2,500",
                    "url": "https://test.com/listing2",
                    "risk_level": "⚠️",
                    "building_violations": 2,
                    "title": "Cozy Brooklyn Spot"
                }
            ]
        }

    def test_email_requests(self):
        """Test various forms of email requests"""
        # Test email requests with listings
        self.assertEqual(
            enhanced_classify_message("can you write an email for listing #1", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("write an email to the landlord of listing 1", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("compose email for the first listing", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("email the owner of listing #2", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("contact listing 1", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("send a message to listing 2", self.state_with_listings),
            "email_request"
        )

        # Test contextual email requests (NEW)
        self.assertEqual(
            enhanced_classify_message("can you write an email for this one? My name is bob ross", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("write an email for this listing", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("compose email for this property", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("email the owner of this one", self.state_with_listings),
            "email_request"
        )
        self.assertEqual(
            enhanced_classify_message("contact this listing", self.state_with_listings),
            "email_request"
        )

        # Test that email requests without listing references don't work
        self.assertEqual(
            enhanced_classify_message("write to the landlord", self.state_with_listings),
            "general_conversation"
        )
        self.assertEqual(
            enhanced_classify_message("can you send an email", self.state_with_listings),
            "general_conversation"
        )

        # Test email requests without listings in state
        self.assertEqual(
            enhanced_classify_message("can you write an email for listing #1", self.empty_state),
            "general_conversation"
        )
        self.assertEqual(
            enhanced_classify_message("can you write an email for this one", self.empty_state),
            "general_conversation"
        )

    def test_search_requests(self):
        """Test various forms of search requests"""
        # Test explicit search patterns
        self.assertEqual(
            enhanced_classify_message("find me an apartment", self.empty_state),
            "new_search"
        )
        self.assertEqual(
            enhanced_classify_message("search for listings", self.empty_state),
            "new_search"
        )
        self.assertEqual(
            enhanced_classify_message("i'm looking for a place", self.empty_state),
            "new_search"
        )

        # Test location-based searches
        self.assertEqual(
            enhanced_classify_message("i have a section 8 voucher in the bronx", self.empty_state),
            "new_search"
        )
        self.assertEqual(
            enhanced_classify_message("looking for apartments in brooklyn", self.empty_state),
            "new_search"
        )
        self.assertEqual(
            enhanced_classify_message("need a 2 bedroom in manhattan", self.empty_state),
            "new_search"
        )

        # Test that general location questions don't trigger search
        self.assertEqual(
            enhanced_classify_message("can i use my voucher in brooklyn?", self.empty_state),
            "general_conversation"
        )
        self.assertEqual(
            enhanced_classify_message("do they accept section 8 in manhattan?", self.empty_state),
            "general_conversation"
        )

    def test_listing_requests(self):
        """Test various forms of listing requests"""
        # Test numeric requests
        self.assertEqual(
            enhanced_classify_message("1", self.state_with_listings),
            "listing_question"
        )
        self.assertEqual(
            enhanced_classify_message("show me #2", self.state_with_listings),
            "listing_question"
        )
        self.assertEqual(
            enhanced_classify_message("can i see listing 1", self.state_with_listings),
            "listing_question"
        )
        self.assertEqual(
            enhanced_classify_message("what about listing #2", self.state_with_listings),
            "listing_question"
        )

        # Test that listing requests require listings in state
        self.assertEqual(
            enhanced_classify_message("1", self.empty_state),
            "general_conversation"
        )
        self.assertEqual(
            enhanced_classify_message("show me listing 1", self.empty_state),
            "general_conversation"
        )

        # Test invalid listing numbers
        self.assertEqual(
            enhanced_classify_message("show me listing 0", self.state_with_listings),
            "listing_question"  # Still returns listing_question, validation happens later
        )
        self.assertEqual(
            enhanced_classify_message("can i see listing 999", self.state_with_listings),
            "listing_question"  # Still returns listing_question, validation happens later
        )

    def test_mixed_requests(self):
        """Test edge cases and mixed requests"""
        # Test that search takes priority over listing when no listings exist
        self.assertEqual(
            enhanced_classify_message("show me listing 1 in brooklyn", self.empty_state),
            "new_search"
        )

        # Test that listing request takes priority when listings exist
        self.assertEqual(
            enhanced_classify_message("show me listing 1 in brooklyn", self.state_with_listings),
            "listing_question"
        )

        # Test that general questions don't trigger listing or search
        self.assertEqual(
            enhanced_classify_message("how does section 8 work?", self.state_with_listings),
            "general_conversation"
        )
        self.assertEqual(
            enhanced_classify_message("what documents do i need?", self.state_with_listings),
            "general_conversation"
        )

if __name__ == '__main__':
    unittest.main() 