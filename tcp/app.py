from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tcp_client import TCPClient
from message_builder import MessageBuilder
from https_client import HTTPSClient
import asyncio
import base64
import json

app = FastAPI()

USERNAME = "info@xd.pt"
PASSWORD = "xd"
USERNAME_APP = "XDBR.105112"
PASSWORD_APP = "1234"
CLIENT_ID = "mobileapps"
CLIENT_SECRET = ""  # If client secret is required, provide it here

# Define your BoardRequest model
class BoardRequest(BaseModel):
    board_id: str


# Define your AuthenticationRequest model
class AuthenticationRequest(BaseModel):
    username: str
    password: str
    client_id: str
    client_secret: str = ""  # Default to an empty string like in your Java code

class Product(BaseModel):
    id: Optional[int]
    name: Optional[str]
    parentId: Optional[int]
    visible: Optional[bool]


message_builder = MessageBuilder(
    user_id="1",
    app_version="1.0",
    protocol_version="1",
    token="6a141f83b2e658377a1d585cf21a7141c115d673",
)


class BoardItem(BaseModel):
    itemId: str
    itemType: int
    parentPosition: int
    quantity: float
    price: float
    additionalInfo: Optional[str] = None
    guid: str
    employee: int
    time: int
    lineLevel: int
    ratio: int
    total: float
    lineDiscount: float
    completed: bool
    parentGuid: str

class BoardResponseItem(BoardItem):
    itemName: Optional[str] = None  # Add itemName field

class BoardResponse(BaseModel):
    id: int
    status: int
    tableLocation: Optional[str]
    content: List[BoardResponseItem]
    total: float
    globalDiscount: float

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

        print("Decoded JSON string:\n", decoded_json_str)  # Debugging step

        # Convert the decoded string into a JSON object (dict)
        return json.loads(decoded_json_str)
    except json.JSONDecodeError as e:
        # Add detailed error message to help debugging
        print(f"Failed to parse JSON: {e}")
        raise ValueError(f"Failed to decode or parse JSON: {e}")
    except Exception as e:
        raise ValueError(f"General error during decoding: {e}")


@app.post("/get-board-content/", response_model=BoardResponse)
async def get_board_content(request: BoardRequest):
    # Initialize TCP client
    client = TCPClient()

    # Connect to the server
    client.connect()

    # Use the MessageBuilder to construct the GETBOARDCONTENT message
    message = message_builder.build_get_board_content(board_id=request.board_id)

    # Send the message to the server
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, client.send_data, message)

        if not response:
            raise HTTPException(status_code=500, detail="No response from the server.")

        # Process the response to extract the decoded content
        board_info = extract_and_decode_board_info(response)
        return board_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process the board content: {str(e)}")

    finally:
        # Ensure the client connection is closed
        client.close()


@app.post("/get-products/", response_model=List[Product])
async def get_products():
    client = TCPClient()
    client.connect()

    # Build the GETDATALIST message for products
    message = message_builder.build_get_data_list(
        object_type="XDPeople.Entities.MobileItemFamily",  # Object Type
        part=0,  # Part
        limit=5000,  # Limit
        message_id="db45856c-b3fe-4995-a5fc-f08b09369904"  # Provided Message ID
    )

    # Run send_data in a thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, client.send_data, message)

    # Check for None response
    if response is None:
        raise HTTPException(
            status_code=500, detail="Failed to receive response from the TCP server"
        )

    try:
        # Extract the Base64 encoded part after "[NP]OBJECT[EQ]"
        encoded_object_part = extract_encoded_object(response)
        
        # Decode the Base64 encoded string
        decoded_json_str = base64.b64decode(encoded_object_part).decode('utf-8')

        # Convert the decoded string into a JSON object (list of products)
        product_data = json.loads(decoded_json_str)

        # Validate and return the list of products using the Product model
        return [Product(**item) for item in product_data]
    
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to decode or process the response: {str(e)}"
        )

def extract_encoded_object(response: str) -> str:
    """
    Extracts the Base64 encoded portion of the response after '[NP]OBJECT[EQ]'.

    Args:
        response (str): The full server response.

    Returns:
        str: The Base64 encoded object part.
    """
    # Find the part after "[NP]OBJECT[EQ]"
    object_start = response.find("[NP]OBJECT[EQ]")
    
    if object_start == -1:
        raise ValueError("No OBJECT field found in the response")

    # Extract everything after "[NP]OBJECT[EQ]"
    encoded_object = response[object_start + len("[NP]OBJECT[EQ]"):]
    
    # Find the next "[NP]" or "[EOM]" which marks the end of the OBJECT field
    object_end = encoded_object.find("[NP]") if "[NP]" in encoded_object else encoded_object.find("[EOM]")
    
    # Return the Base64 string between the delimiters
    return encoded_object[:object_end]

def extract_encoded_object(response: str) -> str:
    """
    Extracts the Base64 encoded portion of the response after '[NP]OBJECT[EQ]'.

    Args:
        response (str): The full server response.

    Returns:
        str: The Base64 encoded object part.
    """
    # Find the part after "[NP]OBJECT[EQ]"
    object_start = response.find("[NP]OBJECT[EQ]")
    
    if object_start == -1:
        raise ValueError("No OBJECT field found in the response")

    # Extract everything after "[NP]OBJECT[EQ]"
    encoded_object = response[object_start + len("[NP]OBJECT[EQ]"):]
    
    # Find the next "[NP]" or "[EOM]" which marks the end of the OBJECT field
    object_end = encoded_object.find("[NP]") if "[NP]" in encoded_object else encoded_object.find("[EOM]")
    
    # Return the Base64 string between the delimiters
    return encoded_object[:object_end]


@app.get("/")
def root():
    return {"message": "API is running"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
