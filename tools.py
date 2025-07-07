import json
import requests
from smolagents import tool, Tool
from typing import Any, Dict, Optional
from nearest_subway_tool import nearest_subway_tool
from enrichment_tool import enrichment_tool
from near_school_tool import near_school_tool

@tool
def find_matching_listings(user_profile: dict) -> list:
    """
    Finds and filters rental listings based on a user's housing profile.
    
    Args:
        user_profile: A dictionary containing the user's housing requirements:
            - voucher_type: The type of housing voucher (e.g., "CityFHEPS", "Section 8")
            - bedrooms: Number of bedrooms required
            - max_rent: Maximum monthly rent the user can afford
    """
    print(f"Searching for listings matching profile: {user_profile}")
    with open('listings.json', 'r') as f:
        all_listings = json.load(f)
    
    matches = []
    for listing in all_listings:
        if (user_profile.get('voucher_type') in listing.get('accepts_voucher_type', []) and
            user_profile.get('bedrooms') <= listing.get('bedrooms', 0) and
            user_profile.get('max_rent') >= listing.get('rent', 0)):
            matches.append(listing)
    print(f"Found {len(matches)} matching listings")
    return matches

@tool
def get_listing_violations(bbl: str) -> dict:
    """
    Retrieves housing violations for a specific building based on its BBL number.
    
    Args:
        bbl: The Borough-Block-Lot (BBL) number of the building
    """
    print(f"Checking violations for BBL: {bbl}")
    try:
        # Mock violation data for testing
        violations = {
            "open_violations": 2,
            "total_violations": 5,
            "last_inspection": "2024-01-15"
        }
        print(f"Found {violations['open_violations']} open violations")
        return violations
    except Exception as e:
        print(f"Error checking violations: {str(e)}")
        return {"error": str(e)}

@tool
def final_answer(data: Any) -> str:
    """
    Formats and returns the final answer to the user.
    
    Args:
        data: Either a string message or a dictionary containing the response data.
            If a dictionary, it should contain:
            - listings: List of enriched listings with their violations
            - summary: A summary message about the results
    
    Returns:
        A formatted string response suitable for display in the chat interface.
    """
    if isinstance(data, dict):
        listings = data.get('listings', [])
        summary = data.get('summary', 'No summary available.')
        
        if not listings:
            return "I'm sorry, I couldn't find any listings that match your criteria. Please try broadening your search."
        
        response = "### I found some matches for you!\n\n"
        for item in listings:
            listing = item.get('listing', {})
            violations = item.get('violations', [])
            
            response += f"**Address:** {listing.get('address', 'N/A')}\n"
            response += f"- Rent: ${listing.get('rent', 0)} | Bedrooms: {listing.get('bedrooms', 0)}\n"
            response += f"- Open Violations: {len(violations)}\n\n"
        
        response += f"**Summary:** {summary}"
        return response
    
    return str(data)

class CommsTool(Tool):
    """
    This tool generates a well-structured email to a landlord based on provided details.
    It takes user requirements, voucher information, and listing details as input,
    and returns the complete email content.

    Args:
        landlord_email: The email address of the landlord.
        landlord_name: The name of the landlord.
        user_name: The name of the user requesting the email.
        user_requirements: A dictionary or string detailing the user's needs (e.g., number of occupants, move-in date, specific amenities).
        voucher_details: A dictionary or string containing voucher information (e.g., voucher ID, amount, expiration).
        listing_details: A dictionary or string with property details (e.g., address, number of bedrooms, rent, availability).
    """
    name = "generate_landlord_email"
    description = (
        "Generates a professional email to a landlord. "
        "Inputs include the landlord's email and name, the user's name and requirements, "
        "voucher details, and specific listing information. "
        "The output is the complete, formatted email content as a string."
    )
    inputs = {
        "landlord_email": {
            "type": "string",
            "description": "The email address of the landlord (e.g., 'landlord@example.com')."
        },
        "landlord_name": {
            "type": "string",
            "description": "The name of the landlord (e.g., 'Mr. Smith')."
        },
        "user_name": {
            "type": "string",
            "description": "The name of the user for whom the email is being generated (e.g., 'John Doe')."
        },
        "user_requirements": {
            "type": "string",
            "description": "Details about the user's needs, such as preferred move-in date, number of people, and specific amenities required."
        },
        "voucher_details": {
            "type": "string",
            "description": "Information about the user's housing voucher, including the voucher ID, amount, and any specific terms."
        },
        "listing_details": {
            "type": "string",
            "description": "Specific details of the property, such as the address, number of bedrooms, monthly rent, and current availability status."
        }
    }
    output_type = "string"

    def forward(
        self,
        landlord_email: str,
        landlord_name: str,
        user_name: str,
        user_requirements: str,
        voucher_details: str,
        listing_details: str
    ) -> str:
        """
        Constructs and returns the email content for the landlord.
        Includes validation for critical listing details.
        """
        # Basic validation for critical information
        if not all([landlord_email, landlord_name, user_name, user_requirements, voucher_details]):
            error_message = "Error: Missing critical contact or user information. Cannot generate email."
            print(error_message)
            return error_message

        # Attempt to parse listing_details (if provided as JSON string)
        parsed_listing_details = {}
        try:
            if listing_details:
                parsed_listing_details = json.loads(listing_details)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse listing_details as JSON: {listing_details}")

        # Check for crucial listing details
        required_listing_fields = ["address", "rent", "availability"]
        missing_listing_info = [
            field for field in required_listing_fields
            if not parsed_listing_details.get(field)
        ]

        if missing_listing_info:
            print(f"Warning: Incomplete listing details. Missing: {', '.join(missing_listing_info)}. Generating email with caveats.")
            address = parsed_listing_details.get("address", "N/A (Missing)")
            rent = parsed_listing_details.get("rent", "N/A (Missing)")
            availability = parsed_listing_details.get("availability", "N/A (Missing)")
            listing_summary = f"Property: {address}, Rent: {rent}, Availability: {availability}."
            if missing_listing_info:
                listing_summary += " (Some listing details were incomplete)."
        else:
            address = parsed_listing_details.get("address")
            rent = parsed_listing_details.get("rent")
            availability = parsed_listing_details.get("availability")
            listing_summary = f"Property located at {address}, with a monthly rent of {rent} and available from {availability}."

        email_subject = f"Inquiry Regarding Property - {user_name} (Voucher Holder)"

        email_body = f"""
Dear {landlord_name},

I hope this email finds you well.

My name is {user_name}, and I am writing to express my interest in your property {address}.
I am a {user_requirements}.

I am a housing voucher holder, and my voucher details are as follows: {voucher_details}.
This voucher can assist with rent payments and is fully compliant with housing program regulations.

Could you please confirm the current availability of the property and its exact rental terms?
I am available for a viewing at your earliest convenience.

Thank you for your time and consideration. I look forward to your response.

Sincerely,
{user_name}
"""
        print(f"Email generated successfully for {landlord_email} with subject: {email_subject}")
        return email_body.strip()

# Create an instance of the CommsTool
comms_tool = CommsTool() 