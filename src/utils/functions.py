import asyncio
import base64
import json
import uuid
from fastapi import HTTPException
from utils.extractors import extract_encoded_object
from ..models.entity_models import Product, Table

async def _get_products(tcp_client_context, message_builder):
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
        
async def _get_tables(tcp_client_context, message_builder):
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