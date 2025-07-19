#!/usr/bin/env python3
"""
MINIMAL FIX for Smolagents 1.19 - Just modify prompt templates
This is the least invasive change possible.
"""

import yaml
from agent_setup import initialize_caseworker_agent

def apply_minimal_fix():
    """Apply minimal fix by modifying prompt templates."""
    
    print("🔧 Applying minimal fix to prompt templates...")
    
    # 1. First, update the prompts.yaml file with better instructions
    try:
        with open("prompts.yaml", 'r') as f:
            prompts = yaml.safe_load(f)
    except FileNotFoundError:
        prompts = {}
    
    # 2. Add minimal fix to the system prompt template
    if "system_prompt" in prompts:
        # Just prepend the critical formatting rules
        critical_rules = """
CRITICAL: When writing code, never use 'py' as a variable name or statement. Write clean Python code directly.

CORRECT format example:
import json
address = "123 Main St"
result = geocode_address(address=address)
final_answer(result)

"""
        prompts["system_prompt"] = critical_rules + prompts["system_prompt"]
    else:
        # Create minimal system prompt
        prompts["system_prompt"] = """
CRITICAL: When writing code, never use 'py' as a variable name or statement. Write clean Python code directly.

You are a helpful NYC housing assistant. Use the available tools to help users find housing information.
Always call final_answer(your_response) at the end.
"""
    
    # 3. Save the updated prompts
    with open("prompts_fixed.yaml", 'w') as f:
        yaml.safe_dump(prompts, f)
    
    print("✅ Created prompts_fixed.yaml with minimal fixes")
    return prompts

def test_minimal_fix():
    """Test the minimal fix approach."""
    print("🧪 Testing Minimal Fix")
    print("=" * 30)
    
    # Apply the fix
    apply_minimal_fix()
    
    # Test by temporarily modifying the prompts.yaml file
    import shutil
    
    # Backup original
    try:
        shutil.copy("prompts.yaml", "prompts_backup.yaml")
        print("✅ Backed up original prompts.yaml")
    except FileNotFoundError:
        print("ℹ️ No existing prompts.yaml found")
    
    # Copy fixed version
    try:
        shutil.copy("prompts_fixed.yaml", "prompts.yaml")
        print("✅ Applied fixed prompts.yaml")
        
        # Initialize agent with fixed prompts
        agent = initialize_caseworker_agent()
        
        # Quick test
        test_query = "Calculate 10 + 15"
        print(f"\n🧪 Testing: {test_query}")
        
        result = agent.run(test_query)
        print(f"✅ Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    
    finally:
        # Restore original if it existed
        try:
            shutil.copy("prompts_backup.yaml", "prompts.yaml")
            print("✅ Restored original prompts.yaml")
        except FileNotFoundError:
            print("ℹ️ No backup to restore")

if __name__ == "__main__":
    success = test_minimal_fix()
    if success:
        print("\n🎉 Minimal fix test completed!")
        print("To apply permanently: cp prompts_fixed.yaml prompts.yaml")
    else:
        print("\n⚠️ Minimal fix needs adjustment") 