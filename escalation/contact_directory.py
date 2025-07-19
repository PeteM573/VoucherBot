#!/usr/bin/env python3
"""
Contact directory for human handoff scenarios.
Maps voucher types and boroughs to specific contact information.
"""

from typing import Optional, Dict

CONTACT_DIRECTORY = {
    "default": {
        "name": "HRA General Support",
        "phone": "718-557-1399",
        "email": "info@hra.nyc.gov",
        "address": "109 E 16th St, Manhattan",
        "hours": "Mon–Fri, 9am–5pm"
    },
    "CITYFHEPS": {
        "default": {
            "name": "CityFHEPS Central Office",
            "phone": "929-221-0047",
            "email": "cityfheps@hra.nyc.gov",
            "address": "109 E 16th St, Manhattan",
            "hours": "Mon–Fri, 9am–5pm"
        },
        "boroughs": {
            "manhattan": {
                "name": "Manhattan CityFHEPS Office",
                "phone": "212-331-4640",
                "email": "manhattan.hra@nyc.gov",
                "address": "109 E 16th St, Manhattan",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "brooklyn": {
                "name": "Brooklyn CityFHEPS Office",
                "phone": "718-557-1399",
                "email": "brooklyn.hra@nyc.gov",
                "address": "505 Clermont Ave, Brooklyn",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "bronx": {
                "name": "Bronx CityFHEPS Office",
                "phone": "718-503-4080",
                "email": "bronx.hra@nyc.gov",
                "address": "1916 Park Ave, Bronx",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "queens": {
                "name": "Queens CityFHEPS Office",
                "phone": "718-784-7216",
                "email": "queens.hra@nyc.gov",
                "address": "32-20 Northern Blvd, Queens",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "staten_island": {
                "name": "Staten Island CityFHEPS Office",
                "phone": "718-390-8418",
                "email": "statenisland.hra@nyc.gov",
                "address": "201 Bay St, Staten Island",
                "hours": "Mon–Fri, 9am–5pm"
            }
        }
    },
    "SECTION 8": {
        "default": {
            "name": "NYCHA Section 8 Central Office",
            "phone": "718-707-7771",
            "email": "section8@nycha.nyc.gov",
            "address": "478 E. 165th St., Bronx",
            "hours": "Mon–Fri, 9am–5pm"
        },
        "boroughs": {
            "manhattan": {
                "name": "Manhattan NYCHA Section 8 Office",
                "phone": "212-306-3000",
                "email": "manhattan.s8@nycha.nyc.gov",
                "address": "55 West 125th Street, Manhattan",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "brooklyn": {
                "name": "Brooklyn NYCHA Section 8 Office",
                "phone": "718-649-6400",
                "email": "brooklyn.s8@nycha.nyc.gov",
                "address": "787 Atlantic Ave, Brooklyn",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "bronx": {
                "name": "Bronx NYCHA Section 8 Office",
                "phone": "718-409-8626",
                "email": "bronx.s8@nycha.nyc.gov",
                "address": "478 E. 165th St., Bronx",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "queens": {
                "name": "Queens NYCHA Section 8 Office",
                "phone": "718-206-3286",
                "email": "queens.s8@nycha.nyc.gov",
                "address": "90-27 Sutphin Blvd, Queens",
                "hours": "Mon–Fri, 9am–5pm"
            },
            "staten_island": {
                "name": "Staten Island NYCHA Section 8 Office",
                "phone": "718-816-1521",
                "email": "statenisland.s8@nycha.nyc.gov",
                "address": "120 Stuyvesant Pl, Staten Island",
                "hours": "Mon–Fri, 9am–5pm"
            }
        }
    },
    "HASA": {
        "default": {
            "name": "HIV/AIDS Services Administration",
            "phone": "212-971-0626",
            "email": "hasa@hra.nyc.gov",
            "address": "12 W 14th St, Manhattan",
            "hours": "Mon–Fri, 9am–5pm"
        }
    },
    "discrimination": {
        "default": {
            "name": "NYC Commission on Human Rights",
            "phone": "212-416-0197",
            "email": "complaints@cchr.nyc.gov",
            "address": "22 Reade St, New York, NY 10007",
            "hours": "Mon–Fri, 9am–5pm"
        },
        "legal": {
            "name": "Housing Works Legal Team",
            "phone": "347-473-7400",
            "email": "legal@housingworks.org",
            "address": "57 Willoughby St, Brooklyn",
            "hours": "Mon–Fri, 9am–5pm"
        },
        "fair_housing": {
            "name": "Fair Housing Justice Center",
            "phone": "212-400-8201",
            "email": "fhjc@fairhousingjustice.org",
            "address": "30-30 Northern Blvd, Long Island City",
            "hours": "Mon–Fri, 9am–5pm"
        }
    }
}

def normalize_voucher_type(voucher_type):
    """Normalize voucher type for consistent lookup."""
    if not voucher_type:
        return None
        
    # Convert to uppercase and remove spaces/punctuation
    normalized = voucher_type.upper().replace(" ", "").replace("-", "").replace(".", "")
    
    # Handle common variations
    variations = {
        # CityFHEPS variations
        "CITYFHEP": "CITYFHEPS",
        "FHEPS": "CITYFHEPS",
        "FHEP": "CITYFHEPS",
        "CFHEPS": "CITYFHEPS",
        
        # Section 8 variations
        "SECTION8": "SECTION 8",
        "SECTIONEIGHT": "SECTION 8",
        "S8": "SECTION 8",
        "SEC8": "SECTION 8",
        
        # HASA variations
        "HASA": "HASA",
        "HIVAIDSERVICESADMIN": "HASA",
        "HIVAIDSERVICES": "HASA"
    }
    
    return variations.get(normalized, normalized)

def get_contact_info(voucher_type: Optional[str] = None, borough: Optional[str] = None, is_discrimination: bool = False, use_borough_office: bool = False) -> Dict[str, str]:
    """
    Get contact information based on voucher type and borough.
    
    Args:
        voucher_type: The type of voucher (CityFHEPS, Section 8, HASA)
        borough: The borough (manhattan, brooklyn, bronx, queens, staten_island)
        is_discrimination: Whether this is a discrimination case
        use_borough_office: Whether to force using borough-specific office for discrimination cases
        
    Returns:
        Dict containing contact information
    """
    # Normalize inputs
    if voucher_type:
        voucher_type = voucher_type.upper()
    if borough:
        borough = borough.lower().replace(" ", "_")
    
    # For discrimination cases, route to appropriate office
    if is_discrimination:
        # HASA discrimination cases go to Housing Works Legal Team
        if voucher_type == "HASA":
            return CONTACT_DIRECTORY["discrimination"]["legal"]
            
        if use_borough_office and voucher_type and borough:
            # Use borough-specific office for voucher programs that have them
            if voucher_type == "SECTION 8":
                return {
                    "name": f"{borough.title()} NYCHA Section 8 Office",
                    "phone": CONTACT_DIRECTORY["SECTION 8"]["boroughs"][borough]["phone"],
                    "email": CONTACT_DIRECTORY["SECTION 8"]["boroughs"][borough]["email"],
                    "address": CONTACT_DIRECTORY["SECTION 8"]["boroughs"][borough]["address"],
                    "hours": CONTACT_DIRECTORY["SECTION 8"]["boroughs"][borough]["hours"]
                }
            elif voucher_type == "CITYFHEPS":
                return {
                    "name": f"{borough.title()} CityFHEPS Office",
                    "phone": CONTACT_DIRECTORY["CITYFHEPS"]["boroughs"][borough]["phone"],
                    "email": CONTACT_DIRECTORY["CITYFHEPS"]["boroughs"][borough]["email"],
                    "address": CONTACT_DIRECTORY["CITYFHEPS"]["boroughs"][borough]["address"],
                    "hours": CONTACT_DIRECTORY["CITYFHEPS"]["boroughs"][borough]["hours"]
                }
        else:
            # Use NYC Commission on Human Rights for other discrimination cases
            return CONTACT_DIRECTORY["discrimination"]["default"]
    
    # For non-discrimination cases, use program-specific contact info
    if voucher_type in CONTACT_DIRECTORY:
        if borough and "boroughs" in CONTACT_DIRECTORY[voucher_type] and borough in CONTACT_DIRECTORY[voucher_type]["boroughs"]:
            return CONTACT_DIRECTORY[voucher_type]["boroughs"][borough]
        return CONTACT_DIRECTORY[voucher_type]["default"]
    
    # Default to HRA general support if no specific routing available
    return CONTACT_DIRECTORY["default"] 