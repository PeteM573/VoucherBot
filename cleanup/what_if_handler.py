#!/usr/bin/env python3
"""
Enhanced "What If" Scenario Handler
Im
This module provides sophisticated handling of "what if" scenarios where users
want to modify their previous search parameters. It demonstrates conversational
intelligence and LLM-driven value by:

1. Understanding natural language variations of parameter changes
2. Maintaining context from previous searches
3. Validating changes and providing user feedback
4. Supporting multiple parameter modifications in one request
"""

import re
from typing import Dict, List, Tuple, Optional, Any
import gradio as gr
from utils import log_tool_action, current_timestamp


class WhatIfScenarioAnalyzer:
    """
    Enhanced "What If" scenario handler that improves on basic pattern matching
    """
    
    def __init__(self):
        # Comprehensive patterns for detecting what-if scenarios
        self.what_if_patterns = [
            # Basic what-if patterns
            r"(?i)what if",
            r"(?i)how about",
            r"(?i)what about",
            
            # Alternative phrasing patterns
            r"(?i)(try|check|look).{0,20}(in|at|for|with).{0,20}(different|another|other)",
            r"(?i)(change|switch|move).{0,20}(to|in|for)",
            r"(?i)can you.{0,20}(try|check|search)",
            r"(?i)(show me|find).{0,20}(in|for).{0,20}(different|another)",
            
            # Comparison patterns
            r"(?i)instead of",
            r"(?i)(compare|versus|vs).{0,20}(bronx|brooklyn|manhattan|queens|staten)",
            r"(?i)same search.{0,20}but",
            
            # Exploratory patterns
            r"(?i)(explore|consider).{0,20}(other|different)",
            r"(?i)let's (try|see|check)",
            
            # Simple borough mentions that could be what-if
            r"(?i)^(try|check|look)\s+(bronx|brooklyn|manhattan|queens|staten)",
            r"(?i)^(how about|what about)\s+(bronx|brooklyn|manhattan|queens|staten)",
            
            # Direct try/check patterns
            r"(?i)^try\s+",
            r"(?i)\btry\s+(the\s+)?(bronx|brooklyn|manhattan|queens|staten)",
            r"(?i)\bcheck\s+(the\s+)?(bronx|brooklyn|manhattan|queens|staten)",
            r"(?i)\btry\s+with\s+",
            r"(?i)\bcheck\s+with\s+",
            r"(?i)\bcheck\s+\w+br\b",  # Check for "check 4br" patterns
            r"(?i)\bcheck\s+si\b"  # Check for "check SI"
        ]
        
        # Enhanced borough detection with variations and abbreviations
        self.borough_patterns = {
            "bronx": [
                r"(?i)\b(the\s+)?bronx\b",
                r"(?i)\bbx\b"
            ],
            "brooklyn": [
                r"(?i)\bbrooklyn\b",
                r"(?i)\bbk\b",
                r"(?i)\bbklyn\b"
            ],
            "manhattan": [
                r"(?i)\bmanhattan\b",
                r"(?i)\bmnh\b",
                r"(?i)\bnyc\b(?!\s+(all|area|wide))",
                r"(?i)\bmidtown\b",
                r"(?i)\bthe\s+city\b"
            ],
            "queens": [
                r"(?i)\bqueens\b",
                r"(?i)\bque\b"
            ],
            "staten_island": [
                r"(?i)\bstaten\s+island\b",
                r"(?i)\bstaten\b",
                r"(?i)\bsi\b"
            ]
        }
        
        # Parameter modification patterns with better extraction
        self.parameter_patterns = {
            "max_rent": [
                r"(?i)\$(\d{1,5})\s*(max|maximum|budget|limit)?",
                r"(?i)(under|below|up\s+to)\s*\$?(\d{1,5})",
                r"(?i)budget.{0,10}\$?(\d{1,5})",
                r"(?i)(\d{1,5})\s*dollars?\s*(max|budget|limit)?",
                r"(?i)with\s+(\d{1,5})\s+dollars?\s+(budget|max|limit)",
                r"(?i)(\d{1,5})\s+(budget|max|limit|maximum)",
                r"(?i)a\s+\$(\d{1,5})\s+budget",
                r"(?i)budget\s+was\s+\$?(\d{1,5})"
            ],
            "voucher_type": [
                r"(?i)(section\s*8|section-8)",
                r"(?i)(cityfheps|city\s*fheps|fheps)",
                r"(?i)(hasa)",
                r"(?i)(dss)",
                r"(?i)(housing\s+)?voucher"
            ],
            "bedrooms": [
                r"(?i)(\d+)\s*(bed|bedroom|br)\b",
                r"(?i)(studio|one|two|three|four|five)\s*(bed|bedroom|br)?\b",
                r"(?i)\b(\d+)br\b",
                r"(?i)(\d+)\s+bedrooms?",
                r"(?i)(studio|one|two|three|four|five)\s+bedrooms?",
                r"(?i)\b(\d+)\s+bed\b"
            ]
        }

    def detect_what_if_scenario(self, message: str, state: Dict) -> Tuple[bool, Dict[str, Any]]:
        """
        Enhanced what-if detection with comprehensive parameter extraction
        Returns: (is_what_if, extracted_changes)
        """
        message_lower = message.lower()
        
        # Check if this is a what-if scenario
        is_what_if = any(
            re.search(pattern, message_lower) for pattern in self.what_if_patterns
        )
        
        if not is_what_if:
            return False, {}
        
        log_tool_action("WhatIfAnalyzer", "scenario_detected", {
            "message": message,
            "timestamp": current_timestamp()
        })
        
        # Extract what parameters are being changed
        changes = {}
        
        # Extract borough changes
        new_borough = self._extract_borough_change(message_lower)
        if new_borough:
            changes["borough"] = new_borough
        
        # Extract rent changes
        new_rent = self._extract_rent_change(message_lower)
        if new_rent:
            changes["max_rent"] = new_rent
        
        # Extract voucher type changes
        new_voucher = self._extract_voucher_change(message_lower)
        if new_voucher:
            changes["voucher_type"] = new_voucher
        
        # Extract bedroom changes
        new_bedrooms = self._extract_bedroom_change(message_lower)
        if new_bedrooms:
            changes["bedrooms"] = new_bedrooms
        
        log_tool_action("WhatIfAnalyzer", "parameters_extracted", {
            "changes": changes,
            "message": message
        })
        
        return True, changes

    def _extract_borough_change(self, message: str) -> Optional[str]:
        """Extract borough change from message"""
        for borough, patterns in self.borough_patterns.items():
            if any(re.search(pattern, message) for pattern in patterns):
                return borough
        return None

    def _extract_rent_change(self, message: str) -> Optional[int]:
        """Extract rent/budget change from message"""
        for pattern in self.parameter_patterns["max_rent"]:
            match = re.search(pattern, message)
            if match:
                # Extract the number from the match groups
                for group in match.groups():
                    if group and group.replace('$', '').replace(',', '').isdigit():
                        rent_value = int(group.replace('$', '').replace(',', ''))
                        # Validate reasonable rent range for NYC
                        if 500 <= rent_value <= 10000:
                            return rent_value
        return None

    def _extract_voucher_change(self, message: str) -> Optional[str]:
        """Extract voucher type change from message"""
        # Check each pattern individually for better matching
        if re.search(r"(?i)\bsection\s*8\b", message) or re.search(r"(?i)\bsection-8\b", message):
            return "Section 8"
        elif re.search(r"(?i)\bcityfheps\b", message) or re.search(r"(?i)\bcity\s*fheps\b", message) or re.search(r"(?i)\bfheps\b", message):
            return "CityFHEPS"
        elif re.search(r"(?i)\bhasa\b", message):
            return "HASA"
        elif re.search(r"(?i)\bdss\b", message):
            return "DSS"
        elif re.search(r"(?i)\bhousing\s+voucher\b", message) or re.search(r"(?i)\bvoucher\b", message):
            return "Housing Voucher"
        
        return None

    def _extract_bedroom_change(self, message: str) -> Optional[str]:
        """Extract bedroom requirement change from message"""
        bedroom_map = {
            "studio": "Studio",
            "one": "1 bedroom",
            "two": "2 bedroom", 
            "three": "3 bedroom",
            "four": "4 bedroom",
            "five": "5 bedroom"
        }
        
        for pattern in self.parameter_patterns["bedrooms"]:
            match = re.search(pattern, message)
            if match:
                for group in match.groups():
                    if group:
                        if group.isdigit():
                            num = int(group)
                            if 0 <= num <= 5:  # Validate reasonable bedroom count
                                return f"{group} bedroom" if num > 0 else "Studio"
                        elif group.lower() in bedroom_map:
                            return bedroom_map[group.lower()]
        return None


class ImprovedWhatIfHandler:
    """
    Improved what-if scenario handler that addresses limitations in basic implementations
    """
    
    def __init__(self):
        self.analyzer = WhatIfScenarioAnalyzer()
    
    def handle_what_if_scenario(self, message: str, history: List, state: Dict) -> Tuple[List, Dict]:
        """
        Enhanced what-if handler with better state management and validation
        """
        try:
            # Detect what-if scenario and extract changes
            is_what_if, changes = self.analyzer.detect_what_if_scenario(message, state)
            
            if not is_what_if:
                return self._handle_non_what_if(message, history, state)
            
            # Validate that we have previous search context
            validation_result = self._validate_context_and_changes(state, changes)
            if not validation_result["valid"]:
                history.append({
                    "role": "assistant",
                    "content": validation_result["message"],
                    "metadata": {
                        "title": "⚠️ Context Required",
                        "timestamp": current_timestamp()
                    }
                })
                return history, state
            
            # Get current preferences and apply changes
            current_prefs = state.get("preferences", {})
            new_prefs = self._apply_changes(current_prefs, changes)
            
            # Create confirmation message
            confirmation = self._create_confirmation_message(changes, current_prefs, new_prefs)
            history.append({
                "role": "assistant",
                "content": confirmation,
                "metadata": {
                    "title": "🔄 Modifying Search",
                    "timestamp": current_timestamp()
                }
            })
            
            # Update state with new preferences
            updated_state = state.copy()
            updated_state["preferences"] = new_prefs
            updated_state["last_what_if_changes"] = changes
            updated_state["previous_search"] = current_prefs.copy()
            
            log_tool_action("WhatIfHandler", "search_modified", {
                "original_prefs": current_prefs,
                "new_prefs": new_prefs,
                "changes": changes
            })
            
            return history, updated_state
            
        except Exception as e:
            log_tool_action("WhatIfHandler", "error", {
                "error": str(e),
                "message": message
            })
            
            error_msg = f"I encountered an error processing your request: {str(e)}. Could you please rephrase what you'd like to change about your search?"
            history.append({
                "role": "assistant",
                "content": error_msg,
                "metadata": {
                    "title": "❌ Error",
                    "timestamp": current_timestamp()
                }
            })
            return history, state

    def _validate_context_and_changes(self, state: Dict, changes: Dict) -> Dict:
        """Validate that we have context and that changes make sense"""
        
        # Check if we have previous search context
        prefs = state.get("preferences", {})
        if not prefs or not any(prefs.get(key) for key in ["borough", "voucher_type", "max_rent"]):
            return {
                "valid": False,
                "message": "I'd be happy to help you explore different options! However, I don't see a previous search to modify. Could you first search for apartments (e.g., 'Find Section 8 apartments in Brooklyn'), and then I can help you explore alternatives?"
            }
        
        # Check that we actually extracted some changes
        if not changes:
            return {
                "valid": False,
                "message": "I couldn't identify what you'd like to change about your search. Could you be more specific? For example:\n• 'What if I looked in Manhattan instead?'\n• 'How about with a $3000 budget?'\n• 'Try searching for 2 bedrooms instead'"
            }
        
        # Check for redundant changes
        for param, new_value in changes.items():
            current_value = prefs.get(param)
            if current_value and str(current_value).lower() == str(new_value).lower():
                return {
                    "valid": False,
                    "message": f"You're already searching with {param.replace('_', ' ')} set to {new_value}. Did you mean something different?"
                }
        
        return {"valid": True, "message": ""}

    def _apply_changes(self, current_prefs: Dict, changes: Dict) -> Dict:
        """Apply changes to current preferences"""
        new_prefs = current_prefs.copy()
        new_prefs.update(changes)
        return new_prefs

    def _create_confirmation_message(self, changes: Dict, old_prefs: Dict, new_prefs: Dict) -> str:
        """Create a user-friendly confirmation message showing what's being changed"""
        change_descriptions = []
        
        if "borough" in changes:
            old_borough = old_prefs.get("borough", "").replace("_", " ").title()
            new_borough = changes["borough"].replace("_", " ").title()
            if old_borough:
                change_descriptions.append(f"searching in **{new_borough}** instead of {old_borough}")
            else:
                change_descriptions.append(f"searching in **{new_borough}**")
        
        if "max_rent" in changes:
            old_rent = old_prefs.get("max_rent")
            new_rent = changes["max_rent"]
            if old_rent:
                change_descriptions.append(f"budget of **${new_rent:,}** instead of ${old_rent:,}")
            else:
                change_descriptions.append(f"budget of **${new_rent:,}**")
        
        if "voucher_type" in changes:
            old_voucher = old_prefs.get("voucher_type", "")
            new_voucher = changes["voucher_type"]
            if old_voucher:
                change_descriptions.append(f"**{new_voucher}** instead of {old_voucher}")
            else:
                change_descriptions.append(f"**{new_voucher}**")
        
        if "bedrooms" in changes:
            old_bedrooms = old_prefs.get("bedrooms", "")
            new_bedrooms = changes["bedrooms"]
            if old_bedrooms:
                change_descriptions.append(f"**{new_bedrooms}** instead of {old_bedrooms}")
            else:
                change_descriptions.append(f"**{new_bedrooms}**")
        
        if len(change_descriptions) == 1:
            changes_text = change_descriptions[0]
        elif len(change_descriptions) == 2:
            changes_text = " and ".join(change_descriptions)
        else:
            changes_text = ", ".join(change_descriptions[:-1]) + f", and {change_descriptions[-1]}"
        
        return f"""🔄 **Exploring Alternative Options**

Great idea! I'll modify your search by {changes_text}.

*Searching for voucher-friendly apartments with your updated criteria...*"""

    def _handle_non_what_if(self, message: str, history: List, state: Dict) -> Tuple[List, Dict]:
        """Handle messages that aren't what-if scenarios"""
        # This would delegate to other handlers in the actual implementation
        return history, state


# Utility functions for integration with the main app
def detect_what_if_message(message: str, state: Dict) -> bool:
    """Quick detection function for message classification - now using V2 router"""
    try:
        from enhanced_semantic_router_v2 import EnhancedSemanticRouterV2, Intent
        router = EnhancedSemanticRouterV2()
        intent = router.classify_intent(message, state)
        return intent == Intent.WHAT_IF
    except ImportError:
        # Fallback to original analyzer if V2 not available
        analyzer = WhatIfScenarioAnalyzer()
        is_what_if, _ = analyzer.detect_what_if_scenario(message, state)
        return is_what_if


def process_what_if_scenario(message: str, history: List, state: Dict) -> Tuple[List, Dict]:
    """Process a what-if scenario and return updated history and state"""
    handler = ImprovedWhatIfHandler()
    return handler.handle_what_if_scenario(message, history, state) 