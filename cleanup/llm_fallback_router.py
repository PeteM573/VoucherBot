#!/usr/bin/env python3
"""
LLM Fallback Router for VoucherBot

This module implements an LLM-powered semantic router that serves as a fallback
for handling natural language queries that the regex-based router cannot process.

Key Features:
- Intent classification for housing search queries
- Parameter extraction with validation
- Robust error handling and JSON parsing
- Support for context-aware routing
- Comprehensive input validation
- Multilingual support for English, Spanish, Chinese, and Bengali
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

# Set up logging
logger = logging.getLogger(__name__)

class IntentType(Enum):
    """Supported intent types for housing search queries."""
    SEARCH_LISTINGS = "SEARCH_LISTINGS"
    CHECK_VIOLATIONS = "CHECK_VIOLATIONS"
    ASK_VOUCHER_SUPPORT = "ASK_VOUCHER_SUPPORT"
    REFINE_SEARCH = "REFINE_SEARCH"
    FOLLOW_UP = "FOLLOW_UP"
    HELP_REQUEST = "HELP_REQUEST"
    UNKNOWN = "UNKNOWN"

# Custom Exceptions
class LLMFallbackRouterError(Exception):
    """Base exception for LLM Fallback Router errors."""
    pass

class InvalidInputError(LLMFallbackRouterError):
    """Raised when input validation fails."""
    pass

class InvalidLLMResponseError(LLMFallbackRouterError):
    """Raised when LLM response cannot be parsed or validated."""
    pass

class LLMProcessingError(LLMFallbackRouterError):
    """Raised when LLM processing fails."""
    pass

@dataclass
class RouterResponse:
    """Structured response from the LLM Fallback Router."""
    intent: str
    parameters: Dict[str, Any]
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "intent": self.intent,
            "parameters": self.parameters,
            "reasoning": self.reasoning
        }

class LLMFallbackRouter:
    """
    LLM-powered fallback semantic router for VoucherBot.
    
    This router handles natural language queries that cannot be processed
    by the regex-based primary router, including edge cases, ambiguous
    language, and multilingual inputs.
    
    Supports:
    - English (en)
    - Spanish (es) 
    - Chinese (zh)
    - Bengali (bn)
    """
    
    # Enhanced Borough normalization mapping with multilingual support
    BOROUGH_MAPPING = {
        # English
        "bk": "Brooklyn",
        "brooklyn": "Brooklyn",
        "si": "Staten Island",
        "staten island": "Staten Island",
        "staten_island": "Staten Island",
        "qns": "Queens",
        "queens": "Queens",
        "bx": "Bronx",
        "bronx": "Bronx",
        "mnh": "Manhattan",
        "manhattan": "Manhattan",
        "nyc": None,  # Too vague
        "city": "Manhattan",  # Common NYC reference
        
        # Spanish
        "bronx": "Bronx",
        "brooklyn": "Brooklyn", 
        "manhattan": "Manhattan",
        "queens": "Queens",
        "isla staten": "Staten Island",
        "staten": "Staten Island",
        
        # Chinese
        "布朗克斯": "Bronx",
        "布鲁克林": "Brooklyn",
        "曼哈顿": "Manhattan", 
        "皇后区": "Queens",
        "史泰登岛": "Staten Island",
        "布朗士": "Bronx",  # Alternative spelling
        "皇后": "Queens",    # Short form
        
        # Bengali
        "ব্রংক্স": "Bronx",
        "ব্রুকলিন": "Brooklyn",
        "ম্যানহাটান": "Manhattan",
        "কুইন্স": "Queens", 
        "স্ট্যাটেন আইল্যান্ড": "Staten Island",
        "ব্রনক্স": "Bronx",  # Alternative spelling
    }
    
    # Enhanced Voucher type normalization mapping with multilingual support
    VOUCHER_MAPPING = {
        # English
        "section 8": "Section 8",
        "section eight": "Section 8",
        "section-8": "Section 8",
        "s8": "Section 8",
        "sec 8": "Section 8",
        "cityfheps": "CityFHEPS",
        "city fheps": "CityFHEPS",
        "cityfeps": "CityFHEPS",  # Common misspelling
        "hasa": "HASA",
        "housing voucher": "Housing Voucher",
        "voucher": "Housing Voucher",
        "hpd": "HPD",
        "dss": "DSS",
        "hra": "HRA",
        
        # Spanish
        "sección 8": "Section 8",
        "seccion 8": "Section 8",
        "vale de vivienda": "Housing Voucher",
        "voucher de vivienda": "Housing Voucher",
        "cupón de vivienda": "Housing Voucher",
        
        # Chinese 
        "住房券": "Housing Voucher",
        "第八条": "Section 8",
        "住房补助": "Housing Voucher",
        "租房券": "Housing Voucher",
        
        # Bengali
        "ভাউচার": "Housing Voucher",
        "হাউজিং ভাউচার": "Housing Voucher",
        "আবাসন ভাউচার": "Housing Voucher",
        "সেকশন ৮": "Section 8",
    }
    
    def __init__(self, llm_client: Any, debug: bool = False, max_retries: int = 3):
        """
        Initialize the LLM Fallback Router.
        
        Args:
            llm_client: An instance of an LLM interface (e.g., OpenAI or smolAI)
            debug: Enable debug logging
            max_retries: Maximum number of retry attempts for LLM calls
        """
        self.llm_client = llm_client
        self.debug = debug
        self.max_retries = max_retries
        
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("LLMFallbackRouter initialized in debug mode")
    
    def detect_languages(self, message: str) -> List[str]:
        """
        Detect languages present in the message.
        
        Args:
            message: Input message to analyze
            
        Returns:
            List of detected language codes
        """
        detected = []
        
        # English: Latin letters and English-specific patterns
        if re.search(r'[a-zA-Z]', message):
            detected.append('en')
            
        # Spanish: Spanish-specific characters and patterns
        if re.search(r'[áéíóúñ¿¡ü]', message) or any(word in message.lower() for word in ['pero', 'español', 'hola', 'ayuda', 'necesito']):
            detected.append('es')
            
        # Chinese: Chinese characters (CJK Unified Ideographs)
        if re.search(r'[\u4e00-\u9fff]', message):
            detected.append('zh')
            
        # Bengali: Bengali script
        if re.search(r'[\u0980-\u09FF]', message):
            detected.append('bn')
            
        return detected if detected else ['en']  # Default to English
    
    def format_prompt(self, message: str, context: Optional[str] = None, language: str = "en") -> str:
        """
        Format the prompt for the LLM with the given message and context.
        
        Args:
            message: User's message to route
            context: Optional context from previous messages or search state
            language: Language code for the user interface (en, es, zh, bn)
            
        Returns:
            Formatted prompt string
        """
        # Detect languages in the message
        detected_languages = self.detect_languages(message)
        
        # Language-specific prompt instructions
        language_instructions = {
            "en": "The user interface is in English. Respond appropriately to English queries.",
            "es": "La interfaz de usuario está en español. El usuario puede escribir en español, responde apropiadamente.",
            "zh": "用户界面是中文的。用户可能会用中文写消息，请适当回应。",
            "bn": "ব্যবহারকারী ইন্টারফেস বাংলায়। ব্যবহারকারী বাংলায় বার্তা লিখতে পারেন, উপযুক্তভাবে সাড়া দিন।"
        }
        
        # Language-specific examples for better understanding
        language_examples = {
            "en": [
                {"message": "I need help finding an apartment", "intent": "HELP_REQUEST"},
                {"message": "Show me listings in Brooklyn", "intent": "SEARCH_LISTINGS"},
                {"message": "What vouchers do you accept?", "intent": "ASK_VOUCHER_SUPPORT"}
            ],
            "es": [
                {"message": "Necesito ayuda para encontrar apartamento", "intent": "HELP_REQUEST"},
                {"message": "Busco apartamento en Brooklyn", "intent": "SEARCH_LISTINGS"},
                {"message": "¿Qué tipos de voucher aceptan?", "intent": "ASK_VOUCHER_SUPPORT"}
            ],
            "zh": [
                {"message": "我需要帮助找房子", "intent": "HELP_REQUEST"},
                {"message": "在布鲁克林找两居室", "intent": "SEARCH_LISTINGS"},
                {"message": "你们接受什么类型的住房券?", "intent": "ASK_VOUCHER_SUPPORT"}
            ],
            "bn": [
                {"message": "ভাউচার নিয়ে সাহায্য চাই", "intent": "HELP_REQUEST"},
                {"message": "ব্রুকলিনে অ্যাপার্টমেন্ট খুঁজছি", "intent": "SEARCH_LISTINGS"},
                {"message": "কি ধরনের ভাউচার গ্রহণ করেন?", "intent": "ASK_VOUCHER_SUPPORT"}
            ]
        }
        
        language_note = language_instructions.get(language, language_instructions["en"])
        examples = language_examples.get(language, language_examples["en"])
        
        # Add detected languages note if message contains multiple languages
        if len(detected_languages) > 1:
            language_note += f" Note: This message contains multiple languages: {', '.join(detected_languages)}. Handle accordingly."
        
        examples_str = "\n".join([f'- "{ex["message"]}" → {ex["intent"]}' for ex in examples])
        
        # Build the prompt with proper escaping
        context_str = f'"{context}"' if context else "null"
        
        prompt = f"""You are a semantic router and parameter extraction engine for a housing chatbot designed to help users find voucher-friendly listings in New York City.

LANGUAGE CONTEXT: {language_note}

EXAMPLES FOR THIS LANGUAGE:
{examples_str}

Your job is to:
1. Classify the **intent** of the user's message.
2. Extract **relevant search parameters** (if any).
3. Generate a short explanation of your reasoning.

You will be given:
- `message`: the user's latest message (string)
- `context`: optionally, a prior message or search state (string or null)

Your response must be a valid JSON object with the following schema:

{{
  "intent": one of [
    "SEARCH_LISTINGS",         
    "CHECK_VIOLATIONS",        
    "ASK_VOUCHER_SUPPORT",     
    "REFINE_SEARCH",           
    "FOLLOW_UP",               
    "HELP_REQUEST",            
    "UNKNOWN"                  
  ],
  
  "parameters": {{
    "borough": (string or null),        
    "bedrooms": (integer or null),      
    "max_rent": (integer or null),      
    "voucher_type": (string or null)    
  }},

  "reasoning": (string)   
}}

Guidelines:
- Normalize borough abbreviations: "BK" → "Brooklyn", etc.
- Support multilingual borough names: "布鲁克林" → "Brooklyn", "ব্রুকলিন" → "Brooklyn"
- Normalize voucher types: "section eight" → "Section 8", "sección 8" → "Section 8" 
- Handle mixed language inputs appropriately
- If the message is vague, return "UNKNOWN" intent and explain why.
- Format JSON precisely.

Input:
- Message: "{message}"
- Context: {context_str}

Response:"""
        
        return prompt
    
    def _validate_input(self, message: str, context: Optional[str] = None) -> None:
        """
        Validate input parameters.
        
        Args:
            message: User message to validate
            context: Optional context to validate
            
        Raises:
            InvalidInputError: If validation fails
        """
        if not message or not message.strip():
            raise InvalidInputError("Message cannot be empty or whitespace-only")
        
        if len(message.strip()) > 1000:  # Reasonable length limit
            raise InvalidInputError("Message exceeds maximum length of 1000 characters")
        
        if context is not None and len(context) > 2000:  # Context can be longer
            raise InvalidInputError("Context exceeds maximum length of 2000 characters")
    
    def _normalize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize extracted parameters to standard formats.
        
        Args:
            parameters: Raw parameters from LLM
            
        Returns:
            Normalized parameters
        """
        normalized = {}
        
        # Normalize borough
        if "borough" in parameters and parameters["borough"]:
            borough_lower = str(parameters["borough"]).lower().strip()
            normalized["borough"] = self.BOROUGH_MAPPING.get(borough_lower, parameters["borough"])
        else:
            normalized["borough"] = None
        
        # Normalize bedrooms
        if "bedrooms" in parameters and parameters["bedrooms"] is not None:
            try:
                bedrooms = int(parameters["bedrooms"])
                if 0 <= bedrooms <= 10:  # Reasonable range
                    normalized["bedrooms"] = bedrooms
                else:
                    normalized["bedrooms"] = None
            except (ValueError, TypeError):
                normalized["bedrooms"] = None
        else:
            normalized["bedrooms"] = None
        
        # Normalize max_rent
        if "max_rent" in parameters and parameters["max_rent"] is not None:
            try:
                max_rent = int(parameters["max_rent"])
                if 500 <= max_rent <= 15000:  # Reasonable range for NYC
                    normalized["max_rent"] = max_rent
                else:
                    normalized["max_rent"] = None
            except (ValueError, TypeError):
                normalized["max_rent"] = None
        else:
            normalized["max_rent"] = None
        
        # Normalize voucher_type
        if "voucher_type" in parameters and parameters["voucher_type"]:
            voucher_lower = str(parameters["voucher_type"]).lower().strip()
            normalized["voucher_type"] = self.VOUCHER_MAPPING.get(voucher_lower, parameters["voucher_type"])
        else:
            normalized["voucher_type"] = None
        
        return normalized
    
    def _validate_response(self, response_data: Dict[str, Any]) -> None:
        """
        Validate LLM response structure and content.
        
        Args:
            response_data: Parsed JSON response from LLM
            
        Raises:
            InvalidLLMResponseError: If response is invalid
        """
        # Check required fields
        required_fields = ["intent", "parameters", "reasoning"]
        for field in required_fields:
            if field not in response_data:
                raise InvalidLLMResponseError(f"Missing required field: {field}")
        
        # Validate intent
        intent = response_data["intent"]
        valid_intents = [intent_type.value for intent_type in IntentType]
        if intent not in valid_intents:
            raise InvalidLLMResponseError(f"Invalid intent: {intent}. Must be one of {valid_intents}")
        
        # Validate parameters structure
        parameters = response_data["parameters"]
        if not isinstance(parameters, dict):
            raise InvalidLLMResponseError("Parameters must be a dictionary")
        
        # Validate reasoning
        reasoning = response_data["reasoning"]
        if not isinstance(reasoning, str) or not reasoning.strip():
            raise InvalidLLMResponseError("Reasoning must be a non-empty string")
    
    def from_response(self, llm_response: str) -> RouterResponse:
        """
        Parse and validate LLM response into structured format.
        
        Args:
            llm_response: Raw response string from LLM
            
        Returns:
            RouterResponse object
            
        Raises:
            InvalidLLMResponseError: If response cannot be parsed or validated
        """
        try:
            # Try to extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', llm_response.strip(), re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = llm_response.strip()
            
            # Parse JSON
            response_data = json.loads(json_str)
            
            # Validate structure
            self._validate_response(response_data)
            
            # Normalize parameters
            normalized_params = self._normalize_parameters(response_data["parameters"])
            
            return RouterResponse(
                intent=response_data["intent"],
                parameters=normalized_params,
                reasoning=response_data["reasoning"].strip()
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {llm_response}")
            raise InvalidLLMResponseError(f"Invalid JSON in LLM response: {e}")
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}")
            raise InvalidLLMResponseError(f"Error processing response: {e}")
    
    def route(self, message: str, context: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
        """
        Route a user message using the LLM fallback router.
        
        Args:
            message: User's message to route
            context: Optional context from previous messages or search state
            language: Language code for the user interface (en, es, zh, bn)
            
        Returns:
            Dictionary with intent, parameters, and reasoning
            
        Raises:
            InvalidInputError: If input validation fails
            LLMProcessingError: If LLM processing fails
            InvalidLLMResponseError: If response parsing fails
        """
        # Validate input
        self._validate_input(message, context)
        
        if self.debug:
            logger.debug(f"Routing message: {message}")
            logger.debug(f"Context: {context}")
        
        # Format prompt
        prompt = self.format_prompt(message, context, language)
        
        # Call LLM with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if self.debug:
                    logger.debug(f"LLM call attempt {attempt + 1}/{self.max_retries}")
                
                # Call the LLM client
                # Note: This assumes the LLM client has a generate() or similar method
                # Adjust based on your specific LLM client interface
                if hasattr(self.llm_client, 'generate'):
                    llm_response = self.llm_client.generate(prompt)
                elif hasattr(self.llm_client, 'chat'):
                    llm_response = self.llm_client.chat(prompt)
                elif hasattr(self.llm_client, '__call__'):
                    llm_response = self.llm_client(prompt)
                else:
                    raise LLMProcessingError("LLM client does not have a recognized interface")
                
                if self.debug:
                    logger.debug(f"LLM response: {llm_response}")
                
                # Parse and validate response
                router_response = self.from_response(llm_response)
                
                if self.debug:
                    logger.debug(f"Parsed response: {router_response.to_dict()}")
                
                return router_response.to_dict()
                
            except InvalidLLMResponseError:
                # Don't retry for response parsing errors
                raise
            except Exception as e:
                last_error = e
                if self.debug:
                    logger.debug(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    continue  # Retry
                else:
                    break  # Max retries reached
        
        # If we get here, all retries failed
        error_msg = f"LLM processing failed after {self.max_retries} attempts"
        if last_error:
            error_msg += f". Last error: {last_error}"
        
        logger.error(error_msg)
        raise LLMProcessingError(error_msg)

# Convenience functions for backward compatibility and easy testing
def create_fallback_router(llm_client: Any, debug: bool = False) -> LLMFallbackRouter:
    """
    Create a new LLMFallbackRouter instance.
    
    Args:
        llm_client: LLM client instance
        debug: Enable debug mode
        
    Returns:
        LLMFallbackRouter instance
    """
    return LLMFallbackRouter(llm_client, debug=debug)

def route_message(llm_client: Any, message: str, context: Optional[str] = None, language: str = "en") -> Dict[str, Any]:
    """
    Convenience function to route a single message.
    
    Args:
        llm_client: LLM client instance
        message: Message to route
        context: Optional context
        language: Language code for the user interface
        
    Returns:
        Routing result dictionary
    """
    router = LLMFallbackRouter(llm_client)
    return router.route(message, context, language) 