#!/usr/bin/env python3
"""
MONKEY PATCH FIX for Smolagents 1.19
Directly patches the code parsing to handle both formats.
"""

import re
import smolagents.agents
from agent_setup import initialize_caseworker_agent

def patch_smolagents_code_parser():
    """Monkey patch Smolagents to handle multiple code formats."""
    
    print("🔧 Applying monkey patch to Smolagents code parser...")
    
    # Find the CodeAgent class
    if hasattr(smolagents.agents, 'CodeAgent'):
        CodeAgent = smolagents.agents.CodeAgent
        
        # Store original method if not already patched
        if not hasattr(CodeAgent, '_original_extract_code'):
            if hasattr(CodeAgent, 'extract_code_from_text'):
                CodeAgent._original_extract_code = CodeAgent.extract_code_from_text
            elif hasattr(CodeAgent, '_parse_code'):
                CodeAgent._original_extract_code = CodeAgent._parse_code
            else:
                # Find any method that handles code extraction
                for attr_name in dir(CodeAgent):
                    attr = getattr(CodeAgent, attr_name)
                    if callable(attr) and ('code' in attr_name.lower() or 'extract' in attr_name.lower()):
                        print(f"Found potential code method: {attr_name}")
        
        # Patch the code extraction to handle multiple formats
        def enhanced_code_parser(self, text):
            """Enhanced code parser that handles multiple formats."""
            
            # Try original <code> format first
            code_pattern_1 = r'<code>(.*?)</code>'
            match = re.search(code_pattern_1, text, re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # Try ```python format
            code_pattern_2 = r'```python\\n(.*?)\\n```'
            match = re.search(code_pattern_2, text, re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # Try ```py format
            code_pattern_3 = r'```py\\n(.*?)\\n```'
            match = re.search(code_pattern_3, text, re.DOTALL)
            if match:
                return match.group(1).strip()
            
            # Try ``` format (generic)
            code_pattern_4 = r'```\\n(.*?)\\n```'
            match = re.search(code_pattern_4, text, re.DOTALL)
            if match:
                code = match.group(1).strip()
                # Basic Python detection
                if any(keyword in code for keyword in ['import ', 'def ', 'final_answer', 'geocode_address']):
                    return code
            
            # If none found, return None to trigger original behavior
            return None
        
        # Apply the patch to the right method
        if hasattr(CodeAgent, 'extract_code_from_text'):
            original_method = CodeAgent.extract_code_from_text
            
            def patched_extract_code(self, text):
                enhanced_code = enhanced_code_parser(self, text)
                if enhanced_code is not None:
                    return enhanced_code
                return original_method(self, text)
            
            CodeAgent.extract_code_from_text = patched_extract_code
            print("✅ Patched extract_code_from_text")
            
        elif hasattr(CodeAgent, '_parse_code'):
            original_method = CodeAgent._parse_code
            
            def patched_parse_code(self, text):
                enhanced_code = enhanced_code_parser(self, text)
                if enhanced_code is not None:
                    return enhanced_code
                return original_method(self, text)
            
            CodeAgent._parse_code = patched_parse_code
            print("✅ Patched _parse_code")
        
        else:
            print("⚠️ Could not find code parsing method to patch")
            return False
        
        print("✅ Smolagents monkey patch applied successfully!")
        return True
    else:
        print("❌ CodeAgent not found in smolagents.agents")
        return False

def test_monkey_patch():
    """Test the monkey patch fix."""
    print("🧪 Testing Monkey Patch Fix")
    print("=" * 40)
    
    # Apply the patch
    success = patch_smolagents_code_parser()
    if not success:
        print("❌ Patch failed - cannot continue test")
        return False
    
    # Test with a simple query
    print("\\n🔧 Initializing agent with monkey patch...")
    agent = initialize_caseworker_agent()
    
    print("\\n🧪 Testing school query...")
    try:
        result = agent.run("What is the nearest school to East 195th Street, Bronx, NY?", max_steps=5)
        print(f"✅ Result: {result[:300]}...")
        return True
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False

if __name__ == "__main__":
    success = test_monkey_patch()
    if success:
        print("\\n🎉 Monkey patch test completed!")
        print("\\n📝 To apply permanently, import this at the top of your app.py:")
        print("from monkey_patch_fix import patch_smolagents_code_parser")
        print("patch_smolagents_code_parser()")
    else:
        print("\\n⚠️ Monkey patch needs adjustment") 