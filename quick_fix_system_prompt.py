#!/usr/bin/env python3
"""
Quick System Prompt Fix for Smolagents 1.19
Modifies the system prompt to fix code formatting issues.
"""

from agent_setup import initialize_caseworker_agent

def apply_system_prompt_fix():
    """Apply a system prompt fix for Smolagents 1.19 code formatting."""
    
    # Initialize your agent
    agent = initialize_caseworker_agent()
    
    # Add fixed system prompt instructions
    FIXED_SYSTEM_PROMPT = """
You are a helpful NYC housing assistant. When you need to execute code, ALWAYS format it properly:

CRITICAL: Never use 'py' as a variable name or statement. Instead, write clean Python code directly.

CORRECT format:
```python
result = calculate_something()
final_answer(result)
```

WRONG format (DO NOT USE):
py
result = calculate_something()  # This will cause errors!

When using tools:
- Use geocode_address(address="full address") for geocoding
- Use find_nearest_school(lat=lat, lon=lon) for schools  
- Use find_nearest_subway(lat=lat, lon=lon) for subways
- Always call final_answer(your_response) at the end

Example of correct usage:
```python
import json
address = "123 Main St, Bronx, NY"
geocode_result = geocode_address(address=address)
geocode_data = json.loads(geocode_result)
if geocode_data["status"] == "success":
    lat = geocode_data["data"]["latitude"]
    lon = geocode_data["data"]["longitude"]
    school_result = find_nearest_school(lat=lat, lon=lon)
    final_answer(f"Found schools near {address}")
```
"""
    
    # Apply the fix to the agent's system prompt
    if hasattr(agent, 'system_prompt'):
        agent.system_prompt = FIXED_SYSTEM_PROMPT + "\n\n" + agent.system_prompt
    elif hasattr(agent, '_system_prompt'):
        agent._system_prompt = FIXED_SYSTEM_PROMPT + "\n\n" + agent._system_prompt
    
    print("✅ System prompt fix applied!")
    return agent

def test_system_prompt_fix():
    """Test the system prompt fix."""
    print("🔧 Testing System Prompt Fix")
    print("=" * 40)
    
    agent = apply_system_prompt_fix()
    
    # Test query
    query = "What's the nearest school to East 195th Street, Bronx, NY?"
    print(f"Testing: {query}")
    
    try:
        result = agent.run(query)
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_system_prompt_fix() 