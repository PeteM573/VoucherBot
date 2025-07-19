#!/usr/bin/env python3
"""
Updated Agent Setup using transformers.agents
Fixes the code parsing regex issues in Smolagents 1.19
"""

import gradio as gr
from gradio import ChatMessage
from transformers import Tool, ReactCodeAgent
from transformers.agents import stream_to_gradio, HfApiEngine
from dataclasses import asdict

# Import your existing tools
from geocoding_tool import GeocodingTool
from near_school_tool import NearSchoolTool
from nearest_subway_tool import NearestSubwayTool
from violation_checker_agent import ViolationCheckerAgent

class TransformersAgentSetup:
    """Fixed agent setup using transformers.agents framework."""
    
    def __init__(self):
        self.setup_tools()
        self.setup_agent()
    
    def setup_tools(self):
        """Convert your existing tools to transformers.Tool format."""
        
        # Geocoding tool wrapper
        @Tool.from_space(
            space_id="your-geocoding-space",  # Replace with actual space
            name="geocoding_tool", 
            description="Converts addresses to coordinates using NYC Geoclient API."
        )
        def geocoding_wrapper(address: str) -> str:
            geocoder = GeocodingTool()
            return geocoder.forward(address)
        
        # School search tool wrapper  
        @Tool.from_space(
            space_id="your-school-space",  # Replace with actual space
            name="school_search_tool",
            description="Finds nearby schools for a given address."
        )
        def school_search_wrapper(address: str) -> str:
            school_tool = NearSchoolTool()
            return school_tool.run(address)
        
        # Subway tool wrapper
        @Tool.from_space(
            space_id="your-subway-space",  # Replace with actual space
            name="subway_tool",
            description="Finds nearest subway stations for a given address."
        )
        def subway_wrapper(address: str) -> str:
            subway_tool = NearestSubwayTool() 
            return subway_tool.run(address)
        
        self.tools = [geocoding_wrapper, school_search_wrapper, subway_wrapper]
    
    def setup_agent(self):
        """Setup the ReactCodeAgent with proper configuration."""
        
        # Use HfApiEngine instead of direct model
        llm_engine = HfApiEngine("Qwen/Qwen2.5-Coder-32B-Instruct")
        
        # Create ReactCodeAgent (this fixes the code parsing issues)
        self.agent = ReactCodeAgent(
            tools=self.tools, 
            llm_engine=llm_engine,
            max_iterations=10,
            verbosity_level=2
        )
    
    def interact_with_agent(self, prompt, history):
        """
        Fixed interaction function that properly streams responses.
        This uses the stream_to_gradio function to avoid code parsing issues.
        """
        messages = []
        yield messages
        
        try:
            # Use stream_to_gradio to properly handle code execution
            for msg in stream_to_gradio(self.agent, prompt):
                messages.append(asdict(msg))
                yield messages
            yield messages
            
        except Exception as e:
            # Fallback with error handling
            error_msg = ChatMessage(
                role="assistant",
                content=f"I encountered an error: {str(e)}. Let me try a different approach.",
                metadata={"title": "⚠️ Error Recovery"}
            )
            messages.append(asdict(error_msg))
            yield messages
    
    def create_gradio_interface(self):
        """Create the Gradio interface with proper configuration."""
        
        demo = gr.ChatInterface(
            self.interact_with_agent,
            chatbot=gr.Chatbot(
                label="NYC Housing Navigator (Fixed)",
                type="messages"
            ),
            examples=[
                ["What's the nearest subway to 350 East 62nd Street, Manhattan?"],
                ["Find schools near East 195th Street, Bronx, NY"],
                ["Check building violations for 1000 Grand Concourse, Bronx"],
            ],
            type="messages",
            title="🏠 NYC Voucher Housing Navigator (Smolagents 1.19 Fixed)",
            description="Fixed version using transformers.agents framework"
        )
        
        return demo

# Alternative: Direct tool conversion for your existing setup
def convert_existing_tools_to_transformers():
    """Convert your existing tools to transformers format."""
    
    @Tool
    def geocoding_tool(address: str) -> str:
        """Converts addresses to coordinates using NYC Geoclient API."""
        from geocoding_tool import GeocodingTool
        geocoder = GeocodingTool()
        return geocoder.forward(address)
    
    @Tool  
    def school_search_tool(address: str) -> str:
        """Finds nearby schools for a given address."""
        from near_school_tool import NearSchoolTool
        school_tool = NearSchoolTool()
        return school_tool.run(address)
    
    @Tool
    def subway_tool(address: str) -> str:
        """Finds nearest subway stations for a given address."""
        from nearest_subway_tool import NearestSubwayTool
        subway_tool = NearestSubwayTool()
        return subway_tool.run(address)
    
    @Tool
    def violation_tool(address: str) -> str:
        """Checks building violations for a given address."""
        from violation_checker_agent import ViolationCheckerAgent
        violation_checker = ViolationCheckerAgent()
        return violation_checker.run(address)
    
    return [geocoding_tool, school_search_tool, subway_tool, violation_tool]

if __name__ == "__main__":
    # Create and launch the fixed agent
    agent_setup = TransformersAgentSetup()
    demo = agent_setup.create_gradio_interface()
    demo.launch() 