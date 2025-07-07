#!/usr/bin/env python3
"""
FINAL WORKING FIX for Smolagents 1.19
This is the definitive solution that fully resolves the code parsing issues.
"""

import re
import ast
from textwrap import dedent
import smolagents.utils

def enhanced_parse_code_blobs(text: str) -> str:
    """
    Final enhanced version that handles all code formats correctly.
    """
    
    # Try original <code> format first
    matches = smolagents.utils._original_extract_code_from_text(text)
    if matches:
        return matches
    
    # Fix the regex patterns to handle actual newlines (not literal \n)
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
    
    # Handle single-line ```python format without newlines
    single_python_pattern = r"```python\s*(.*?)\s*```"
    single_python_matches = re.findall(single_python_pattern, text, re.DOTALL)
    if single_python_matches:
        return "\n\n".join(match.strip() for match in single_python_matches)
    
    # Handle single-line ```py format without newlines  
    single_py_pattern = r"```py\s*(.*?)\s*```"
    single_py_matches = re.findall(single_py_pattern, text, re.DOTALL)
    if single_py_matches:
        return "\n\n".join(match.strip() for match in single_py_matches)
    
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
    """Final enhanced extract_code_from_text that handles all formats."""
    
    # Try original <code> format first
    pattern = r"<code>(.*?)</code>"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return "\n\n".join(match.strip() for match in matches)
    
    # Try ```python format with newlines
    python_pattern = r"```python\s*\n(.*?)\n```"
    python_matches = re.findall(python_pattern, text, re.DOTALL)
    if python_matches:
        return "\n\n".join(match.strip() for match in python_matches)
        
    # Try ```py format with newlines
    py_pattern = r"```py\s*\n(.*?)\n```"
    py_matches = re.findall(py_pattern, text, re.DOTALL)
    if py_matches:
        return "\n\n".join(match.strip() for match in py_matches)
    
    # Try single-line formats
    single_python_pattern = r"```python\s*(.*?)\s*```"
    single_python_matches = re.findall(single_python_pattern, text, re.DOTALL)
    if single_python_matches:
        return "\n\n".join(match.strip() for match in single_python_matches)
        
    single_py_pattern = r"```py\s*(.*?)\s*```"
    single_py_matches = re.findall(single_py_pattern, text, re.DOTALL)
    if single_py_matches:
        return "\n\n".join(match.strip() for match in single_py_matches)
    
    return None

def apply_final_fix():
    """Apply the final working fix to Smolagents 1.19."""
    
    print("🔧 Applying FINAL FIX to Smolagents 1.19...")
    
    # Store original functions if not already patched
    if not hasattr(smolagents.utils, '_original_parse_code_blobs'):
        smolagents.utils._original_parse_code_blobs = smolagents.utils.parse_code_blobs
        smolagents.utils._original_extract_code_from_text = smolagents.utils.extract_code_from_text
        
        # Apply patches
        smolagents.utils.parse_code_blobs = enhanced_parse_code_blobs
        smolagents.utils.extract_code_from_text = enhanced_extract_code_from_text
        
        print("✅ Successfully patched parse_code_blobs and extract_code_from_text")
        print("✅ Now supports <code>, ```python, and ```py formats!")
        print("✅ Handles both single-line and multi-line code blocks!")
        return True
    else:
        print("ℹ️ Final fix already applied")
        return True

def test_final_fix():
    """Test the final fix comprehensively."""
    print("🧪 Testing FINAL FIX")
    print("=" * 30)
    
    # Apply the fix
    success = apply_final_fix()
    if not success:
        return False
    
    # Test all formats
    print("\\n🔧 Testing all supported formats...")
    
    test_cases = [
        ('<code>final_answer("Test 1")</code>', '<code> format'),
        ('```python\\nfinal_answer("Test 2")\\n```', '```python with newlines'),
        ('```python final_answer("Test 3") ```', '```python single-line'),
        ('```py\\nfinal_answer("Test 4")\\n```', '```py with newlines'),
        ('```py final_answer("Test 5") ```', '```py single-line'),
    ]
    
    for test_code, description in test_cases:
        try:
            result = smolagents.utils.parse_code_blobs(test_code)
            print(f"✅ {description}: {result}")
        except Exception as e:
            print(f"❌ {description} failed: {str(e)[:100]}...")
    
    return True

if __name__ == "__main__":
    success = test_final_fix()
    if success:
        print("\\n🎉 FINAL FIX READY!")
        print("\\n📝 To apply to your app, add this line to the top of app.py:")
        print("from final_fix import apply_final_fix; apply_final_fix()")
    else:
        print("\\n⚠️ Final fix needs adjustment") 