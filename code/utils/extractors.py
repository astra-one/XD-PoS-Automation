import base64
import json

def extract_and_decode_board_info(response: str) -> dict:
    """
    Extracts the Base64 encoded BOARDINFO content and decodes it into a dictionary.
    
    Args:
        response (str): The full server response.
        
    Returns:
        dict: The decoded JSON content of the board.
    """
    # Find the part after "[NP]BOARDINFO[EQ]"
    board_info_start = response.find("[NP]BOARDINFO[EQ]")
    if board_info_start == -1:
        raise ValueError("No BOARDINFO field found in the response")

    # Extract everything after "[NP]BOARDINFO[EQ]"
    encoded_board_info = response[board_info_start + len("[NP]BOARDINFO[EQ]"):]

    # Find the end of the BOARDINFO part, marked by the next [NP] or [EOM]
    board_info_end = encoded_board_info.find("[NP]") if "[NP]" in encoded_board_info else encoded_board_info.find("[EOM]")
    
    # Get the Base64 string between the delimiters
    base64_string = encoded_board_info[:board_info_end].strip()  # Make sure to strip out any extra whitespace

    try:
        # Decode the Base64-encoded content
        decoded_json_str = base64.b64decode(base64_string).decode('utf-8')

        return json.loads(decoded_json_str)
    except json.JSONDecodeError as e:
        # Add detailed error message to help debugging
        print(f"Failed to parse JSON: {e}")
        raise ValueError(f"Failed to decode or parse JSON: {e}")
    except Exception as e:
        raise ValueError(f"General error during decoding: {e}")