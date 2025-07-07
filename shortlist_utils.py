from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

def add_to_shortlist(listing: Dict, app_state: Dict) -> Tuple[Dict, str]:
    """
    Add a listing to the shortlist.
    
    Args:
        listing: The listing dictionary to add
        app_state: Current application state
        
    Returns:
        Tuple of (updated_state, status_message)
    """
    # Initialize shortlist if it doesn't exist
    if "shortlist" not in app_state:
        app_state["shortlist"] = []
    
    # Create unique ID for the listing
    listing_id = str(listing.get("id", listing.get("address", "")))
    address = listing.get("address", listing.get("title", "N/A"))
    
    # Check if listing is already in shortlist
    for item in app_state["shortlist"]:
        if item.get("listing_id") == listing_id:
            return app_state, f"Listing '{address}' is already in your shortlist"
    
    # Create shortlisted item with metadata
    shortlisted_item = {
        "listing_id": listing_id,
        "address": address,
        "price": listing.get("price", "N/A"),
        "risk_level": listing.get("risk_level", "❓"),
        "violations": listing.get("building_violations", 0),
        "url": listing.get("url", "No link available"),
        "added_at": datetime.now().isoformat(),
        "priority": None,  # Can be set later
        "notes": "",
        "original_listing": listing  # Store full listing data
    }
    
    app_state["shortlist"].append(shortlisted_item)
    return app_state, f"✅ Added '{address}' to your shortlist"

def remove_from_shortlist(listing_id: str, app_state: Dict) -> Tuple[Dict, str]:
    """
    Remove a listing from the shortlist by ID.
    
    Args:
        listing_id: ID of the listing to remove
        app_state: Current application state
        
    Returns:
        Tuple of (updated_state, status_message)
    """
    if "shortlist" not in app_state:
        return app_state, "Your shortlist is empty"
    
    original_count = len(app_state["shortlist"])
    app_state["shortlist"] = [
        item for item in app_state["shortlist"] 
        if item.get("listing_id") != listing_id
    ]
    
    if len(app_state["shortlist"]) < original_count:
        return app_state, "✅ Removed listing from your shortlist"
    else:
        return app_state, "❌ Listing not found in your shortlist"

def remove_from_shortlist_by_index(index: int, app_state: Dict) -> Tuple[Dict, str]:
    """
    Remove a listing from the shortlist by index (1-based).
    
    Args:
        index: 1-based index of the listing to remove
        app_state: Current application state
        
    Returns:
        Tuple of (updated_state, status_message)
    """
    if "shortlist" not in app_state or not app_state["shortlist"]:
        return app_state, "Your shortlist is empty"
    
    if index < 1 or index > len(app_state["shortlist"]):
        return app_state, f"❌ Invalid index. Please specify a number between 1 and {len(app_state['shortlist'])}"
    
    removed_item = app_state["shortlist"].pop(index - 1)
    return app_state, f"✅ Removed '{removed_item['address']}' from your shortlist"

def get_shortlist(app_state: Dict) -> List[Dict]:
    """
    Get the current shortlist, sorted by priority then by date added.
    
    Args:
        app_state: Current application state
        
    Returns:
        List of shortlisted items
    """
    shortlist = app_state.get("shortlist", [])
    
    # Sort by priority (None/null goes to end), then by date added
    def sort_key(item):
        priority = item.get("priority")
        if priority is None:
            priority = float('inf')
        return (priority, item.get("added_at", ""))
    
    return sorted(shortlist, key=sort_key)

def set_priority(listing_id: str, priority: int, app_state: Dict) -> Tuple[Dict, str]:
    """
    Set priority for a shortlisted listing.
    
    Args:
        listing_id: ID of the listing
        priority: Priority level (1 = highest)
        app_state: Current application state
        
    Returns:
        Tuple of (updated_state, status_message)
    """
    if "shortlist" not in app_state:
        return app_state, "Your shortlist is empty"
    
    for item in app_state["shortlist"]:
        if item.get("listing_id") == listing_id:
            item["priority"] = priority
            return app_state, f"✅ Set priority {priority} for '{item['address']}'"
    
    return app_state, "❌ Listing not found in your shortlist"

def add_note(listing_id: str, note: str, app_state: Dict) -> Tuple[Dict, str]:
    """
    Add a note to a shortlisted listing.
    
    Args:
        listing_id: ID of the listing
        note: Note text to add
        app_state: Current application state
        
    Returns:
        Tuple of (updated_state, status_message)
    """
    if "shortlist" not in app_state:
        return app_state, "Your shortlist is empty"
    
    for item in app_state["shortlist"]:
        if item.get("listing_id") == listing_id:
            item["notes"] = note
            return app_state, f"✅ Added note to '{item['address']}'"
    
    return app_state, "❌ Listing not found in your shortlist"

def is_shortlisted(listing: Dict, app_state: Dict) -> bool:
    """
    Check if a listing is already in the shortlist.
    
    Args:
        listing: The listing to check
        app_state: Current application state
        
    Returns:
        True if listing is shortlisted, False otherwise
    """
    if "shortlist" not in app_state:
        return False
    
    listing_id = str(listing.get("id", listing.get("address", "")))
    return any(item.get("listing_id") == listing_id for item in app_state["shortlist"])

def get_shortlist_summary(app_state: Dict) -> str:
    """
    Get a formatted summary of the shortlist.
    
    Args:
        app_state: Current application state
        
    Returns:
        Formatted string summary of the shortlist
    """
    shortlist = get_shortlist(app_state)
    
    if not shortlist:
        return "📋 Your shortlist is empty. Save some listings to get started!"
    
    summary = f"📋 **Your Shortlist ({len(shortlist)} listings):**\n\n"
    
    for i, item in enumerate(shortlist, 1):
        priority_text = ""
        if item.get("priority"):
            priority_text = f" ⭐ Priority {item['priority']}"
        
        notes_text = ""
        if item.get("notes"):
            notes_text = f"\n   💭 Note: {item['notes']}"
        
        summary += f"{i}. **{item['address']}** - {item['price']} {item['risk_level']}{priority_text}{notes_text}\n\n"
    
    return summary

def clear_shortlist(app_state: Dict) -> Tuple[Dict, str]:
    """
    Clear all items from the shortlist.
    
    Args:
        app_state: Current application state
        
    Returns:
        Tuple of (updated_state, status_message)
    """
    if "shortlist" not in app_state or not app_state["shortlist"]:
        return app_state, "Your shortlist is already empty"
    
    count = len(app_state["shortlist"])
    app_state["shortlist"] = []
    return app_state, f"✅ Cleared {count} listings from your shortlist"

def get_shortlisted_ids(app_state: Dict) -> set:
    """
    Get a set of all shortlisted listing IDs for quick lookup.
    
    Args:
        app_state: Current application state
        
    Returns:
        Set of shortlisted listing IDs
    """
    if "shortlist" not in app_state:
        return set()
    
    return {item.get("listing_id") for item in app_state["shortlist"]} 