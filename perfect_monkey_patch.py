#!/usr/bin/env python3
"""
PERFECT MONKEY PATCH for Smolagents 1.19
Patches the exact function causing the code parsing error.
"""

import re
import ast
from textwrap import dedent
import smolagents.utils
from agent_setup import initialize_caseworker_agent

def enhanced_parse_code_blobs(text: str) -> str:
    """
    Enhanced version of parse_code_blobs that handles multiple code formats.
    
    This replaces the original function to support both:
    - <code>python_code</code> (original format)
    - ```python\\npython_code\\n``` (markdown format)
    - ```py\\npython_code\\n``` (short markdown format)
    """
    
    # Try original <code> format first
    matches = smolagents.utils._original_extract_code_from_text(text)
    if matches:
        return matches
    
    # Try ```python format
    python_pattern = r"```python\s*\n(.*?)\n```"
    python_matches = re.findall(python_pattern, text, re.DOTALL)
    if python_matches:
        return "\n\n".join(match.strip() for match in python_matches)
    
    # Try ```py format  
    py_pattern = r"```py\s*\n(.*?)\n```"
    py_matches = re.findall(py_pattern, text, re.DOTALL)
    if py_matches:
        return "\n\n".join(match.strip() for match in py_matches)
    
    # Try generic ``` format (with Python detection)
    generic_pattern = r"```\s*\n(.*?)\n```"
    generic_matches = re.findall(generic_pattern, text, re.DOTALL)
    for match in generic_matches:
        # Basic Python detection
        if any(keyword in match for keyword in ['import ', 'def ', 'final_answer', 'geocode_address', '=']):
            return match.strip()
    
    # Maybe the LLM outputted a code blob directly
    try:
        ast.parse(text)
        return text
    except SyntaxError:
        pass

    # Enhanced error messages that guide towards the correct format
    if "final" in text and "answer" in text:
        raise ValueError(
            dedent(
                f"""
                Your code snippet is invalid. Please use one of these formats:
                
                Format 1 (preferred):
                <code>
                final_answer("YOUR FINAL ANSWER HERE")
                </code>
                
                Format 2 (also supported):
                ```python
                final_answer("YOUR FINAL ANSWER HERE")
                ```
                
                Your output was:
                {text}
                """
            ).strip()
        )
    
    raise ValueError(
        dedent(
            f"""
            Your code snippet is invalid. Please use one of these formats:
            
            Format 1 (preferred):
            <code>
            # Your python code here
            final_answer("result")
            </code>
            
            Format 2 (also supported):
            ```python
            # Your python code here  
            final_answer("result")
            ```
            
            Your output was:
            {text}
            """
        ).strip()
    )

def enhanced_extract_code_from_text(text: str) -> str | None:
    """Enhanced extract_code_from_text that handles multiple formats."""
    
    # Try original <code> format first
    pattern = r"<code>(.*?)</code>"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return "\n\n".join(match.strip() for match in matches)
    
    # Try ```python format
    python_pattern = r"```python\s*\n(.*?)\n```"
    python_matches = re.findall(python_pattern, text, re.DOTALL)
    if python_matches:
        return "\n\n".join(match.strip() for match in python_matches)
        
    # Try ```py format
    py_pattern = r"```py\s*\n(.*?)\n```"
    py_matches = re.findall(py_pattern, text, re.DOTALL)
    if py_matches:
        return "\n\n".join(match.strip() for match in py_matches)
    
    return None

def apply_perfect_monkey_patch():
    """Apply the perfect monkey patch to fix Smolagents 1.19 code parsing."""
    
    print("🔧 Applying perfect monkey patch to Smolagents 1.19...")
    
    # Store original functions if not already patched
    if not hasattr(smolagents.utils, '_original_parse_code_blobs'):
        smolagents.utils._original_parse_code_blobs = smolagents.utils.parse_code_blobs
        smolagents.utils._original_extract_code_from_text = smolagents.utils.extract_code_from_text
        
        # Apply patches
        smolagents.utils.parse_code_blobs = enhanced_parse_code_blobs
        smolagents.utils.extract_code_from_text = enhanced_extract_code_from_text
        
        print("✅ Successfully patched parse_code_blobs and extract_code_from_text")
        print("✅ Now supports both <code> and ```python formats!")
        return True
    else:
        print("ℹ️ Patch already applied")
        return True

def test_perfect_patch():
    """Test the perfect monkey patch."""
    print("🧪 Testing Perfect Monkey Patch")
    print("=" * 45)
    
    # Apply the patch
    success = apply_perfect_monkey_patch()
    if not success:
        return False
    
    # Test the patched functions directly
    print("\\n🔧 Testing patched functions...")
    
    # Test 1: <code> format (should work)
    test1 = '<code>final_answer("Hello World")</code>'
    try:
        result1 = smolagents.utils.parse_code_blobs(test1)
        print(f"✅ <code> format: {result1}")
    except Exception as e:
        print(f"❌ <code> format failed: {e}")
    
    # Test 2: ```python format (should now work!)
    test2 = '```python\\nfinal_answer("Hello World")\\n```'
    try:
        result2 = smolagents.utils.parse_code_blobs(test2)
        print(f"✅ ```python format: {result2}")
    except Exception as e:
        print(f"❌ ```python format failed: {e}")
    
    # Test 3: With actual agent
    print("\\n🤖 Testing with actual agent...")
    try:
        agent = initialize_caseworker_agent()
        result = agent.run("What is 5 + 3?", max_steps=3)
        print(f"✅ Agent test result: {result}")
        return True
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_perfect_patch()
    if success:
        print("\\n🎉 Perfect monkey patch test completed!")
        print("\\n📝 To apply permanently, add this to the top of your app.py:")
        print("from perfect_monkey_patch import apply_perfect_monkey_patch")
        print("apply_perfect_monkey_patch()")
    else:
        print("\\n⚠️ Perfect monkey patch needs adjustment") 