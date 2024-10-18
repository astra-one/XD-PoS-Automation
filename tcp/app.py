import asyncio
import base64
import json
import logging
import os
import uuid
from contextlib import contextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException

from models import BoardRequest, BoardResponse, Product, Table
from tcp_client import TCPClient
from message_builder import MessageBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global cache to store product data
product_cache = {}

# Initialize MessageBuilder
message_builder = MessageBuilder(
    user_id="1",
    app_version="1.0",
    protocol_version="1",
    token="2a898f1115c259f17ce5d802455fd3e658cbce56",
)

@app.on_event("startup")
async def startup_event():
    global product_cache
    try:
        # Fetch products and store them in the cache using itemId as the key
        products = await _get_products()
        product_cache = {str(product.id): product for product in products}
        logger.info(f"Product cache initialized with {len(product_cache)} items.")
    except Exception as e:
        logger.error(f"Failed to initialize product cache: {e}")

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
    # Find the end of the BOARDINFO part
    board_info_end = encoded_board_info.find("[NP]") if "[NP]" in encoded_board_info else encoded_board_info.find("[EOM]")
    if board_info_end == -1:
        raise ValueError("End of BOARDINFO field not found in the response")
    # Get the Base64 string between the delimiters
    base64_string = encoded_board_info[:board_info_end].strip()
    try:
        # Decode the Base64-encoded content
        decoded_json_str = base64.b64decode(base64_string).decode('utf-8')
        return json.loads(decoded_json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise ValueError(f"Failed to decode or parse JSON: {e}")
    except Exception as e:
        raise ValueError(f"General error during decoding: {e}")

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
    if object_end == -1:
        raise ValueError("End of OBJECT field not found in the response")
    # Return the Base64 string between the delimiters
    return encoded_object[:object_end].strip()

@contextmanager
def tcp_client_context():
    client = TCPClient()
    try:
        client.connect()
        yield client
    finally:
        client.close()

@app.post("/get-board-content/", response_model=BoardResponse)
async def get_board_content(request: BoardRequest):
    # Initialize TCP client
    with tcp_client_context() as client:
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

            # Check if board_info is a dict and process the 'content' list
            if isinstance(board_info, dict) and 'content' in board_info:
                formatted_lines = [f"Comanda: {request.board_id}"]

                for index, item in enumerate(board_info['content']):
                    # Ensure itemId is used as a string for dictionary lookup
                    item_id = item.get('itemId')
                    if item_id is not None:
                        product = product_cache.get(str(item_id))
                    else:
                        product = None
                        logger.warning(f"Item at index {index} has no 'itemId'.")

                    if product:
                        # Convert price and total to strings with comma as decimal separator and R$ prefix
                        price_str = f"R$ {item['price']:.2f}".replace('.', ',')
                        total_str = f"R$ {item['total']:.2f}".replace('.', ',')
                        quantity_str_int = int(item['quantity'])
                        # Format the item line: itemName quantity X unit price = total
                        formatted_line = f"{product.name} {quantity_str_int} X {price_str} = {total_str}"
                        formatted_lines.append(formatted_line)
                    else:
                        # Handle items without a valid product
                        logger.warning(f"Product not found for itemId: {item_id}")

                # Generate the file name based on the board_id
                file_name = f"comanda_{request.board_id}.txt"
                file_path = os.path.join(os.getcwd(), file_name)

                # Write the formatted content to a .txt file
                with open(file_path, 'w') as file:
                    file.write("\n".join(formatted_lines))

                # Sanitize the 'itemId' fields to ensure they are strings
                for item in board_info['content']:
                    if 'itemId' in item and item['itemId'] is not None:
                        item['itemId'] = str(item['itemId'])
                    else:
                        # Assign a default value or handle as needed
                        item['itemId'] = "unknown_item_id"
                        logger.warning("Assigned default value to missing 'itemId'.")

                # Return the board info as the response
                return BoardResponse(**board_info)
            else:
                raise HTTPException(status_code=500, detail="Board content is not in the expected format.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process the board content: {str(e)}")

async def _get_products():
    with tcp_client_context() as client:
        # Build the GETDATALIST message for products
        message = message_builder.build_get_data_list(
            object_type="XDPeople.Entities.MobileItem",  # Object Type
            part=0,  # Part
            limit=5000,  # Limit
            message_id=str(uuid.uuid4()),  # Message ID
        )
        # Run send_data in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, client.send_data, message)
        if response is None:
            raise HTTPException(
                status_code=500, detail="Failed to receive response from the TCP server"
            )
        try:
            # Extract and decode the product list
            encoded_object_part = extract_encoded_object(response)
            decoded_json_str = base64.b64decode(encoded_object_part).decode('utf-8')
            product_data = json.loads(decoded_json_str)
            # Validate and return the list of products using the Product model
            return [Product(**item) for item in product_data]
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to decode or process the response: {str(e)}"
            )

@app.post("/get-products/", response_model=List[Product])
async def get_products():
    try:
        products = await _get_products()
        return products
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get products: {str(e)}"
        )

async def _get_tables():
    with tcp_client_context() as client:
        # Build the GETDATALIST message for tables
        message = message_builder.build_get_data_list(
            object_type="XDPeople.Entities.MobileBoardStatus",  # Object Type
            part=0,  # Part
            limit=5000,  # Limit
            message_id=str(uuid.uuid4()),  # Message ID
        )
        # Run send_data in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, client.send_data, message)
        if response is None:
            raise HTTPException(
                status_code=500, detail="Failed to receive response from the TCP server"
            )
        try:
            # Extract and decode the table list
            encoded_object_part = extract_encoded_object(response)
            decoded_json_str = base64.b64decode(encoded_object_part).decode('utf-8')
            table_data = json.loads(decoded_json_str)
            # Validate and return the list of tables using the Table model
            return [Table(**item) for item in table_data]
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to decode or process the response: {str(e)}"
            )

@app.post("/get-tables/", response_model=List[Table])
async def get_tables():
    try:
        tables = await _get_tables()
        return tables
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get tables: {str(e)}"
        )

@app.get("/")
def root():
    return {"message": "API is running"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
