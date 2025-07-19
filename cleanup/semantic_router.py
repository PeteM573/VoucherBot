"""
Enhanced Semantic Router for VoucherBot Application

This module provides context-aware intent classification and parameter extraction
for natural language understanding in housing search conversations.
"""

import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime

logger = logging.getLogger(__name__)

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
    patterns: List[str]
    priority: int  # Higher number = higher priority
    requires_context: bool = False
    description: str = ""

@dataclass
class Parameter:
    name: str
    patterns: List[str]
    transform: Optional[callable] = None
    aliases: List[str] = field(default_factory=list)

@dataclass
class ParameterChange:
    param_name: str
    old_value: Optional[Any]
    new_value: Any
    change_type: str  # "new", "redundant", "refinement", "conflict"

@dataclass
class SearchContext:
    current_borough: Optional[str] = None
    current_params: Dict[str, Any] = field(default_factory=dict)
    search_history: List[Dict] = field(default_factory=list)
    last_result_count: int = 0
    
    def allows_borough_retry(self) -> bool:
        """Determine if borough can be searched again"""
        return (
            self.last_result_count == 0 or  # No results found
            len(self.search_history) == 0 or  # First search
            self._params_changed()  # Other parameters changed
        )
    
    def _params_changed(self) -> bool:
        """Check if non-borough parameters changed"""
        if not self.search_history:
            return True
        last_params = self.search_history[-1].get("params", {})
        current_non_borough = {k: v for k, v in self.current_params.items() 
                             if k != "borough"}
        last_non_borough = {k: v for k, v in last_params.items() 
                           if k != "borough"}
        return current_non_borough != last_non_borough

@dataclass
class ClassificationResult:
    intent: Intent
    confidence: float
    matched_patterns: List[Tuple[str, str]]  # (pattern, matched_text)
    requires_context: bool
    extracted_params: Optional[Dict] = None

@dataclass
class ResponseContext:
    changes: List[ParameterChange]
    search_context: SearchContext
    intent: Intent
    confidence: float

# Intent patterns with priorities and context requirements
INTENT_PATTERNS: Dict[Intent, PatternGroup] = {
    Intent.WHAT_IF: PatternGroup(
        patterns=[
            r"\b(what if|how about|what about)\b",
            r"\btry\b.*\b(looking|searching|checking|bk|brooklyn|manhattan|bronx|queens|si|staten)\b",
            r"\bcheck\b.*\b(in|with|for|bk|brooklyn|manhattan|bronx|queens|si|staten|\d+br|\d+\s*bed|\$\d+)\b",
            r"\binstead\b.*\b(of|in|with)\b"
        ],
        priority=3,
        requires_context=True,
        description="What-if scenarios that modify existing searches"
    ),
    
    Intent.PARAMETER_REFINEMENT: PatternGroup(
        patterns=[
            r"\b(add|include|also|with)\b.*\b(bedrooms?|bed|br)\b",
            r"\b(under|below|max|maximum)\b.*\$?\d+",
            r"\b(only|just)\b.*\b(studio|1br|2br|3br|4br)\b",
            r"\balso\s+look\s+for\b.*\b(\d+br|\d+\s*bed|studio)\b"
        ],
        priority=2,
        requires_context=True,
        description="Adding or refining search parameters"
    ),
    
    Intent.SEARCH_LISTINGS: PatternGroup(
        patterns=[
            r"\b(find|search|look for|browse)\b.*\b(housing|apartment|place|listing|home|spot|unit)\b",
            r"\b(listings?|places?)\b.*\b(available|renting|open)\b",
            r"\b(available|open)\b.*\b(units?|apartments?)\b",
            r"\blooking (for|to rent|to find)\b.*\b(room|apartment|place|spot)\b",
            r"\bbrowse\s+(available\s+)?listings?\b",
            r"\bfind\s+.*\s+apartments?\b",
            r"\bfind\s+apartments?\b"
        ],
        priority=1,
        description="Initial housing search requests"
    ),
    
    Intent.CHECK_VIOLATIONS: PatternGroup(
        patterns=[
            r"\b(check|see|lookup|find out|review)\b.*\b(violations?|hpd|safety|issues?)\b",
            r"\b(is|was|are)\b.*\b(this|that)?\b.*\b(building|apartment|place)\b.*\b(safe|good|clean|legal)\b",
            r"\b(has|have) (any|a lot of)? violations\b",
            r"\bhow many violations\b.*\b(building|apartment|listing)\b"
        ],
        priority=1,
        description="Building safety and violation checks"
    ),
    
    Intent.VOUCHER_INFO: PatternGroup(
        patterns=[
            r"\b(section[\s\-]?8|hasa|cityfeps|voucher(s)?|housing assistance|hra)\b",
            r"\b(accepts?|takes?)\b.*\bvouchers?\b",
            r"\b(how|where|when)\b.*\b(apply|get|use)\b.*\bvoucher\b",
            r"\bi (have|got) (a )?(hasa|section[\s\-]?8|voucher)\b"
        ],
        priority=1,
        description="Voucher program information and eligibility"
    ),
    
    Intent.SHOW_HELP: PatternGroup(
        patterns=[
            r"\b(help|what can you do|options|commands|features|assist|instructions)\b",
            r"\b(stuck|lost|confused)\b",
            r"\bhow (do|can) i\b.*(use|search|find)"
        ],
        priority=1,
        description="Help and usage instructions"
    )
}

# Parameter extraction patterns
INTENT_PARAMETERS: Dict[Intent, List[Parameter]] = {
    Intent.WHAT_IF: [
        Parameter(
            name="borough",
            patterns=[
                r"\b(in|at|near)\s+(the\s+)?(bronx|brooklyn|manhattan|queens|staten\s+island)\b",
                r"\b(bk|si|bx|qns|mnh)\b",
                r"\b(bronx|brooklyn|manhattan|queens|staten\s+island)\b",
                r"\bhow\s+about\s+(the\s+)?(bronx|brooklyn|manhattan|queens|staten\s+island)\b"
            ],
            transform=lambda x: x.lower().replace(" ", "_"),
            aliases=["bk", "brooklyn", "si", "staten_island", "bx", "bronx", "qns", "queens", "mnh", "manhattan"]
        ),
        Parameter(
            name="bedrooms",
            patterns=[
                r"\b(\d+)\s*(?:bed|br|bedroom)",
                r"\b(?:bed|br|bedroom)\s*(\d+)\b",
                r"\b(\d+)br\b"
            ],
            transform=int
        ),
        Parameter(
            name="max_rent",
            patterns=[
                r"\$(\d+(?:,\d{3})*)",
                r"\b(\d+)\s*dollars?\b",
                r"\bunder\s*\$?(\d+)",
                r"\bmax\s*\$?(\d+)"
            ],
            transform=lambda x: int(str(x).replace(",", ""))
        ),
        Parameter(
            name="voucher_type",
            patterns=[
                r"\b(section[\s\-]?8|hasa|cityfeps|housing\s+voucher)\b",
                r"\b(section[\s\-]?8|hasa|cityfheps|housing\s+voucher)\s+(welcome|accepted|ok|okay)\b"
            ],
            transform=lambda x: x.lower().replace(" ", "_").replace("-", "_")
        )
    ],
    
    Intent.PARAMETER_REFINEMENT: [
        Parameter(
            name="bedrooms",
            patterns=[
                r"\b(\d+)\s*(?:bed|br|bedroom)",
                r"\b(?:bed|br|bedroom)\s*(\d+)\b"
            ],
            transform=int
        ),
        Parameter(
            name="max_rent",
            patterns=[
                r"\$(\d+(?:,\d{3})*)",
                r"\bunder\s*\$?(\d+)"
            ],
            transform=lambda x: int(str(x).replace(",", ""))
        )
    ],
    
    Intent.SEARCH_LISTINGS: [
        Parameter(
            name="borough",
            patterns=[
                r"\b(in|at|near)\s+(the\s+)?(bronx|brooklyn|manhattan|queens|staten\s+island)\b",
                r"\b(bk|si|bx|qns|mnh)\b"
            ],
            transform=lambda x: x.lower().replace(" ", "_")
        ),
        Parameter(
            name="bedrooms",
            patterns=[
                r"\b(\d+)\s*(?:bed|br|bedroom)",
                r"\b(?:bed|br|bedroom)\s*(\d+)\b"
            ],
            transform=int
        ),
        Parameter(
            name="voucher_type",
            patterns=[
                r"\b(section[\s\-]?8|hasa|cityfeps|housing\s+voucher)\b",
                r"\b(section[\s\-]?8|hasa|cityfheps|housing\s+voucher)\s+(welcome|accepted|ok|okay)\b"
            ],
            transform=lambda x: x.lower().replace(" ", "_").replace("-", "_")
        )
    ]
}

class ParameterAnalyzer:
    """Analyzes parameter changes between current and new parameters"""
    
    def analyze_changes(
        self,
        current_params: Dict[str, Any],
        new_params: Dict[str, Any],
        context: SearchContext
    ) -> List[ParameterChange]:
        changes = []
        
        for param, value in new_params.items():
            if param not in current_params:
                changes.append(ParameterChange(
                    param_name=param,
                    old_value=None,
                    new_value=value,
                    change_type="new"
                ))
            elif param == "borough":
                if current_params[param] == value:
                    if context.allows_borough_retry():
                        changes.append(ParameterChange(
                            param_name=param,
                            old_value=current_params[param],
                            new_value=value,
                            change_type="refinement"
                        ))
                    else:
                        changes.append(ParameterChange(
                            param_name=param,
                            old_value=value,
                            new_value=value,
                            change_type="redundant"
                        ))
                else:
                    changes.append(ParameterChange(
                        param_name=param,
                        old_value=current_params[param],
                        new_value=value,
                        change_type="refinement"
                    ))
            elif current_params[param] == value:
                changes.append(ParameterChange(
                    param_name=param,
                    old_value=value,
                    new_value=value,
                    change_type="redundant"
                ))
            else:
                changes.append(ParameterChange(
                    param_name=param,
                    old_value=current_params[param],
                    new_value=value,
                    change_type="refinement"
                ))
        
        return changes

class ResponseGenerator:
    """Generates natural language responses based on parameter changes"""
    
    def generate_response(self, context: ResponseContext) -> str:
        """Generate natural language response based on parameter changes"""
        parts = []
        
        # Group changes by type
        changes_by_type = self._group_changes(context.changes)
        
        # Handle borough changes specially
        borough_changes = [c for c in context.changes if c.param_name == "borough"]
        if borough_changes:
            borough_change = borough_changes[0]
            if context.search_context.last_result_count == 0:
                parts.append(
                    f"I'll search {borough_change.new_value.replace('_', ' ').title()} again "
                    f"(previous search found no listings)"
                )
            elif borough_change.change_type == "refinement":
                parts.append(
                    f"Updating search location to {borough_change.new_value.replace('_', ' ').title()}"
                )
            elif borough_change.change_type == "redundant":
                parts.append(
                    f"We're already searching in {borough_change.new_value.replace('_', ' ').title()}"
                )
        
        # Handle other parameter changes
        new_params = [c for c in changes_by_type.get("new", []) if c.param_name != "borough"]
        if new_params:
            param_str = ", ".join(f"{p.param_name.replace('_', ' ')}: {p.new_value}" 
                                for p in new_params)
            parts.append(f"Adding new criteria: {param_str}")
            
        refinements = [c for c in changes_by_type.get("refinement", []) if c.param_name != "borough"]
        if refinements:
            param_str = ", ".join(
                f"{p.param_name.replace('_', ' ')} from {p.old_value} to {p.new_value}" 
                for p in refinements
            )
            if param_str:
                parts.append(f"Refining: {param_str}")
        
        # Handle redundant cases
        redundant_params = changes_by_type.get("redundant", [])
        if redundant_params and not new_params and not refinements:
            redundant_str = ", ".join(p.param_name.replace('_', ' ') for p in redundant_params)
            return f"We're already searching with those criteria: {redundant_str}."
        
        return ". ".join(parts) + "." if parts else "I'll help you with that search."
    
    def _group_changes(
        self, 
        changes: List[ParameterChange]
    ) -> Dict[str, List[ParameterChange]]:
        grouped = {}
        for change in changes:
            grouped.setdefault(change.change_type, []).append(change)
        return grouped

def classify_intent(
    message: str,
    current_state: Optional[Dict] = None,
    previous_intent: Optional[Intent] = None
) -> ClassificationResult:
    """
    Enhanced classification that considers conversation context and state.
    """
    msg = message.lower()
    matches = []
    
    # Check each intent's patterns
    for intent, pattern_group in INTENT_PATTERNS.items():
        for pattern in pattern_group.patterns:
            if match := re.search(pattern, msg):
                matches.append((
                    intent,
                    pattern_group.priority,
                    pattern,
                    match.group(0),
                    pattern_group.requires_context
                ))
    
    if not matches:
        return ClassificationResult(
            intent=Intent.UNCLASSIFIED,
            confidence=0.0,
            matched_patterns=[],
            requires_context=False
        )
    
    # Sort by priority
    matches.sort(key=lambda x: x[1], reverse=True)
    top_match = matches[0]
    
    # Handle context-dependent intents
    if top_match[4]:  # requires_context
        if not current_state:
            # Fallback to next best non-context-dependent match
            for match in matches[1:]:
                if not match[4]:  # doesn't require context
                    top_match = match
                    break
            else:
                # No non-context match found, use original but with lower confidence
                pass
    
    return ClassificationResult(
        intent=top_match[0],
        confidence=1.0 if len(matches) == 1 else 0.8,
        matched_patterns=[(m[2], m[3]) for m in matches],
        requires_context=top_match[4]
    )

def extract_parameters(
    message: str,
    intent: Intent
) -> Dict[str, Any]:
    """
    Extract structured parameters based on intent.
    """
    params = {}
    if intent not in INTENT_PARAMETERS:
        return params
        
    for param in INTENT_PARAMETERS[intent]:
        for pattern in param.patterns:
            if match := re.search(pattern, message, re.I):
                value = match.group(1)
                if param.transform:
                    try:
                        value = param.transform(value)
                    except (ValueError, TypeError):
                        continue  # Skip if transformation fails
                params[param.name] = value
                break
                
    return params

class EnhancedSemanticRouter:
    """Main semantic router with context awareness and parameter analysis"""
    
    def __init__(self):
        self.parameter_analyzer = ParameterAnalyzer()
        self.response_generator = ResponseGenerator()
        self.context: Optional[SearchContext] = None
    
    def process_message(
        self, 
        message: str,
        current_state: Optional[Dict] = None
    ) -> Tuple[Intent, Dict[str, Any], str]:
        """Process message and return intent, parameters, and response"""
        
        # Classify intent
        classification = classify_intent(message, current_state)
        
        # Extract parameters
        new_params = extract_parameters(message, classification.intent)
        
        # Initialize or update context
        if not self.context:
            self.context = SearchContext(
                current_borough=current_state.get("borough") if current_state else None,
                current_params=current_state.copy() if current_state else {},
                search_history=[],
                last_result_count=current_state.get("last_result_count", 0) if current_state else 0
            )
        
        # Analyze parameter changes
        changes = self.parameter_analyzer.analyze_changes(
            self.context.current_params,
            new_params,
            self.context
        )
        
        # Generate response
        response_ctx = ResponseContext(
            changes=changes,
            search_context=self.context,
            intent=classification.intent,
            confidence=classification.confidence
        )
        response = self.response_generator.generate_response(response_ctx)
        
        # Update context
        self._update_context(new_params)
        
        # Log classification
        self._log_classification(message, classification, new_params, response)
        
        return classification.intent, new_params, response
    
    def update_search_results(self, result_count: int):
        """Update context with search results"""
        if self.context:
            self.context.last_result_count = result_count
    
    def _update_context(self, new_params: Dict[str, Any]):
        """Update search context with new parameters"""
        if self.context:
            self.context.search_history.append({
                "params": self.context.current_params.copy(),
                "result_count": self.context.last_result_count,
                "timestamp": datetime.now().isoformat()
            })
            self.context.current_params.update(new_params)
            if "borough" in new_params:
                self.context.current_borough = new_params["borough"]
    
    def _log_classification(
        self,
        message: str,
        classification: ClassificationResult,
        params: Dict[str, Any],
        response: str
    ):
        """Log classification results for analysis"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "intent": classification.intent.value,
            "confidence": classification.confidence,
            "extracted_params": params,
            "response": response
        }
        
        logger.info(f"Classification: {log_data}")
        
        # Log unclassified messages for pattern improvement
        if classification.intent == Intent.UNCLASSIFIED:
            logger.warning(f"Unclassified message: {message}")

# Convenience functions for backward compatibility
def classify_intent_with_regex(message: str) -> str:
    """Simple classification function for backward compatibility"""
    result = classify_intent(message)
    return result.intent.value

def classify_intent_with_debug(message: str) -> dict:
    """Debug classification function for backward compatibility"""
    result = classify_intent(message)
    return {
        "intent": result.intent.value,
        "matches": result.matched_patterns,
        "confidence": result.confidence
    } 