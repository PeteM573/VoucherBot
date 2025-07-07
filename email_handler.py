# Copy V0's EmailTemplateHandler class and related functions here
import re
import json
from typing import Dict, List, Tuple, Optional
import gradio as gr

class EmailTemplateHandler:
    """Enhanced email template handler with better detection and generation"""
    
    def __init__(self):
        self.email_patterns = [
            r"(?i)(email|write|compose|contact|message|reach out).{0,20}(landlord|owner|property manager)",
            r"(?i)(send|write|compose).{0,10}(email|message)",
            r"(?i)contact.{0,20}listing",
            r"(?i)(email|message).{0,20}listing\s*#?\d+",
            r"(?i)(compose|write).{0,20}(email|message).{0,20}(listing|property|apartment)",
            r"(?i)write to.{0,20}(landlord|owner)",
            r"(?i)(write|compose|email).{0,20}(this|the).{0,10}(listing|property|apartment)"
        ]
        
        self.listing_reference_patterns = [
            r"listing\s*#?(\d+)",
            r"property\s*#?(\d+)",
            r"apartment\s*#?(\d+)",
            r"the\s*(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s*(listing|property|apartment)",
            r"this\s*(listing|property|apartment)",
            r"the\s*(listing|property|apartment)"
        ]
        
        self.name_patterns = [
            r"my name is ([^.,!?\n]+?)(?:\s+and|\.|\?|!|$)",
            r"i'm ([^.,!?\n]+?)(?:\s+and|\.|\?|!|$)",
            r"i am ([^.,!?\n]+?)(?:\s+and|\.|\?|!|$)",
            r"call me ([^.,!?\n]+?)(?:\s+and|\.|\?|!|$)"
        ]
        
        self.voucher_patterns = {
            "section 8": r"(?i)section\s*8|section-8",
            "cityfheps": r"(?i)cityfheps|city\s*fheps|fheps",
            "hasa": r"(?i)hasa",
            "dss": r"(?i)dss",
            "voucher": r"(?i)voucher"
        }

    def detect_email_request(self, message: str) -> bool:
        """Enhanced email request detection using multiple patterns"""
        message_lower = message.lower()
        
        # Check for email intent patterns
        has_email_intent = any(
            re.search(pattern, message) for pattern in self.email_patterns
        )
        
        # Check for listing reference
        has_listing_ref = any(
            re.search(pattern, message_lower) for pattern in self.listing_reference_patterns
        )
        
        return has_email_intent and has_listing_ref

    def extract_listing_number(self, message: str) -> Optional[int]:
        """Extract listing number from message with multiple pattern support"""
        message_lower = message.lower()
        
        # Try direct number patterns first
        for pattern in [r"listing\s*#?(\d+)", r"property\s*#?(\d+)", r"apartment\s*#?(\d+)"]:
            match = re.search(pattern, message_lower)
            if match:
                return int(match.group(1))
        
        # Try ordinal patterns
        ordinal_map = {
            "first": 1, "1st": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4,
            "fifth": 5, "5th": 5
        }
        
        ordinal_pattern = r"the\s*(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s*(?:listing|property|apartment)"
        match = re.search(ordinal_pattern, message_lower)
        if match:
            return ordinal_map.get(match.group(1))
        
        return None

    def extract_user_info(self, message: str) -> Dict[str, str]:
        """Extract user information from message"""
        user_info = {}
        
        # Extract name
        for pattern in self.name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                user_info["name"] = match.group(1).strip().title()
                break
        
        # Extract voucher type
        for voucher_type, pattern in self.voucher_patterns.items():
            if re.search(pattern, message):
                user_info["voucher_type"] = voucher_type
                break
        
        # Extract voucher amount (looking for $XXXX patterns)
        amount_match = re.search(r"\$(\d{3,4})", message)
        if amount_match:
            user_info["voucher_amount"] = amount_match.group(1)
        
        return user_info

    def generate_email_template(self, listing: Dict, user_info: Dict, state: Dict) -> str:
        """Generate comprehensive email template"""
        
        # Default values
        user_name = user_info.get("name", "Prospective Tenant")
        voucher_type = user_info.get("voucher_type", "housing voucher")
        voucher_amount = user_info.get("voucher_amount", "approved amount")
        
        # Format voucher amount with dollar sign if it's a number
        if voucher_amount and voucher_amount.isdigit():
            formatted_amount = f"${voucher_amount}"
        else:
            formatted_amount = voucher_amount
        
        # Extract listing details
        address = listing.get("title", "your property")
        rent = listing.get("price", "listed price")
        bedrooms = listing.get("housing_info", "")
        
        # Clean up rent format
        if rent and rent != "N/A":
            rent = rent.replace("$", "").replace(",", "")
            try:
                rent_num = int(re.search(r"\d+", rent).group())
                rent = f"${rent_num:,}"
            except:
                pass
        
        # Generate email content
        email_template = f"""Subject: Inquiry About Your Rental Property - {voucher_type.title()} Voucher Holder

Dear Property Manager/Landlord,

I hope this message finds you well. My name is {user_name}, and I am writing to express my sincere interest in your rental property listed at: {address}.

I am a qualified {voucher_type.title()} voucher holder with an approved rental amount of {formatted_amount}. I noticed that your listing welcomes voucher holders, which is why I am reaching out to you directly.

**About Me:**
• Reliable tenant with {voucher_type.title()} voucher
• All required documentation ready for review
• Excellent rental history and references available
• Looking for immediate occupancy

**Property Details I'm Interested In:**
• Address: {address}
• Listed Rent: {rent}
• Unit Details: {bedrooms}

**What I Can Provide:**
✓ Valid {voucher_type.title()} voucher letter
✓ Income verification documents  
✓ Background check authorization
✓ Previous landlord references
✓ Security deposit (if required)

I understand the voucher process and can work with you to ensure all paperwork is completed efficiently. The housing authority inspection can typically be scheduled within 1-2 weeks of lease signing.

I am available for a viewing at your convenience and can move forward quickly with the application process. Please let me know if you have any questions about the voucher program or if you'd like to schedule a time to discuss this opportunity.

Thank you for your time and consideration. I look forward to hearing from you soon.

Best regards,
{user_name}

---
*This email was generated to help you contact the landlord about this voucher-friendly listing.*"""

        return email_template


def enhanced_classify_message(message: str, state: Dict) -> str:
    """Enhanced message classification with what-if scenario detection using V2 router"""
    email_handler = EmailTemplateHandler()
    
    if email_handler.detect_email_request(message):
        return "email_request"
    
    message_lower = message.lower()
    
    # Check for shortlist commands FIRST (high priority)
    shortlist_patterns = [
        "save listing", "add to shortlist", "shortlist", "save to shortlist",
        "remove from shortlist", "delete from shortlist", "unsave",
        "show shortlist", "view shortlist", "my shortlist", "show my shortlist",
        "clear shortlist", "empty shortlist", "delete shortlist",
        "priority", "set priority", "add note", "add comment"
    ]
    
    if any(pattern in message_lower for pattern in shortlist_patterns):
        return "shortlist_command"
    
    # Check for new search requests FIRST (before listing questions to avoid conflicts)
    new_search_patterns = [
        "find me", "search for", "look for", "i want", 
        "show me apartments", "find apartments", "search apartments",
        "new search", "different search", "another search"
    ]
    
    # More specific "I need" patterns that are housing-related
    housing_need_patterns = [
        "i need an apartment", "i need a place", "i need housing",
        "i need to find", "i need apartments"
    ]
    
    # Location change patterns - KEY FIX for your issue
    location_change_patterns = [
        "how about in", "what about in", "try in", "look in", 
        "search in", "find in", "check in", "instead in",
        # Also handle variations without "in"
        "how about", "what about", "try", "instead"
    ]
    
    # "Can I see" patterns for housing searches
    can_i_see_patterns = [
        "can i see", "could i see", "show me", "let me see"
    ]
    
    # Also check for explicit borough mentions or housing program mentions
    borough_mentions = ["bronx", "brooklyn", "manhattan", "queens", "staten island"]
    program_mentions = ["section 8", "cityfheps", "hasa", "voucher", "housing", "apartment", "housing"]
    
    # Enhanced new search detection - BUT EXCLUDE listing requests
    listing_request_phrases = [
        "listing 1", "listing 2", "listing 3", "listing 4", "listing 5", 
        "listing 6", "listing 7", "listing 8", "listing 9", "listing 10",
        "see listing", "show listing", "want to see listing"
    ]
    
    # Don't treat as new search if it's clearly a listing request
    is_listing_request = any(phrase in message_lower for phrase in listing_request_phrases)
    
    is_new_search = (
        not is_listing_request and (
            any(pattern in message_lower for pattern in new_search_patterns) or
            any(pattern in message_lower for pattern in housing_need_patterns) or
            (any(program in message_lower for program in program_mentions) and 
             any(borough in message_lower for borough in borough_mentions)) or
            ("apartment" in message_lower and any(word in message_lower for word in ["find", "search", "want"])) or
            # Key fix: "show me" + program/housing terms = new search
            ("show me" in message_lower and any(program in message_lower for program in program_mentions)) or
            ("show me" in message_lower and "apartment" in message_lower) or
            # CRITICAL FIX: Location change requests like "how about in Brooklyn?" (without requiring housing keywords)
            (any(pattern in message_lower for pattern in location_change_patterns) and 
             any(borough in message_lower for borough in borough_mentions)) or
            # Also catch "Can I see section 8 housing in [borough]?"
            (any(pattern in message_lower for pattern in can_i_see_patterns) and 
             any(program in message_lower for program in program_mentions) and
             any(borough in message_lower for borough in borough_mentions)) or
            # Also catch "Can I see housing in [borough]?" without "section 8"
            (any(pattern in message_lower for pattern in can_i_see_patterns) and 
             "housing" in message_lower and
             any(borough in message_lower for borough in borough_mentions))
        )
    )
    
    if is_new_search:
        return "new_search"
    
    # SECOND: Check for listing questions (after new search to avoid conflicts)
    has_listings = len(state.get("listings", [])) > 0
    listing_question_patterns = [
        "link to", "url for", "give me", "can i have", 
        "first listing", "second listing", "third listing", "fourth listing", "fifth listing", "last listing",
        "1st listing", "2nd listing", "3rd listing", "4th listing", "5th listing",
        "listing #", "listing number", "details for", "more info",
        "tell me about", "let me see listing", "can i see listing", "show me listing",
        "see listing", "listing 1", "listing 2", "listing 3", "listing 4", "listing 5",
        "listing 6", "listing 7", "listing 8", "listing 9", "listing 10",
        "5th listing", "6th listing", "7th listing", "8th listing", "9th listing", "10th listing",
        "i want to see listing", "want to see listing", "see the", "view listing"
        # Removed "what about" to avoid conflicts with "what about in Brooklyn?"
    ]
    
    # If they're asking about listings but we have no listings, it's general conversation
    if not has_listings and any(pattern in message_lower for pattern in listing_question_patterns):
        return "general_conversation"
    
    if has_listings and any(pattern in message_lower for pattern in listing_question_patterns):
        return "listing_question"
    
    # THIRD: Try LLM Fallback Router for accurate intent classification
    llm_intent = None
    llm_confidence = 0.0
    try:
        from llm_fallback_router import LLMFallbackRouter
        import json
        
        # Create a simple mock LLM client for testing
        class SimpleLLMClient:
            def generate(self, prompt):
                # Simple rule-based classification for demo
                message_lower = message.lower()
                
                # Check for specific listing requests first (highest priority if listings exist)
                if state.get("listings") and any(phrase in message_lower for phrase in ["listing 1", "listing 2", "listing 3", "listing 4", "listing 5", "listing 6", "listing 7", "listing 8", "listing 9", "listing 10", "see listing", "show listing", "let me see listing", "want to see listing", "i want to see listing"]):
                    return '{"intent": "LISTING_QUESTION", "confidence": 0.95, "parameters": {}, "reasoning": "User wants to see specific listing details"}'
                # Check for location change patterns first (most specific)
                elif any(phrase in message_lower for phrase in ["how about in", "what about in", "try in", "instead in"]):
                    return '{"intent": "SEARCH_LISTINGS", "confidence": 0.90, "parameters": {}, "reasoning": "User wants to change search location"}'
                # Check for "can i see" + housing terms
                elif "can i see" in message_lower and any(word in message_lower for word in ["section 8", "housing", "apartment"]):
                    return '{"intent": "SEARCH_LISTINGS", "confidence": 0.85, "parameters": {}, "reasoning": "User wants to see housing listings"}'
                # Check for help/how-to patterns (more specific)
                elif any(phrase in message_lower for phrase in ["how do i", "how to", "how can i", "help me", "assist", "support"]):
                    return '{"intent": "HELP_REQUEST", "confidence": 0.80, "parameters": {}, "reasoning": "User needs assistance"}'
                # General search patterns
                elif any(word in message_lower for word in ["find", "search", "look", "apartment", "housing"]) and "how" not in message_lower:
                    return '{"intent": "SEARCH_LISTINGS", "confidence": 0.85, "parameters": {}, "reasoning": "User wants to find housing"}'
                else:
                    return '{"intent": "UNKNOWN", "confidence": 0.60, "parameters": {}, "reasoning": "Unclear intent"}'
        
        # Create fallback router with mock client
        llm_fallback = LLMFallbackRouter(SimpleLLMClient(), debug=True)
        
        # Get the raw LLM response first to extract confidence
        raw_llm_response = llm_fallback.llm_client.generate(llm_fallback.format_prompt(message, state))
        
        # Extract confidence from raw response
        try:
            raw_data = json.loads(raw_llm_response)
            llm_confidence = raw_data.get("confidence", 0.0)
        except:
            llm_confidence = 0.0
        
        # Route the message to get intent and other data
        result = llm_fallback.route(message, state)
        
        # Get intent from result
        llm_intent = result.get("intent", "UNKNOWN")
            
    except Exception as e:
        print(f"⚠️ LLM Fallback Router failed: {e}")
    
    # Map LLM intents to our app's message types
    intent_mapping = {
        "SEARCH_LISTINGS": "new_search",
        "CHECK_VIOLATIONS": "violation_check", 
        "ASK_VOUCHER_SUPPORT": "voucher_info",
        "REFINE_SEARCH": "what_if_scenario",
        "FOLLOW_UP": "general_conversation",
        "HELP_REQUEST": "general_conversation",
        "LISTING_QUESTION": "listing_question",
        "UNKNOWN": "general_conversation"
    }
    
    # Only use LLM result if we got one and confidence is reasonable
    if llm_intent and llm_confidence >= 0.6:
        mapped_intent = intent_mapping.get(llm_intent, "general_conversation")
        print(f"🧠 LLM Fallback Router: {message[:50]}... → {llm_intent} ({llm_confidence:.2f}) → {mapped_intent}")
        return mapped_intent
    else:
        print(f"🚫 LLM Router bypassed: intent={llm_intent}, confidence={llm_confidence}")
    
    # FOURTH: Use V2 router only if LLM router didn't provide confident result
    try:
        from enhanced_semantic_router_v2 import EnhancedSemanticRouterV2, Intent
        router = EnhancedSemanticRouterV2()
        intent = router.classify_intent(message, state)
        
        print(f"🔧 V2 Router result: {intent}")
        if intent == Intent.WHAT_IF:
            return "what_if_scenario"
    except ImportError:
        # Fallback to what_if_handler if V2 not available
        try:
            from what_if_handler import detect_what_if_message
            if detect_what_if_message(message, state):
                return "what_if_scenario"
        except ImportError:
            pass  # what_if_handler not available
    
    return "general_conversation"


def enhanced_handle_email_request(message: str, history: List, state: Dict) -> Tuple[List, gr.update]:
    """Enhanced email request handler with better error handling and validation"""
    email_handler = EmailTemplateHandler()
    
    try:
        # Extract listing number
        listing_num = email_handler.extract_listing_number(message)
        if listing_num is None:
            history.append({
                "role": "assistant",
                "content": "I couldn't determine which listing you want to email about. Please specify the listing number (e.g., 'email listing #1' or 'contact the first listing')."
            })
            return history, gr.update(visible=False)
        
        # Validate listing exists
        listings = state.get("listings", [])
        if not listings:
            history.append({
                "role": "assistant", 
                "content": "I don't have any current listings to reference. Please search for apartments first, then I can help you generate an email template."
            })
            return history, gr.update(visible=False)
        
        if listing_num > len(listings):
            history.append({
                "role": "assistant",
                "content": f"I only found {len(listings)} listings in our search. Please choose a number between 1 and {len(listings)}."
            })
            return history, gr.update(visible=False)
        
        # Get the listing (convert to 0-based index)
        listing = listings[listing_num - 1]
        
        # Extract user information
        user_info = email_handler.extract_user_info(message)
        
        # Generate email template
        email_content = email_handler.generate_email_template(listing, user_info, state)
        
        # Format response
        response = f"""### 📧 Email Template for Listing #{listing_num}

{email_content}

---
**Next Steps:**
1. Copy the email template above
2. Send it to the landlord's contact information
3. Follow up within 2-3 business days if you don't hear back

*Tip: Make sure to attach any required documents mentioned in the email when you send it.*"""
        
        history.append({
            "role": "assistant",
            "content": response
        })
        
        return history, gr.update(visible=False)
        
    except Exception as e:
        error_msg = f"I apologize, but I encountered an error generating the email template: {str(e)}. Please try rephrasing your request or contact support if the issue persists."
        history.append({"role": "assistant", "content": error_msg})
        return history, gr.update(visible=False)


# Test cases for the enhanced email functionality
def test_enhanced_email_functionality():
    """Test cases for the enhanced email handling"""
    
    test_cases = [
        {
            "message": "Can you write an email for listing #1? My name is John Smith and I have a Section 8 voucher for $2000",
            "expected_detection": True,
            "expected_listing": 1,
            "expected_name": "John Smith",
            "expected_voucher": "section 8"
        },
        {
            "message": "I want to contact the landlord of the first listing",
            "expected_detection": True,
            "expected_listing": 1,
            "expected_name": None,
            "expected_voucher": None
        },
        {
            "message": "Please help me reach out to the owner of property #3. I'm Maria and have CityFHEPS",
            "expected_detection": True,
            "expected_listing": 3,
            "expected_name": "Maria",
            "expected_voucher": "cityfheps"
        },
        {
            "message": "Tell me more about the second apartment",
            "expected_detection": False,
            "expected_listing": None,
            "expected_name": None,
            "expected_voucher": None
        }
    ]
    
    email_handler = EmailTemplateHandler()
    
    print("🧪 Testing Enhanced Email Functionality\n")
    
    for i, test in enumerate(test_cases, 1):
        message = test["message"]
        
        # Test detection
        detected = email_handler.detect_email_request(message)
        listing_num = email_handler.extract_listing_number(message)
        user_info = email_handler.extract_user_info(message)
        
        print(f"Test {i}: {'✅' if detected == test['expected_detection'] else '❌'}")
        print(f"  Message: {message}")
        print(f"  Email Detected: {detected} (expected: {test['expected_detection']})")
        print(f"  Listing Number: {listing_num} (expected: {test['expected_listing']})")
        print(f"  User Name: {user_info.get('name')} (expected: {test['expected_name']})")
        print(f"  Voucher Type: {user_info.get('voucher_type')} (expected: {test['expected_voucher']})")
        print()

if __name__ == "__main__":
    test_enhanced_email_functionality() 