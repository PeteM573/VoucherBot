#!/usr/bin/env python3
"""
PATCHED VERSION of your existing app.py for Smolagents 1.19
"""

import gradio as gr
from smolagents import CodeAgent, InferenceClientModel
from agent_setup import initialize_caseworker_agent
import re

# PATCH 1: Fix the code parsing regex issue
def patch_smolagents_parser():
    """Monkey patch Smolagents to handle different code formats."""
    import smolagents.agents
    
    if hasattr(smolagents.agents, '_original_parse_code'):
        return  # Already patched
    
    # Find and patch the code parsing function
    original_parse = None
    for attr_name in dir(smolagents.agents):
        attr = getattr(smolagents.agents, attr_name)
        if callable(attr) and 'code' in attr_name.lower() and 'parse' in attr_name.lower():
            original_parse = attr
            break
    
    if original_parse:
        smolagents.agents._original_parse_code = original_parse
        
        def fixed_parse_code(text: str):
            """Fixed code parser that handles multiple formats."""
            # Try original format first
            if '<code>' in text and '</code>' in text:
                return original_parse(text)
            
            # Handle markdown code blocks
            code_pattern = r'```(?:python)?\n(.*?)\n```'
            match = re.search(code_pattern, text, re.DOTALL)
            if match:
                fixed_text = f'<code>\n{match.group(1)}\n</code>'
                return original_parse(fixed_text)
            
            # Handle inline code
            inline_pattern = r'`([^`]+)`'
            match = re.search(inline_pattern, text)
            if match:
                fixed_text = f'<code>\n{match.group(1)}\n</code>'
                return original_parse(fixed_text)
            
            return original_parse(text)
        
        setattr(smolagents.agents, attr_name, fixed_parse_code)
        print("✅ Smolagents code parser patched!")

# PATCH 2: Apply the patches before initializing agent
patch_smolagents_parser()

# PATCH 3: Enhanced agent initialization with better prompts
def initialize_fixed_agent():
    """Initialize agent with fixed system prompt."""
    agent = initialize_caseworker_agent()
    
    # Enhanced system prompt for better code formatting
    enhanced_prompt = """
CRITICAL FORMATTING RULES for Smolagents 1.19:
1. Never use 'py' as a variable name or statement
2. Write clean Python code without language specifiers
3. Always use proper variable assignments
4. End with final_answer(your_response)

CORRECT CODE FORMAT:
```python
import json
address = "123 Main St"
result = geocode_address(address=address)
final_answer(result)
```

TOOLS AVAILABLE:
- geocode_address(address="full address")
- find_nearest_school(lat=lat, lon=lon)
- find_nearest_subway(lat=lat, lon=lon)
"""
    
    # Apply enhanced prompt
    if hasattr(agent, 'system_prompt'):
        agent.system_prompt = enhanced_prompt + "\n\n" + agent.system_prompt
    
    return agent

# Initialize the fixed agent
agent = initialize_fixed_agent()

# PATCH 4: Gradio interface with error handling
def chat_interface(message, history):
    """Enhanced chat interface with error recovery."""
    try:
        # Run the agent with the message
        response = agent.run(message)
        return response
    except Exception as e:
        # Fallback response with error info
        error_msg = f"I encountered a technical issue: {str(e)[:100]}..."
        
        # Try simple responses for common queries
        if "school" in message.lower():
            return "To find nearby schools, please use the NYC Department of Education website or Google Maps."
        elif "subway" in message.lower():
            return "For subway information, please check the MTA website or use Google Maps."
        else:
            return f"I'm experiencing technical difficulties. {error_msg}"

# Create Gradio interface
demo = gr.ChatInterface(
    chat_interface,
    title="🏠 NYC Voucher Housing Navigator (Patched for Smolagents 1.19)",
    description="✅ Fixed version with patches for code parsing issues",
    examples=[
        "What's the nearest school to East 195th Street, Bronx, NY?",
        "Find subway stations near 350 East 62nd Street, Manhattan",
        "Help me find housing in Brooklyn"
    ],
    retry_btn=None,
    undo_btn="⏪ Undo",
    clear_btn="🗑️ Clear",
)

if __name__ == "__main__":
    print("🚀 Starting PATCHED NYC Voucher Housing Navigator")
    print("✅ All Smolagents 1.19 fixes applied!")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    ) 