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
            r"(?i)(send|write|compose)\s+(an?\s+)?(email|message)\s+(to|for|about)",
            r"(?i)(send|write|compose)\s+(an?\s+)?(email|message)",  # More flexible - no requirement for to/for/about
            r"(?i)contact.{0,20}listing",
            r"(?i)(email|message).{0,20}listing\s*#?\d+",
            r"(?i)(compose|write).{0,20}(email|message).{0,20}(listing|property|apartment)",
            r"(?i)write to.{0,20}(landlord|owner)",
            r"(?i)(write|compose|email).{0,20}(this|the).{0,10}(listing|property|apartment)",
            r"(?i)(write|compose|draft|create)\s+(an?\s+)?(email|message)",  # Additional flexible patterns
            r"(?i)(email|message)\s+(me|for me|to me)"  # Direct email requests
        ]
        
        self.listing_reference_patterns = [
            r"listing\s*#?(\d+)",
            r"property\s*#?(\d+)",
            r"apartment\s*#?(\d+)",
            r"the\s*(first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\s*(listing|property|apartment)",
            r"this\s*(listing|property|apartment|one)",
            r"the\s*(listing|property|apartment)",
            r"that\s*(listing|property|apartment|one)",
            r"this\s*one",
            r"that\s*one",
            r"the\s*one",
            r"current\s*(listing|property|apartment)",
            r"above\s*(listing|property|apartment)"
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

    def detect_email_request(self, message: str, state: Dict = None) -> bool:
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
        
        # If we have listings available, be more flexible with email detection
        if state and state.get("listings"):
            # Allow general email requests to landlord/owner when listings are available
            general_email_patterns = [
                r"(?i)(compose|write|draft|create)\s+(email|message)",
                r"(?i)(email|message|contact)\s+(landlord|owner|property manager)",
                r"(?i)(inquiry|contact)\s+(about|for)\s+(apartment|property|listing)",
                r"(?i)(email|contact)\s+the\s+(property owner|landlord)",
                r"(?i)(write|send)\s+(inquiry|email)",
                r"(?i)(create|generate)\s+(email template)",
                r"(?i)(write|compose|draft)\s+(me\s+)?(an?\s+)?(email|message)",  # "write me an email"
                r"(?i)(email|message)\s+(me|for me|to me)",  # "email me"
                r"(?i)(write|compose)\s+(an?\s+)?(email|message)\s+(my name is|i'm|i am)",  # "write an email my name is"
                r"(?i)(write|compose)\s+(an?\s+)?(email|message)\s+(for|to)\s+(me|bob|john|jane)"  # "write an email for bob"
            ]
            
            has_general_email_intent = any(
                re.search(pattern, message) for pattern in general_email_patterns
            )
            
            return has_email_intent or has_general_email_intent
        
        return has_email_intent and has_listing_ref

    def extract_listing_number(self, message: str, state: Dict = None) -> Optional[int]:
        """Extract listing number from message with multiple pattern support"""
        message_lower = message.lower()
        
        # Check for contextual references first if we have state
        if state:
            contextual_patterns = [
                r"this\s*(listing|property|apartment|one)",
                r"that\s*(listing|property|apartment|one)",
                r"this\s*one",
                r"that\s*one",
                r"the\s*one",
                r"current\s*(listing|property|apartment)",
                r"above\s*(listing|property|apartment)"
            ]
            
            if any(re.search(pattern, message_lower) for pattern in contextual_patterns):
                # Use current listing if available
                current_listing_index = state.get("current_listing_index")
                if current_listing_index is not None:
                    return current_listing_index + 1  # Convert to 1-based
                # If no current listing, default to listing 1
                listings = state.get("listings", [])
                if listings:
                    return 1
        
        # Try direct number patterns
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
    """Enhanced message classification with comprehensive voucher question handling"""
    email_handler = EmailTemplateHandler()
    
    # Check for email requests only if we have listings
    if state.get("listings") and email_handler.detect_email_request(message, state):
        return "email_request"
    
    message_lower = message.lower().strip()  # Add strip() to handle whitespace
    
    # Search trigger patterns (highest priority for explicit search requests)
    search_patterns = [
        # English patterns
        "find me", "search for", "show me listings", "look for",
        "i need a", "i need an", "i'm looking for", "im looking for",
        "find a", "find an", "search apartments", "looking for",
        
        # Spanish patterns
        "busco", "estoy buscando", "quiero", "necesito",
        "buscar", "encontrar", "mostrar", "ver",
        "tengo un vale", "tienes un vale", "con mi voucher",
        "busco vivienda", "busco apartamento", "busco departamento",
        "estoy buscando vivienda", "estoy buscando apartamento",
        "quiero vivienda", "quiero apartamento", "necesito vivienda",
        "necesito apartamento", "buscar vivienda", "buscar apartamento"
    ]
    
    # Location patterns that should NOT trigger search
    general_location_patterns = [
        "can i use this in", "does it work in", "accepted in",
        "landlords in", "take vouchers in", "can i use my voucher in",
        "does my voucher work in", "is my voucher accepted in",
        "do they accept vouchers in", "are there landlords that accept",
        "do they accept section 8 in", "accept section 8 in",
        "take section 8 in", "is section 8 accepted in"
    ]
    
    # Check if it's a general location question (not a search)
    if any(pattern in message_lower for pattern in general_location_patterns):
        return "general_conversation"
    
    # Check if it's an explicit search request
    if any(pattern in message_lower for pattern in search_patterns):
        # Make sure it's not just asking about voucher acceptance
        if not any(pattern in message_lower for pattern in ["how do i", "where can i", "what do i"]):
            return "new_search"
            
    # Check if it might be a location-based search
    has_location = any(borough in message_lower for borough in [
        "bronx", "brooklyn", "manhattan", "queens", "staten island",
        "el bronx", "en bronx", "en brooklyn", "en manhattan", "en queens", "en staten island"
    ])
    has_housing_terms = any(term in message_lower for term in [
        "bedroom", "apt", "apartment", "housing", "place", "listings", "listing",
        "vivienda", "apartamento", "departamento", "casa", "habitación", "habitacion"
    ])
    has_voucher_terms = any(term in message_lower for term in [
        "section 8", "section-8", "voucher", "cityfheps", "hasa", "dss", "fheps",
        "sección 8", "seccion 8", "vale", "vales", "voucher", "vouchers"
    ])
    
    # Check for listing questions first if we have listings
    if state.get("listings"):
        # First check for bare numbers (just a number by itself)
        if message_lower.replace(" ", "").isdigit():
            number = int(message_lower)
            if 1 <= number <= 10:  # Only accept reasonable listing numbers
                return "listing_question"
        
        # Then check for numbers with context, but exclude "section 8" patterns
        numbers = re.findall(r'\b\d+\b', message_lower)
        has_number = bool(numbers and 1 <= int(numbers[0]) <= 10)
        
        # Special case: ignore numbers in "section 8" context for listing questions
        if "section 8" in message_lower or "section-8" in message_lower:
            has_number = False
        
        # Also check for listing-specific words
        listing_question_patterns = [
            "show listing", "tell me about listing", "what about listing",
            "can i see listing", "show me listing", "details for listing",
            "more info about listing", "information about listing",
            "tell me more about listing", "what's listing", "whats listing",
            "listing #", "listing number", "listing no", "listing details",
            "can i see #", "show me #", "what about #", "tell me about #",
            "show #", "see #", "view #", "look at #",
            # Add ordinal patterns
            "first listing", "second listing", "third listing", "last listing",
            "1st listing", "2nd listing", "3rd listing",
            "the first", "the second", "the third", "the last",
            "see the first", "see the second", "see the third", "see the last",
            "show the first", "show the second", "show the third", "show the last",
            "view the first", "view the second", "view the third", "view the last"
        ]
        
        # Only match if:
        # 1. Has a number AND some listing context, OR
        # 2. Matches a listing pattern
        # 3. Not asking a general question about listings
        if (has_number and any(word in message_lower for word in ["listing", "show", "see", "view", "about", "#"])) or \
           any(pattern in message_lower for pattern in listing_question_patterns):
            # Make sure it's not a general question about listings (but allow "tell me about listing #X")
            if not any(pattern in message_lower for pattern in [
                "how do", "what is", "what are", "where can", "where do",
                "when can", "why do", "explain", "tell me about the process"
            ]):
                return "listing_question"
    
    # Now check for location-based search
    # Only trigger if:
    # 1. Has location AND (housing terms OR voucher terms)
    # 2. Not asking about acceptance/availability
    if has_location and (has_housing_terms or has_voucher_terms):
        # Make sure it's not just asking about acceptance
        if not any(word in message_lower for word in ["accept", "take", "allowed", "available"]):
            return "new_search"
    
    # Voucher information and help patterns
    voucher_info_patterns = [
        # How-to Questions
        "how do i", "how can i", "what do i do", "what's the process",
        "what happens if", "how to use", "how does", "what should i",
        
        # Information/Understanding Questions
        "what's the difference", "what does", "can i", "does my voucher",
        "am i eligible", "do i have to", "is it possible",
        
        # Status/Timeline Questions
        "when do i", "how long does", "why haven't i", "what's the status",
        "when will", "how much time", "deadline", "extension",
        
        # Documentation/Process Questions
        "what documents", "what paperwork", "forms", "application",
        "inspection", "requirements", "recertification",
        
        # Rights/Rules Questions
        "can a landlord", "is it legal", "discrimination", "rights",
        "allowed to", "required to",
        
        # Program Understanding
        "difference between", "vs", "versus", "compared to",
        "what is cityfheps", "what is section 8", "what is hasa",
        
        # Specific Voucher Questions
        "maximum rent", "rent limit", "utilities", "bedrooms",
        "expire", "transfer", "move with", "portability"
    ]
    
    # Check if it's a voucher question
    if any(pattern in message_lower for pattern in voucher_info_patterns):
        return "general_conversation"
    
    # Documentation/help patterns
    documentation_patterns = [
        "where can i find", "how do i find", "where do i find",
        "how can i find", "where is", "how do i",
        "how can i", "can you explain", "what does",
        "explain", "help me understand",
        "documentation", "guide", "tutorial", "instructions",
        "where should i look", "where would i find"
    ]
    
    # Check for documentation patterns
    if any(pattern in message_lower for pattern in documentation_patterns):
        return "general_conversation"
    
    # Check for general "tell me about" (voucher/program info)
    if "tell me about" in message_lower:
        # If it's about voucher programs/general info, it's general conversation
        if any(word in message_lower for word in ["voucher", "section 8", "cityfheps", "hasa", "program", "process"]):
            return "general_conversation"
    
    # Check for shortlist commands
    shortlist_patterns = [
        "save listing", "add to shortlist", "shortlist", "save to shortlist",
        "remove from shortlist", "delete from shortlist", "unsave",
        "show shortlist", "view shortlist", "my shortlist", "show my shortlist",
        "clear shortlist", "empty shortlist", "delete shortlist",
        "priority", "set priority", "add note", "add comment"
    ]
    
    if any(pattern in message_lower for pattern in shortlist_patterns):
        return "shortlist_command"
    
    return "general_conversation"


def enhanced_handle_email_request(message: str, history: List, state: Dict) -> Tuple[List, gr.update]:
    """Enhanced email request handler with better error handling and validation"""
    email_handler = EmailTemplateHandler()
    
    try:
        # Extract listing number
        listing_num = email_handler.extract_listing_number(message, state)
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