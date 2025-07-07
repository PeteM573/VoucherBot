from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import json

@dataclass
class ToolObservation:
    """
    Standardized observation structure for all VoucherBot tools.
    Ensures consistent data format across BrowserAgent, ViolationChecker, etc.
    """
    status: str  # "success" or "error"
    data: Dict
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if the tool operation was successful."""
        return self.status == "success"
    
    @property
    def is_error(self) -> bool:
        """Check if the tool operation failed."""
        return self.status == "error"

def log_tool_action(tool_name: str, action: str, details: dict) -> None:
    """
    Standardized logging for tool actions.
    This output will be visible in ActionStep.observations for LLM feedback.
    
    Args:
        tool_name: Name of the tool (e.g., "BrowserAgent", "ViolationChecker")
        action: Action being performed (e.g., "search_started", "bbl_lookup")
        details: Dictionary with relevant details for the action
    """
    print(f"[{tool_name}] {action}: {json.dumps(details, indent=2)}")

def current_timestamp() -> str:
    """
    Generate ISO format timestamp for tool observations.
    
    Returns:
        ISO format timestamp string with Z suffix (UTC)
    """
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def format_duration(start_time: datetime, end_time: datetime) -> float:
    """
    Calculate duration between two datetime objects.
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        
    Returns:
        Duration in seconds as float
    """
    return (end_time - start_time).total_seconds()

def parse_observation_data(observation: dict) -> Optional[ToolObservation]:
    """
    Parse a dictionary into a ToolObservation object.
    Useful for converting agent outputs back to structured format.
    
    Args:
        observation: Dictionary with observation data
        
    Returns:
        ToolObservation object or None if parsing fails
    """
    try:
        # Validate that we have valid data types
        status = observation.get("status", "error")
        data = observation.get("data", {})
        error = observation.get("error")
        
        # Check for invalid data types that would cause issues
        if status is None or data is None:
            raise ValueError("Invalid data types in observation")
        
        return ToolObservation(
            status=status,
            data=data,
            error=error
        )
    except Exception as e:
        print(f"Failed to parse observation: {str(e)}")
        return None 