#!/usr/bin/env python3
"""
Quick Fix for Smolagents 1.19 Code Parsing Issue
Addresses the regex pattern <code>(.*?)</code> error
"""

from smolagents import CodeAgent, InferenceClientModel
from agent_setup import initialize_caseworker_agent
import re

class SmolagentsCodeFixer:
    """Fixes code parsing issues in Smolagents 1.19."""
    
    @staticmethod
    def fix_code_format(agent_response: str) -> str:
        """
        Fix the code format to match what Smolagents 1.19 expects.
        Wraps code blocks in the expected <code></code> tags.
        """
        # Pattern to find Python code blocks
        code_pattern = r'```python\n(.*?)\n```'
        
        def replace_code_block(match):
            code_content = match.group(1)
            return f'<code>\n{code_content}\n</code>'
        
        # Replace markdown code blocks with <code> tags
        fixed_response = re.sub(code_pattern, replace_code_block, agent_response, flags=re.DOTALL)
        
        # Also handle plain ``` blocks
        plain_code_pattern = r'```\n(.*?)\n```'
        fixed_response = re.sub(plain_code_pattern, replace_code_block, fixed_response, flags=re.DOTALL)
        
        return fixed_response
    
    @staticmethod
    def wrap_agent_run(agent, query: str):
        """
        Wrapper that fixes the agent's response format before processing.
        """
        try:
            # Monkey patch the agent's model to fix output format
            original_model_call = agent.model
            
            class FixedModel:
                def __init__(self, original_model):
                    self.original_model = original_model
                    for attr in dir(original_model):
                        if not attr.startswith('_') and attr != '__call__':
                            setattr(self, attr, getattr(original_model, attr))
                
                def __call__(self, *args, **kwargs):
                    response = self.original_model(*args, **kwargs)
                    # Fix the response format
                    if hasattr(response, 'content'):
                        response.content = SmolagentsCodeFixer.fix_code_format(response.content)
                    elif isinstance(response, str):
                        response = SmolagentsCodeFixer.fix_code_format(response)
                    return response
            
            # Temporarily replace the model
            agent.model = FixedModel(original_model_call)
            
            # Run the agent
            result = agent.run(query)
            
            # Restore original model
            agent.model = original_model_call
            
            return result
            
        except Exception as e:
            print(f"Error in fixed agent run: {e}")
            # Fallback to original agent
            return agent.run(query)

def test_fixed_agent():
    """Test the fixed agent setup."""
    print("🔧 Testing Fixed Smolagents 1.19 Setup")
    print("=" * 50)
    
    # Initialize your agent
    agent = initialize_caseworker_agent()
    
    # Test queries
    test_queries = [
        "What's the nearest school to East 195th Street, Bronx, NY?",
        "Find the nearest subway station to 350 East 62nd Street, Manhattan",
        "Calculate 15 + 25"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: {query}")
        try:
            # Use the fixed wrapper
            result = SmolagentsCodeFixer.wrap_agent_run(agent, query)
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

# Alternative: Direct regex fix for your existing code
def patch_smolagents_parser():
    """
    Monkey patch Smolagents to handle different code formats.
    Apply this before initializing your agent.
    """
    import smolagents.agents
    
    # Store original parse function
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
                # Wrap in expected format
                fixed_text = f'<code>\n{match.group(1)}\n</code>'
                return original_parse(fixed_text)
            
            # Handle inline code with backticks
            inline_pattern = r'`([^`]+)`'
            match = re.search(inline_pattern, text)
            if match:
                fixed_text = f'<code>\n{match.group(1)}\n</code>'
                return original_parse(fixed_text)
            
            # Fallback to original
            return original_parse(text)
        
        # Replace the function
        setattr(smolagents.agents, attr_name, fixed_parse_code)
        print("✅ Smolagents code parser patched successfully!")

if __name__ == "__main__":
    # Apply the patch first
    patch_smolagents_parser()
    
    # Test the fixed agent
    test_fixed_agent() 