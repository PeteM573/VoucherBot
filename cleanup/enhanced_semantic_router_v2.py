#!/usr/bin/env python3
"""
Enhanced Semantic Router V2 - Comprehensive Pattern Matching

This version addresses the gaps revealed by comprehensive testing,
including better handling of:
- More diverse what-if trigger patterns
- Expanded borough extraction patterns  
- Better bedroom expression handling
- Improved rent/budget pattern matching
- Enhanced voucher type detection
- Better handling of informal language
"""

import re
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

class Intent(Enum):
    SEARCH_LISTINGS = "search_listings"
    CHECK_VIOLATIONS = "check_violations"
    VOUCHER_INFO = "voucher_info"
    SHOW_HELP = "show_help"
    WHAT_IF = "what_if"
    PARAMETER_REFINEMENT = "parameter_refinement"
    UNCLASSIFIED = "unclassified"

@dataclass
class PatternGroup:
    """Group of patterns with priority for intent classification"""
    patterns: List[str]
    priority: int = 1
    case_insensitive: bool = True

class EnhancedSemanticRouterV2:
    """Enhanced semantic router with comprehensive pattern matching"""
    
    def __init__(self):
        self.intent_patterns = self._build_intent_patterns()
        self.parameter_patterns = self._build_parameter_patterns()
        
    def _build_intent_patterns(self) -> Dict[Intent, PatternGroup]:
        """Build comprehensive intent classification patterns"""
        return {
            Intent.WHAT_IF: PatternGroup([
                # Core what-if patterns
                r'\b(?:what if|how about|what about)\b',
                r'\b(?:try|check|look)\b',
                r'\b(?:search|find|show)\s+(?:in|around|near)\b',
                r'\b(?:look|search)\s+(?:in|around|near|for)\b',
                r'\b(?:can you|could you|would you|should i)\s+(?:try|check|look|search)\b',
                r'\bmaybe\s+(?:try|check|look)\b',
                r'\b(?:let\'s|lets)\s+(?:try|check|look)\b',
                r'\b(?:actually|wait|hmm),?\s+(?:try|check|look|how about|what about)\b',
                r'\binstead\b',
                r'\b(?:please|por favor)\s+(?:try|check|look|search)\b',
                r'\b(?:i\'d like to|i want to)\s+(?:try|check|look|see)\b',
                
                # Informal variations
                r'\b(?:yo|tho|though)\b',
                r'\b(?:bout|about)\b',
                r'\bw/\b',  # "with" abbreviation
                r'@',       # "at" symbol
                
                # More specific question patterns (avoid overly broad matching)
                r'\b(?:what about|how about|what happens if)\b.*\?\s*$',
                r'\b(?:would|could|should|might)\b.*\?\s*$',
                
                # Borough + context patterns (removed overly broad borough pattern)
                # r'\b(?:manhattan|brooklyn|queens|bronx|staten island|bk|si|bx|mnh|qns)\b',  # Too aggressive - matches any borough mention
                r'\b(?:the city|downtown|uptown)\b',
                
                # Bedroom patterns in what-if context
                r'\b\d+\s*(?:br|bed|bedroom|bedrooms?)\b',
                r'\b(?:studio|one|two|three|four|five)\s+(?:bed|bedroom)\b',
                
                # Budget patterns in what-if context
                r'\$\d+',
                r'\b(?:under|max|budget|around|about)\s+\$?\d+\b',
                
                # Voucher patterns in what-if context
                r'\b(?:section\s*8|hasa|cityfheps|housing\s+voucher)\b',
            ], priority=2),
            
            Intent.PARAMETER_REFINEMENT: PatternGroup([
                r'\b(?:under|max|maximum|up to)\s+\$?\d+',
                r'\$\d+(?:\.\d{2})?(?:\s*max|\s*maximum|\s*or\s+less)?$',
                r'\bbudget\s+(?:of\s+)?\$?\d+',
                r'\b(?:less than|no more than)\s+\$?\d+',
            ], priority=3),
            
            Intent.SEARCH_LISTINGS: PatternGroup([
                # English patterns
                r'\b(?:show|get|find|display)\s+(?:me\s+)?(?:listings|apartments|places)',
                r'\b(?:i want|i need|looking for)\s+(?:listings|apartments|places)',
                r'\bsearch\s+(?:for\s+)?(?:listings|apartments|places)',
                r'\b(?:browse|look at)\s+(?:available\s+)?(?:listings|apartments|places)',
                r'\b(?:available|open)\s+(?:units?|apartments?|places?)\b',
                r'\blooking\s+(?:for|to rent|to find)\s+(?:a\s+)?(?:room|apartment|place|spot)\b',
                
                # Spanish search patterns
                r'\b(?:busco|estoy buscando|quiero|necesito)\s+(?:un\s+)?(?:apartamento|departamento|vivienda|casa|lugar|opción|opciones|listado|listados|alojamiento|habitación|habitaciones)\b',
                r'\btengo un vale\b.*(?:sección\s*8|section\s*8|voucher)',
                r'\bbuscar\s+(?:apartamento|vivienda|casa|lugar|listado|listados|alojamiento|habitación|habitaciones)\b',
                r'\b(?:sección\s*8|section\s*8|voucher)\b.*(?:bronx|brooklyn|manhattan|queens|staten\s+island)',
                r'\b(?:busco|estoy buscando)\s+(?:vivienda|apartamento|casa)\s+(?:en|en el|en la)\s+(?:bronx|brooklyn|manhattan|queens|staten\s+island)\b',
                r'\b(?:tengo|tiene)\s+(?:un\s+)?(?:vale|voucher)\s+(?:de\s+)?(?:sección\s*8|section\s*8)\b',
                r'\b(?:busco|estoy buscando)\s+(?:un\s+)?(?:apartamento|departamento|vivienda)\s+(?:que\s+)?(?:acepte|acepten|reciba|reciban)\s+(?:vales|vouchers|sección\s*8|section\s*8)\b',
            ], priority=1),
            
            Intent.CHECK_VIOLATIONS: PatternGroup([
                r'\b(?:check|verify|look up)\s+violations?\b',
                r'\bviolations?\s+(?:for|at|on)\b',
                r'\b(?:any|check for)\s+violations?\b',
            ], priority=1),
            
            Intent.VOUCHER_INFO: PatternGroup([
                r'\b(?:what is|tell me about|explain)\s+(?:section\s*8|hasa|cityfheps|housing\s+vouchers?|vouchers?)',
                r'\b(?:voucher|section\s*8|hasa|cityfheps)\s+(?:info|information|details)',
                r'\bhow\s+(?:does|do)\s+(?:vouchers?|section\s*8|hasa|cityfheps|housing\s+vouchers?)\s+work',
                r'\b(?:what are|what\'s)\s+(?:the\s+)?(?:requirements|eligibility|criteria)\s+for\s+(?:section\s*8|hasa|cityfheps|vouchers?)',
                r'\bhow\s+(?:do i|can i)\s+apply\s+for\s+(?:section\s*8|hasa|cityfheps|vouchers?)',
                r'\b(?:difference|differences)\s+between\s+(?:section\s*8|hasa|cityfheps)',
                r'\b(?:can you|could you)\s+explain\s+(?:voucher|section\s*8|hasa|cityfheps)',
                r'\b(?:what|which)\s+voucher\s+(?:types|programs|options)\b',
            ], priority=3),
            
            Intent.SHOW_HELP: PatternGroup([
                # Informational patterns (higher priority to catch before SEARCH_LISTINGS)
                r'\b(?:what|how|why|tell me|explain)\b.*\b(?:benefits|definition|mean|process|steps|work|involve)\b',
                r'\b(?:what are|what is|what does)\b.*\b(?:housing|apartment|listing|search|finding|looking)\b',
                r'\b(?:how do|how does)\b.*\b(?:housing|apartment|listing|search|finding|looking)\b.*\bwork\b',
                r'\b(?:explain|tell me about)\b.*\b(?:housing|apartment|listing|search|finding|looking)\b',
                r'\b(?:how do people|how do most people|how do tenants|how do renters)\b.*\b(?:find|search|look for)\b',
                r'\b(?:what should i know|what do i need to know)\b.*\b(?:finding|searching|looking)\b',
                # Original help patterns
                r'\b(?:help|assistance|support)\b',
                r'\b(?:what can you do|how do i|how can i)\b',
                r'\b(?:commands|options|features)\b',
            ], priority=2),
        }
    
    def _build_parameter_patterns(self) -> Dict[str, List[str]]:
        """Build comprehensive parameter extraction patterns"""
        return {
            'borough': [
                # With prepositions - extract the borough after the preposition (more specific, checked first)
                r'\b(?:in|around|near|at|from)\s+(manhattan|brooklyn|queens|bronx|staten\s+island|bk|si|bx|mnh|qns)\b',
                r'\b(?:search|look|check|try|find)\s+(?:in|around|near)\s+(manhattan|brooklyn|queens|bronx|staten\s+island|bk|si|bx|mnh|qns)\b',
                
                # Full borough names
                r'\b(manhattan)\b',
                r'\b(brooklyn)\b', 
                r'\b(queens)\b',
                r'\b(?:the\s+)?(bronx)\b',
                r'\b(staten\s+island)\b',
                
                # Abbreviations
                r'\b(bk)\b',
                r'\b(si)\b',
                r'\b(bx)\b', 
                r'\b(mnh)\b',
                r'\b(qns)\b',
                
                # Informal references
                r'\b(?:the\s+)?(city)\b',  # Manhattan
                
                # Spanish borough patterns
                r'\b(?:en|en el|en la|del|de la)\s+(manhattan|brooklyn|queens|bronx|staten\s+island)\b',
                r'\b(?:busco|estoy buscando|quiero|necesito)\s+(?:vivienda|apartamento|casa)\s+(?:en|en el|en la)\s+(manhattan|brooklyn|queens|bronx|staten\s+island)\b',
                r'\b(?:vivienda|apartamento|casa)\s+(?:en|en el|en la)\s+(manhattan|brooklyn|queens|bronx|staten\s+island)\b',
            ],
            
            'bedrooms': [
                # Numeric + abbreviations
                r'\b(\d+)\s*(?:br|bed|bedroom|bedrooms?)\b',
                r'\b(\d+)(?:br|bed)\b',
                
                # Spelled out numbers
                r'\b(one|1)\s+(?:bed|bedroom)\b',
                r'\b(two|2)\s+(?:bed|bedroom)\b', 
                r'\b(three|3)\s+(?:bed|bedroom)\b',
                r'\b(four|4)\s+(?:bed|bedroom)\b',
                r'\b(five|5)\s+(?:bed|bedroom)\b',
                
                # Studio handling
                r'\b(studio)\b',  # Convert to 0
                
                # With context words
                r'\b(?:with|for|having)\s+(\d+)\s+(?:bed|bedroom|bedrooms?)\b',
                r'\b(\d+)(?:br|bed|bedroom)\s+(?:apartment|unit|place)\b',
                
                # Spanish bedroom patterns
                r'\b(\d+)\s+(?:habitación|habitaciones|dormitorio|dormitorios)\b',
                r'\b(?:con|de|para)\s+(\d+)\s+(?:habitación|habitaciones|dormitorio|dormitorios)\b',
                r'\b(?:apartamento|departamento|vivienda|casa)\s+(?:de|con)\s+(\d+)\s+(?:habitación|habitaciones|dormitorio|dormitorios)\b',
                r'\b(?:busco|estoy buscando|quiero|necesito)\s+(?:un\s+)?(?:apartamento|departamento|vivienda|casa)\s+(?:de|con)\s+(\d+)\s+(?:habitación|habitaciones|dormitorio|dormitorios)\b',
                
                # Spanish spelled out numbers
                r'\b(uno|una|1)\s+(?:habitación|dormitorio)\b',
                r'\b(dos|2)\s+(?:habitaciones|dormitorios)\b',
                r'\b(tres|3)\s+(?:habitaciones|dormitorios)\b',
                r'\b(cuatro|4)\s+(?:habitaciones|dormitorios)\b',
                r'\b(cinco|5)\s+(?:habitaciones|dormitorios)\b',
                
                # Spanish studio
                r'\b(estudio)\b',  # Convert to 0
            ],
            
            'max_rent': [
                # Standard formats
                r'\$(\d{1,5}(?:,\d{3})*(?:\.\d{2})?)',
                r'\b(\d{1,5}(?:,\d{3})*)\s+dollars?\b',
                
                # With context words
                r'\b(?:under|max|maximum|up\s+to|budget(?:\s+of)?|around|about|roughly)\s+\$?(\d{1,5}(?:,\d{3})*(?:\.\d{2})?)',
                r'\bbudget\s+(?:of\s+)?\$?(\d{1,5}(?:,\d{3})*(?:\.\d{2})?)',
                
                # Informal formats
                r'\b(\d+(?:\.\d+)?)k\b',  # "2k", "2.5k"
                r'\b(?:around|about|roughly)\s+(\d+(?:\.\d+)?)k\b',  # "around 2k"
                
                # Range formats (extract first number)
                r'\$?(\d{1,5}(?:,\d{3})*)\s*(?:-|to)\s*\$?\d+',
                r'\bbetween\s+\$?(\d{1,5}(?:,\d{3})*)\s*(?:and|-|to)',
            ],
            
            'voucher_type': [
                # Section 8 variations
                r'\b(section\s*8|section-8)\b',
                r'\b(sec\s*8)\b',
                
                # HASA variations  
                r'\b(hasa)\b',
                
                # CityFHEPS variations
                r'\b(cityfheps|city\s*fheps)\b',
                
                # Housing voucher
                r'\b(housing\s+voucher)\b',
                
                # Generic voucher references
                r'\b(voucher)s?\b',
                
                # Other NYC assistance programs
                r'\b(dss)\b',
                r'\b(hra)\b',
                
                # Context patterns
                r'\b(?:with|using|accepts?|welcome)\s+(section\s*8|hasa|cityfheps|housing\s+voucher)\b',
                r'\b(section\s*8|hasa|cityfheps|housing\s+voucher)\s+(?:ok|accepted?|welcome)\b',
                
                # Spanish voucher patterns
                r'\b(sección\s*8|section\s*8)\b',
                r'\b(vale|voucher)s?\b',
                r'\b(?:tengo|tiene)\s+(?:un\s+)?(vale|voucher)\s+(?:de\s+)?(?:sección\s*8|section\s*8)\b',
                r'\b(?:vale|voucher)\s+(?:de\s+)?(?:sección\s*8|section\s*8)\b',
                r'\b(?:apartamento|vivienda|casa)\s+(?:que\s+)?(?:acepte|acepten|reciba|reciban)\s+(?:vales|vouchers|sección\s*8|section\s*8)\b',
            ]
        }
    
    def classify_intent(self, message: str, context: Dict = None) -> Intent:
        """Classify message intent using comprehensive pattern matching"""
        message_lower = message.lower()
        
        # Sort intents by priority (higher priority first)
        sorted_intents = sorted(
            self.intent_patterns.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        for intent, pattern_group in sorted_intents:
            for pattern in pattern_group.patterns:
                flags = re.IGNORECASE if pattern_group.case_insensitive else 0
                if re.search(pattern, message_lower, flags):
                    return intent
        
        return Intent.UNCLASSIFIED
    
    def extract_parameters(self, message: str) -> Dict[str, Any]:
        """Extract parameters using comprehensive pattern matching"""
        params = {}
        message_lower = message.lower()
        
        for param_name, patterns in self.parameter_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    
                    # Post-process the extracted value
                    processed_value = self._process_parameter_value(param_name, value)
                    if processed_value is not None:
                        params[param_name] = processed_value
                        break  # Use first match for each parameter
        
        return params
    
    def _process_parameter_value(self, param_name: str, value: str) -> Any:
        """Process and normalize extracted parameter values"""
        value = value.lower().strip()
        
        if param_name == 'borough':
            # Normalize borough names
            borough_mapping = {
                'manhattan': 'manhattan',
                'brooklyn': 'brooklyn', 
                'queens': 'queens',
                'bronx': 'bronx',
                'staten island': 'staten_island',
                'bk': 'bk',
                'si': 'si', 
                'bx': 'bx',
                'mnh': 'mnh',
                'qns': 'qns',
                'city': 'manhattan',  # "the city" = Manhattan
            }
            return borough_mapping.get(value, value)
            
        elif param_name == 'bedrooms':
            # Convert bedroom values to integers
            if value in ['studio', 'estudio']:
                return 0
            elif value in ['one', '1', 'uno', 'una']:
                return 1
            elif value in ['two', '2', 'dos']:
                return 2
            elif value in ['three', '3', 'tres']:
                return 3
            elif value in ['four', '4', 'cuatro']:
                return 4
            elif value in ['five', '5', 'cinco']:
                return 5
            else:
                try:
                    return int(value)
                except ValueError:
                    return None
                    
        elif param_name == 'max_rent':
            # Convert rent values to integers
            # Handle "k" suffix
            if value.endswith('k'):
                try:
                    return int(float(value[:-1]) * 1000)
                except ValueError:
                    return None
            else:
                # Remove commas and convert
                clean_value = value.replace(',', '')
                try:
                    return int(float(clean_value))
                except ValueError:
                    return None
                    
        elif param_name == 'voucher_type':
            # Normalize voucher types
            voucher_mapping = {
                'section 8': 'section_8',
                'section-8': 'section_8',
                'sec 8': 'section_8',
                'sección 8': 'section_8',
                'seccion 8': 'section_8',
                'hasa': 'hasa',
                'cityfheps': 'cityfheps',
                'city fheps': 'cityfheps',
                'housing voucher': 'housing_voucher',
                'voucher': 'housing_voucher',  # Generic
                'vale': 'housing_voucher',  # Spanish generic
                'dss': 'dss',
                'hra': 'hra',
            }
            return voucher_mapping.get(value, value)
        
        return value
    
    def analyze_parameter_changes(self, new_params: Dict, context: Dict = None) -> Dict[str, str]:
        """Enhanced parameter change analysis"""
        if not context:
            return {param: "new" for param in new_params}
        
        analysis = {}
        previous_params = context.get('parameters', {})
        
        for param, value in new_params.items():
            if param not in previous_params:
                analysis[param] = "new"
            elif previous_params[param] == value:
                # Check if we should allow redundant borough searches
                if (param == 'borough' and 
                    context.get('last_result_count', 0) == 0):
                    analysis[param] = "retry_allowed"
                else:
                    analysis[param] = "redundant"
            else:
                analysis[param] = "refinement"
        
        return analysis
    
    def generate_response(self, intent: Intent, params: Dict, param_analysis: Dict = None, context: Dict = None) -> str:
        """Generate contextual response based on intent and parameters"""
        if intent == Intent.WHAT_IF:
            if not params:
                return "I'll help you with that search."
            
            # Build response based on parameters
            response_parts = []
            
            if 'borough' in params:
                borough_name = params['borough'].replace('_', ' ').title()
                if param_analysis and param_analysis.get('borough') == 'retry_allowed':
                    response_parts.append(f"I'll search {borough_name} again (previous search found no listings)")
                elif param_analysis and param_analysis.get('borough') == 'redundant':
                    response_parts.append(f"I'll search {borough_name} again")
                else:
                    response_parts.append(f"I'll search {borough_name}")
            
            if 'bedrooms' in params:
                bedrooms = params['bedrooms']
                if bedrooms == 0:
                    response_parts.append("for studio apartments")
                else:
                    response_parts.append(f"for {bedrooms} bedroom apartments")
            
            if 'max_rent' in params:
                rent = params['max_rent']
                response_parts.append(f"under ${rent:,}")
            
            if 'voucher_type' in params:
                voucher = params['voucher_type'].replace('_', ' ').title()
                response_parts.append(f"accepting {voucher}")
            
            if response_parts:
                return " ".join(response_parts) + "."
            else:
                return "I'll help you with that search."
        
        elif intent == Intent.PARAMETER_REFINEMENT:
            if 'max_rent' in params:
                return f"I'll refine the search to show listings under ${params['max_rent']:,}."
            return "I'll refine the search parameters."
        
        elif intent == Intent.SEARCH_LISTINGS:
            return "I'll search for listings matching your criteria."
        
        elif intent == Intent.CHECK_VIOLATIONS:
            return "I'll check for violations on that property."
        
        elif intent == Intent.VOUCHER_INFO:
            return "I'll provide information about voucher programs."
        
        elif intent == Intent.SHOW_HELP:
            return "I can help you search for apartments, check violations, and provide voucher information."
        
        else:
            return "I'll help you with that search."
    
    def process_message(self, message: str, context: Dict = None) -> Tuple[Intent, Dict, str]:
        """Process message and return intent, parameters, and response"""
        intent = self.classify_intent(message, context)
        params = self.extract_parameters(message)
        param_analysis = self.analyze_parameter_changes(params, context)
        response = self.generate_response(intent, params, param_analysis, context)
        
        return intent, params, response

# Convenience functions for backward compatibility
def classify_intent(message: str, context: Dict = None) -> Intent:
    router = EnhancedSemanticRouterV2()
    return router.classify_intent(message, context)

def extract_parameters(message: str) -> Dict[str, Any]:
    router = EnhancedSemanticRouterV2()
    return router.extract_parameters(message)

if __name__ == "__main__":
    # Quick test
    router = EnhancedSemanticRouterV2()
    
    test_messages = [
        "Look in Staten Island",
        "Try 2 bedrooms", 
        "Budget of $3000",
        "With Section 8",
        "Check Brooklyn yo",
        "Around 2k",
        "Search in Manhattan",
        "Look for 3 bedroom",
    ]
    
    print("🧪 Testing Enhanced Semantic Router V2")
    print("=" * 50)
    
    for msg in test_messages:
        intent, params, response = router.process_message(msg)
        print(f"\nMessage: '{msg}'")
        print(f"Intent: {intent.value}")
        print(f"Params: {params}")
        print(f"Response: {response}") 