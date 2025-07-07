from typing import Dict, Optional
from datetime import datetime, timezone
from utils import ToolObservation, current_timestamp, format_duration

class ObservationMixin:
    """
    Mixin class for creating standardized tool observations.
    Use this with any smolagents Tool to ensure consistent output format.
    
    Example:
        class MyTool(ObservationMixin, Tool):
            def forward(self, query: str):
                result = self.do_work(query)
                return self.create_observation("success", {"result": result})
    """
    
    def create_observation(self, status: str, data: dict, error: Optional[str] = None, 
                          start_time: Optional[datetime] = None) -> Dict:
        """
        Create a standardized tool observation.
        
        Args:
            status: "success" or "error"
            data: Dictionary containing the tool's output data
            error: Optional error message if status is "error"
            start_time: Optional start time for duration calculation
            
        Returns:
            Dictionary in ToolObservation format
        """
        # Calculate duration if start_time provided
        duration = None
        if start_time:
            duration = format_duration(start_time, datetime.now(timezone.utc))
        
        # Create metadata
        metadata = {
            "source": self.__class__.__name__,
            "timestamp": current_timestamp()
        }
        
        if duration is not None:
            metadata["duration"] = duration
        
        # Create the observation
        observation = ToolObservation(
            status=status,
            data={
                **data,
                "metadata": metadata
            },
            error=error
        )
        
        return observation.__dict__
    
    def create_success_observation(self, data: dict, start_time: Optional[datetime] = None) -> Dict:
        """
        Convenience method for creating successful observations.
        
        Args:
            data: Dictionary containing the successful result data
            start_time: Optional start time for duration calculation
            
        Returns:
            Dictionary in ToolObservation format with status="success"
        """
        return self.create_observation("success", data, start_time=start_time)
    
    def create_error_observation(self, error_message: str, data: Optional[dict] = None,
                               start_time: Optional[datetime] = None) -> Dict:
        """
        Convenience method for creating error observations.
        
        Args:
            error_message: Description of the error that occurred
            data: Optional dictionary with any partial data or context
            start_time: Optional start time for duration calculation
            
        Returns:
            Dictionary in ToolObservation format with status="error"
        """
        return self.create_observation(
            "error", 
            data or {}, 
            error=error_message,
            start_time=start_time
        )

class TimedObservationMixin(ObservationMixin):
    """
    Enhanced observation mixin that automatically tracks timing.
    Use this for tools where you want automatic duration tracking.
    
    Example:
        class MyTool(TimedObservationMixin, Tool):
            def forward(self, query: str):
                with self.timed_observation() as timer:
                    result = self.do_work(query)
                    return timer.success({"result": result})
    """
    
    def timed_observation(self):
        """
        Context manager for automatic timing of tool operations.
        
        Returns:
            TimedObservationContext instance
        """
        return TimedObservationContext(self)

class TimedObservationContext:
    """
    Context manager for timed observations.
    Automatically tracks start/end times and provides convenience methods.
    """
    
    def __init__(self, mixin: ObservationMixin):
        self.mixin = mixin
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # If an exception occurred, create an error observation
        if exc_type is not None:
            return self.error(f"Unexpected error: {str(exc_val)}")
        return False
    
    def success(self, data: dict) -> Dict:
        """Create a successful timed observation."""
        return self.mixin.create_success_observation(data, self.start_time)
    
    def error(self, error_message: str, data: Optional[dict] = None) -> Dict:
        """Create an error timed observation."""
        return self.mixin.create_error_observation(error_message, data, self.start_time) 