#!/usr/bin/env python3
"""
Example integration of the human handoff detection system.
Shows how to use the handoff detector in the main app flow.
"""

from typing import Dict, Any
from .handoff_detector import HandoffDetector, final_answer

class ChatHandler:
    """Example chat handler showing handoff integration."""
    
    def __init__(self):
        self.handoff_detector = HandoffDetector()
        self.context = {}  # Store user context
    
    def handle_message(self, message: str) -> Dict[str, Any]:
        """
        Handle an incoming chat message.
        Shows how handoff detection integrates with normal chat flow.
        """
        # First check for handoff triggers
        needs_handoff, reason, contact_info = self.handoff_detector.detect_handoff(
            message, 
            self.context
        )
        
        if needs_handoff:
            # Format and return handoff message
            response_text = self.handoff_detector.format_handoff_message(
                reason,
                contact_info
            )
            return final_answer(response_text)
        
        # If no handoff needed, continue with normal message handling
        return self._handle_normal_message(message)
    
    def _handle_normal_message(self, message: str) -> Dict[str, Any]:
        """
        Handle non-handoff messages (search, info requests, etc.)
        This is just an example - replace with your actual message handling.
        """
        # Your normal message handling logic here
        return {
            "response": "Normal message handling response...",
            "metadata": {
                "requires_human_handoff": False
            }
        }

def example_usage():
    """Example showing how to use the chat handler."""
    handler = ChatHandler()
    
    # Example: Normal search message
    result = handler.handle_message("Show me apartments in Brooklyn")
    print("Search message response:", result)
    assert not result["metadata"]["requires_human_handoff"]
    
    # Example: User requests human help
    result = handler.handle_message("Can I talk to a caseworker?")
    print("\nHandoff message response:", result)
    assert result["metadata"]["requires_human_handoff"]
    
    # Example: Discrimination case
    result = handler.handle_message("The landlord said they don't accept vouchers")
    print("\nDiscrimination case response:", result)
    assert result["metadata"]["requires_human_handoff"]

if __name__ == "__main__":
    example_usage() 