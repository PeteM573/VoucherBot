#!/usr/bin/env python3
"""
ULTRA MINIMAL FIX: Just add the correct code format to prompts.yaml
This is the absolute smallest change possible.
"""

import yaml
import os

def apply_ultra_minimal_fix():
    """Add only the essential code format fix to prompts.yaml"""
    
    print("🔧 Applying ultra-minimal code format fix...")
    
    # Check if prompts.yaml exists
    if os.path.exists("prompts.yaml"):
        with open("prompts.yaml", 'r') as f:
            prompts = yaml.safe_load(f) or {}
    else:
        prompts = {}
    
    # The ONLY fix needed: Add the correct code format instruction
    code_format_fix = """
IMPORTANT: When writing code, use this EXACT format:

<code>
your_python_code_here
</code>

Never use ```py or ```python - only use <code> tags.
"""
    
    # Add to system prompt if it exists, otherwise create it
    if "system_prompt" in prompts:
        prompts["system_prompt"] = code_format_fix + "\n" + prompts["system_prompt"]
    else:
        prompts["system_prompt"] = code_format_fix + """
You are a helpful NYC housing assistant. Use the available tools to help users find housing information.
Always call final_answer(your_response) at the end."""
    
    # Save the fixed version
    with open("prompts_ultrafix.yaml", 'w') as f:
        yaml.safe_dump(prompts, f)
    
    print("✅ Created prompts_ultrafix.yaml with minimal code format fix")
    return True

def test_ultra_minimal():
    """Test the ultra minimal fix"""
    print("🧪 Testing Ultra-Minimal Fix")
    print("=" * 35)
    
    apply_ultra_minimal_fix()
    
    print("\n📝 To apply this fix:")
    print("1. cp prompts_ultrafix.yaml prompts.yaml")
    print("2. Restart your app: python3 app.py")
    print("\n🔄 To revert:")
    print("1. rm prompts.yaml  # (if no original existed)")
    print("2. Or restore your original prompts.yaml")
    
    print("\n✅ Ultra-minimal fix ready!")
    print("This only adds the correct <code> format instruction.")

if __name__ == "__main__":
    test_ultra_minimal() 