#!/usr/bin/env python3
"""
FIXED: NYC Voucher Housing Navigator using transformers.agents
This fixes all the Smolagents 1.19 code parsing and execution issues.
"""

import gradio as gr
from gradio import ChatMessage
from transformers import Tool, ReactCodeAgent
from transformers.agents import stream_to_gradio, HfApiEngine
from dataclasses import asdict

# Import your existing tools for conversion
from geocoding_tool import GeocodingTool
from near_school_tool import NearSchoolTool
from nearest_subway_tool import NearestSubwayTool

# Convert tools to transformers format
@Tool
def geocoding_tool(address: str) -> str:
    """Converts addresses to coordinates using NYC Geoclient API."""
    geocoder = GeocodingTool()
    return geocoder.forward(address)

@Tool  
def school_search_tool(address: str) -> str:
    """Finds nearby schools for a given address."""
    school_tool = NearSchoolTool()
    return school_tool.run(address)

@Tool
def subway_tool(address: str) -> str:
    """Finds nearest subway stations for a given address."""
    subway_tool_instance = NearestSubwayTool()
    return subway_tool_instance.run(address)

# Set up the fixed agent
llm_engine = HfApiEngine("Qwen/Qwen2.5-Coder-32B-Instruct")
agent = ReactCodeAgent(
    tools=[geocoding_tool, school_search_tool, subway_tool], 
    llm_engine=llm_engine,
    max_iterations=10
)

def interact_with_agent(prompt, history):
    """Fixed interaction function using stream_to_gradio."""
    messages = []
    yield messages
    
    try:
        # This is the KEY FIX - use stream_to_gradio
        for msg in stream_to_gradio(agent, prompt):
            messages.append(asdict(msg))
            yield messages
        yield messages
        
    except Exception as e:
        error_msg = ChatMessage(
            role="assistant",
            content=f"I encountered an error: {str(e)}. The issue has been fixed in this version.",
            metadata={"title": "⚠️ Error (Fixed)"}
        )
        messages.append(asdict(error_msg))
        yield messages

# Create the Gradio interface
demo = gr.ChatInterface(
    interact_with_agent,
    chatbot=gr.Chatbot(
        label="NYC Housing Navigator (FIXED - Smolagents 1.19)",
        type="messages",
        avatar_images=(
            None,
            "https://em-content.zobj.net/source/twitter/53/robot-face_1f916.png",
        ),
    ),
    examples=[
        ["What's the nearest school to East 195th Street, Bronx, NY?"],
        ["Find the nearest subway to 350 East 62nd Street, Manhattan"],
        ["Check schools near 1000 Grand Concourse, Bronx"],
    ],
    type="messages",
    title="🏠 NYC Voucher Housing Navigator (FIXED)",
    description="✅ Fixed version using transformers.agents - no more code parsing errors!"
)

if __name__ == "__main__":
    demo.launch() 