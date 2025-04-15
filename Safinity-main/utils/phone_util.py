import re

def normalize_phone_number(phone):
    """
    Normalize phone number to a standard format (with + and digits only).
    This handles various phone input formats:
    - Numbers with or without country code
    - Numbers with or without + prefix
    - Numbers starting with 0 (removing leading zero if country code exists)
    
    Args:
        phone (str): The phone number to normalize
        
    Returns:
        str: The normalized phone number
    """
    if not phone:
        return phone
    
    # Strip all whitespace
    phone = re.sub(r'\s+', '', phone)
    
    # If phone contains + and digits
    if re.match(r'^\+\d+$', phone):
        return phone
    
    # Specific handling for Pakistani numbers (03xxxxxxxxx format)
    # Convert 03xxxxxxxx to +923xxxxxxxx
    if phone.startswith('0') and len(phone) > 10 and (
        phone.startswith('03') or phone.startswith('0092')):
        if phone.startswith('0092'):
            return f"+{phone[1:]}"  # Convert 0092 to +92
        else:
            return f"+92{phone[1:]}"  # Convert 03... to +923...
    
    # If phone starts with a country code digit (not 0), add + prefix
    # This handles cases where user entered country code without +
    if len(phone) > 7 and phone[0] not in ['+', '0'] and phone.isdigit():
        # Assume it's a country code without + prefix
        return f"+{phone}"
    
    # If phone is just digits (no +), check format
    if phone.isdigit():
        # If starts with 0, assume it's a local number, keep as is
        if phone.startswith('0'):
            return phone
        # If longer than 7 digits and doesn't start with 0, assume country code is included
        elif len(phone) > 7:
            return f"+{phone}"
        return phone
    
    # If phone contains + and digits with other characters
    if '+' in phone:
        # Extract all digits after the +
        digits = re.sub(r'[^\d]', '', phone.split('+', 1)[1])
        return f"+{digits}"
    
    # If phone contains colon followed by digits (e.g., :923026962828)
    if ':' in phone:
        parts = phone.split(':', 1)
        if len(parts) == 2 and parts[1]:
            # If the part after : starts with 0, remove it
            if parts[1].startswith('0'):
                return f"+{parts[1][1:]}"
            return f"+{parts[1]}"
    
    # Default: just return phone after removing non-digits
    digits = re.sub(r'[^\d]', '', phone)
    if len(digits) > 7:  # If it looks like it has a country code
        return f"+{digits}"
    return digits

def find_phone_number_variants(phone):
    """
    Generate possible variants of a phone number for flexible matching
    
    Args:
        phone (str): The phone number to generate variants for
        
    Returns:
        list: List of possible phone number variants
    """
    if not phone:
        return []
    
    variants = [phone]  # Start with original
    normalized = normalize_phone_number(phone)
    
    # Add normalized variant
    if normalized != phone:
        variants.append(normalized)
    
    # Pakistan-specific handling - crucial pattern
    # If the number is in local Pakistani format (03xxxxxxxxx)
    if phone.startswith('03') and len(phone) >= 11:
        # Add the international format with country code
        pk_international = f"+92{phone[1:]}"  # 03xx... -> +923xx...
        variants.append(pk_international)
        # Also add without +
        variants.append(f"92{phone[1:]}")  # 03xx... -> 923xx...
    
    # If the number is in international Pakistani format (+923xxxxxxxxx)
    if (phone.startswith('+92') and len(phone) >= 12) or (phone.startswith('92') and len(phone) >= 11):
        # Extract the part after country code
        if phone.startswith('+'):
            local_part = phone[3:]  # Skip +92
        else:
            local_part = phone[2:]  # Skip 92
        
        # Add the local format with leading 0
        pk_local = f"0{local_part}"  # +923xx... -> 03xx...
        variants.append(pk_local)
    
    # If normalized format has a + (indicating country code), create variations
    if normalized.startswith('+'):
        # Add version without +
        variants.append(normalized[1:])
        
        # Add version with leading 0 after removing +
        # This specifically helps with Pakistani numbers
        variants.append(f"0{normalized[1:]}")
    # If no + but looks like it has a country code (length > 10 and not starting with 0)
    elif len(normalized) > 10 and not normalized.startswith('0') and normalized.isdigit():
        # Add version with +
        variants.append(f"+{normalized}")
        
        # Add version with leading 0
        variants.append(f"0{normalized}")
    # If it starts with 0 and is long enough to have a country code
    elif normalized.startswith('0') and len(normalized) > 10:
        # Add version without leading 0
        no_zero = normalized[1:]
        variants.append(no_zero)
        
        # Add version with + (assuming the 0 was masking a country code)
        variants.append(f"+{no_zero}")
        
        # Specific for Pakistan, also try with country code
        variants.append(f"+92{normalized[1:]}")
        variants.append(f"92{normalized[1:]}")
    # For shorter numbers (local numbers)
    elif normalized.isdigit():
        # If it doesn't start with 0, add version with leading 0
        if not normalized.startswith('0'):
            variants.append(f"0{normalized}")
        # If it starts with 0, add version without it
        else:
            variants.append(normalized[1:])
    
    # For debugging, print variants
    print(f"Phone number variants for '{phone}': {variants}")
    
    return list(set(variants))  # Remove any duplicates
