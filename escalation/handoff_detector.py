#!/usr/bin/env python3
"""
Human handoff detection module for VoucherBot.
Detects when a conversation should be escalated to a human caseworker.
"""

import re
from typing import Dict, Tuple, Optional
from .contact_directory import get_contact_info

class HandoffDetector:
    """Detects when a conversation should be escalated to a human."""
    
    def __init__(self):
        # User-driven trigger patterns
        self.user_request_patterns = [
            # Direct requests
            r"(?i)^.*?(can|could|may|how\s+do|how\s+can)\s+(i|we|you)?\s*(speak|talk|get|connect|reach|contact)\s*(to|with|through)?\s*(someone|anybody|a?\s*person|a?\s*caseworker|a?\s*specialist|a?\s*counselor|a?\s*agent|a?\s*housing\s*specialist)",
            r"(?i)^.*?(need|want|would\s*like|trying)\s*(to)?\s*(speak|talk|get|connect|reach|contact)\s*(to|with|through)?\s*(someone|anybody|a?\s*person|a?\s*caseworker|a?\s*specialist|a?\s*counselor|a?\s*agent|a?\s*housing\s*specialist)",
            r"(?i)^.*?(connect|put|get)\s*(me|us|in\s*touch|through)\s*(with|to)?\s*(someone|anybody|a?\s*person|a?\s*caseworker|a?\s*specialist|a?\s*counselor|a?\s*agent|a?\s*housing\s*specialist)",
            r"(?i)^.*?(is\s*there)?\s*(someone|anybody|a?\s*person|a?\s*caseworker|a?\s*specialist|a?\s*counselor|a?\s*agent|a?\s*housing\s*specialist)\s*(i|we|to)?\s*(can)?\s*(speak|talk|contact|meet)",
            r"(?i)^.*?(how|where|who)\s*(do|can|should)\s*(i|we)?\s*(get|speak|talk|contact|connect|reach|find|meet)",
            r"(?i)^.*?(need|want)\s*(help|assistance)\s*(with|understanding|about|regarding|for)\s*(my|the)?\s*(rights|options|voucher|application)",
            
            # Indirect requests
            r"(?i)^.*?(would|could)\s+it\s+be\s+possible\s+to\s+(speak|talk)\s+(to|with)\s+(someone|anybody|a\s+person|a\s+caseworker|a\s+specialist)",
            r"(?i)^.*?(need|want)\s+(help|assistance)\s+(understanding|with|about|regarding)",
            r"(?i)^.*?(having|got)\s+(trouble|problems|issues|difficulty)\s+with\s+(my|the)\s+(application|paperwork|forms)",
            r"(?i)^.*?(need|want)\s+to\s+(speak|talk)\s+to\s+someone\s+about\s+(my|the)\s+(application|paperwork|forms|voucher|options|rights)",
            
            # Rights and understanding
            r"(?i)^.*?(understand|know)\s+(my|the)\s+(rights|options)",
            r"(?i)^.*?what\s+(are|about)\s+(my|the)\s+(rights|options)",
            r"(?i)^.*?(need|want)\s+(help|assistance)\s+understanding\s+(my|the)\s+(rights|options)"
        ]
        
        # Case-based trigger patterns
        self.case_based_patterns = [
            # Direct discrimination
            r"(?i)^.*?(landlords?|owners?|brokers?|agents?|they|management|building)\s+(won't|will\s+not|refuses?|denied|denying|declined|declining|stopped|won't|wont)\s+(to\s+)?(take|accept|consider|allow|process|approve)\s+(my\s+)?(vouchers?|section\s*8|cityfheps|hasa|applications?)",
            r"(?i)^.*?(said|told|mentioned|implied)\s+(they|he|she|we)?\s*(don't|doesn't|do\s+not|does\s+not|won't|will\s+not)\s+(take|accept|allow|consider)\s+(vouchers?|section\s*8|cityfheps|hasa)",
            r"(?i)^.*?(no|not)\s+(accepting|taking|allowing)\s+(vouchers?|section\s*8|cityfheps|hasa)",
            r"(?i)^.*?broker\s+told\s+me\s+.*?(not|no)\s+(allowed|permitted|accepted)",
            r"(?i)^.*?management\s+company\s+refuses\s+.*?clients",
            
            # Indirect discrimination
            r"(?i)^.*?(every\s+time|whenever|after|when)\s+.*?(mention|say|tell|bring\s+up).*?(voucher|section\s*8|cityfheps|hasa).*?(no\s+longer|rented|taken|gone|unavailable|different)",
            r"(?i)^.*?(stop(ped)?|quit|cease|won't|don't)\s+(respond|answer|reply|call|contact|get\s+back)",
            r"(?i)^.*?(prefer|want|looking\s+for|only\s+accept)\s+(working|employed|professionals|people\s+with\s+jobs)",
            r"(?i)^.*?(suddenly|keeps?|always)\s+(unavailable|gone|taken|changed|different)",
            r"(?i)^.*?(unit|apartment|place)\s+(was|is|got)\s+(just|recently|suddenly)\s+(rented|taken|unavailable)",
            
            # Implicit/incomplete discrimination patterns
            r"(?i)^.*?landlord.*?(?:\.{3}|\.\.\.).*?(voucher|section\s*8|cityfheps|hasa)",
            r"(?i)^.*?(voucher|section\s*8|cityfheps|hasa).*?(?:\.{3}|\.\.\.).*?landlord",
            r"(?i)^.*?(?:\.{3}|\.\.\.).*?(mention|say|tell).*?(voucher|section\s*8|cityfheps|hasa).*?(?:\.{3}|\.\.\.)$",
            r"(?i)^.*?(when|after).*?(voucher|section\s*8|cityfheps|hasa).*?(?:\.{3}|\.\.\.)$",
            
            # HASA-specific discrimination
            r"(?i)^.*?(refuses?|won't|will\s+not|don't|do\s+not)\s+(accept|take|allow|consider)\s+hasa\s+(clients|recipients|vouchers?)",
            r"(?i)^.*?(discriminat\w+|bias\w*)\s+.*\s+hasa",
            
            # General discrimination indicators
            r"(?i)^.*?(discriminat\w+|bias\w*)\s+.*\s+(vouchers?|section\s*8|cityfheps|housing)",
            r"(?i)^.*?(illegal(ly)?|against\s+the\s+law)\s+.*\s+(reject\w*|refus\w*|deny\w*)\s+.*\s+(vouchers?|section\s*8|cityfheps|hasa)",
            r"(?i)^.*?(treated\s+differently|unfair\w*)\s+.*\s+because\s+of\s+(my\s+)?(vouchers?|section\s*8|cityfheps|hasa)"
        ]

    def detect_handoff(self, message: str, context: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Detect if a message should trigger human handoff.
        
        Args:
            message: The user's message
            context: Dict containing user context (voucher type, etc.)
            
        Returns:
            Tuple of:
            - bool: Whether handoff is needed
            - str: The reason for handoff (None if no handoff needed)
            - Dict: Contact information (None if no handoff needed)
        """
        # Normalize message
        message = message.strip()
        if not message:
            return False, None, None

        # First check for explicit discrimination complaints
        discrimination_complaint_keywords = [
            'discrimination complaint', 'file complaint', 'report discrimination',
            'housing discrimination', 'voucher discrimination', 'illegal discrimination',
            'file.*discrimination', 'report.*discrimination', 'complain.*discrimination',
            'complaint about discrimination', 'discrimination.*complaint'
        ]
        
        # Use regex for more flexible complaint matching
        complaint_patterns = [
            r"(?i)^.*?(file|report|make|submit|lodge)\s+.*?(complaint|report)\s+.*?(discrimination|unfair|illegal)",
            r"(?i)^.*?(complain|report)\s+.*?(discrimination|unfair treatment|illegal)",
            r"(?i)^.*?(help|assist).*?(file|report|make).*?(complaint|discrimination)"
        ]
        
        if (any(keyword in message.lower() for keyword in discrimination_complaint_keywords) or
            any(re.search(pattern, message) for pattern in complaint_patterns)):
            contact_info = get_contact_info(
                voucher_type=context.get('voucher_type'),
                borough=context.get('borough'),
                is_discrimination=True,
                use_borough_office=True
            )
            return True, "discrimination_case", contact_info

        # Then check for rights assistance requests
        rights_assistance = [
            'understand my rights', 'know my rights', 'understand my options',
            'know my options', 'what are my rights', 'what options do i have',
            'help understanding my rights', 'help with my rights',
            'explain my rights', 'learn about my rights'
        ]
        if any(keyword in message.lower() for keyword in rights_assistance):
            contact_info = get_contact_info(
                voucher_type=context.get('voucher_type'),
                borough=context.get('borough')
            )
            return True, "user_request", contact_info

        # Then check for direct assistance requests
        for pattern in self.user_request_patterns:
            if re.search(pattern, message):
                # Don't trigger on search-related help unless it's a clear request for human assistance
                if any(word in message.lower() for word in ['find', 'search', 'looking', 'show', 'list']):
                    # Only trigger if there's a clear request for human assistance
                    if any(phrase in message.lower() for phrase in [
                        'talk to', 'speak with', 'need someone', 'talk with', 'speak to',
                        'human', 'person', 'caseworker', 'agent', 'staff', 'specialist',
                        'having trouble', 'need help with', 'assistance with'
                    ]):
                        contact_info = get_contact_info(
                            voucher_type=context.get('voucher_type'),
                            borough=context.get('borough')
                        )
                        return True, "user_request", contact_info
                else:
                    contact_info = get_contact_info(
                        voucher_type=context.get('voucher_type'),
                        borough=context.get('borough')
                    )
                    return True, "user_request", contact_info

        # Then check for other discrimination indicators
        discrimination_keywords = [
            'discrimination', 'illegal', 'unfair', 'bias',
            'won\'t take', 'don\'t accept', 'refuse', 'denied',
            'no longer available when', 'stop responding when', 'prefer working professionals',
            'against the law', 'treated differently'
        ]
        if any(keyword in message.lower() for keyword in discrimination_keywords):
            contact_info = get_contact_info(
                voucher_type=context.get('voucher_type'),
                borough=context.get('borough'),
                is_discrimination=True,
                use_borough_office=True
            )
            return True, "discrimination_case", contact_info

        # Check case-based patterns
        for pattern in self.case_based_patterns:
            if re.search(pattern, message):
                contact_info = get_contact_info(
                    voucher_type=context.get('voucher_type'),
                    borough=context.get('borough'),
                    is_discrimination=True,
                    use_borough_office=True
                )
                return True, "discrimination_case", contact_info

        # Check for assistance-related keywords
        assistance_keywords = [
            'help with', 'assistance with', 'having trouble with', 'need help with',
            'having difficulty with', 'problems with', 'issues with', 'speak with',
            'talk to someone', 'contact someone', 'get in touch', 'caseworker',
            'specialist', 'advisor', 'counselor', 'need to speak', 'need to talk',
            'how do i get in touch', 'how can i speak', 'how can i talk',
            'housing specialist', 'need assistance with'
        ]
        
        if any(keyword in message.lower() for keyword in assistance_keywords):
            # Don't trigger on simple help requests without context
            if message.lower().strip() in ['help', 'i need help', 'need help']:
                return False, None, None
                
            # Don't trigger on search-related help unless it's a clear request for human assistance
            if any(word in message.lower() for word in ['find', 'search', 'looking', 'show', 'list']):
                if not any(phrase in message.lower() for phrase in [
                    'talk to', 'speak with', 'need someone', 'talk with', 'speak to',
                    'human', 'person', 'caseworker', 'agent', 'staff', 'specialist',
                    'having trouble', 'need help with', 'assistance with'
                ]):
                    return False, None, None
        
        return False, None, None

    def format_handoff_message(self, reason: str, contact_info: Dict) -> str:
        """Format the handoff message based on the trigger reason."""
        
        # Base message parts
        messages = {
            "user_request": """
I understand you'd like to speak with a human caseworker. I'm happy to connect you with the right person.

**{name}**
Phone: {phone}
Email: {email}
Address: {address}
Hours: {hours}

I'm still here if you need help drafting a message or have other questions about your housing search.
""",
            "discrimination_case": """
I notice you may be experiencing housing discrimination, which is illegal in NYC. You should speak with a housing specialist right away.

**{name}**
Phone: {phone}
Email: {email}
Address: {address}
Hours: {hours}

Additionally, you can report housing discrimination:
- NYC Commission on Human Rights: 212-416-0197
- NYS Division of Human Rights: 1-888-392-3644

I'm here if you need help documenting what happened or have other questions.
"""
        }
        
        # Format the appropriate message with contact info
        formatted_msg = messages[reason].format(**contact_info)
        
        # Ensure consistent line endings and spacing
        formatted_msg = formatted_msg.strip()
        
        return formatted_msg

def final_answer(response_text: str) -> Dict:
    """Format the final response for the UI."""
    return {
        "response": response_text,
        "metadata": {
            "requires_human_handoff": True,
            "handoff_type": "caseworker",
            "timestamp": None  # You can add timestamp if needed
        }
    } 