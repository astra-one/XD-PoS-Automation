import asyncio
import uuid
import base64
import json
from typing import Dict
from fastapi import HTTPException
from .tcp_client import TCPClient
from ..builders.pos_message_builder import MessageBuilder
from ..models.entity_models import Product


class RestaurantClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RestaurantClient, cls).__new__(cls)
            cls._instance.products = {}  # Cache for products
        return cls._instance

    def __init__(self):
        if not self.products:
            asyncio.run(self.load_products())

    async def load_products(self):
        """
        Load products and store them in the cache.
        """
        try:
            products = await self._fetch_products()
            self.products = {str(product.id): product for product in products}
            print(f"Product cache initialized with {len(self.products)} items.")
        except Exception as e:
            print(f"Failed to load products: {e}")

    async def _fetch_products(self) -> list[Product]:
        """
        Fetch products from the server via TCP.
        """
        message_builder = MessageBuilder(
            user_id="1", app_version="1.0", protocol_version="1", token="f460a145dceae95e8b39c5afa110e820a7f1d8ff"
        )

        with TCPClient() as client:
            message = message_builder.build_get_data_list(
                object_type="XDPeople.Entities.MobileItem",
                part=0,
                limit=5000,
                message_id=str(uuid.uuid4()),
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, client.send_data, message)
            if response is None:
                raise HTTPException(status_code=500, detail="Failed to receive response from the TCP server")

            try:
                encoded_object_part = self._extract_encoded_object(response)
                decoded_json_str = base64.b64decode(encoded_object_part).decode('utf-8')
                product_data = json.loads(decoded_json_str)
                return [Product(**item) for item in product_data]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to decode or process the response: {str(e)}")

    async def fetch_table_content(self, table_id: str) -> Dict:
        """
        Fetch content for a specific table and enrich it with product names.
        """
        message_builder = MessageBuilder(
            user_id="1", app_version="1.0", protocol_version="1", token="f460a145dceae95e8b39c5afa110e820a7f1d8ff"
        )

        with TCPClient() as client:
            message = message_builder.build_get_board_content(board_id=table_id)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, client.send_data, message)
            if response is None:
                raise HTTPException(status_code=500, detail="Failed to receive response from the TCP server")

            try:
                # Process and decode the table content
                table_content = self._extract_and_decode_board_info(response)

                # Enrich the table content with product names
                self._enrich_table_content_with_product_names(table_content)

                return table_content
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to decode or process the response: {str(e)}")

    def _enrich_table_content_with_product_names(self, table_content: dict):
        """
        Enrich the table content with product names using the product cache.
        """
        content = table_content.get('content', [])

        for index, item in enumerate(content):
            item_id = item.get('itemId')
            if item_id is not None:
                product = self.products.get(str(item_id))
            else:
                product = None
                print(f"Item at index {index} has no 'itemId'.")

            if product:
                item['itemName'] = product.name
            else:
                item['itemName'] = "Unknown Product"
                print(f"Product not found for itemId: {item_id}")

    @staticmethod
    def _extract_encoded_object(response: str) -> str:
        """
        Extracts the Base64 encoded portion of the response after '[NP]OBJECT[EQ]'.
        """
        object_start = response.find("[NP]OBJECT[EQ]")
        if object_start == -1:
            raise ValueError("No OBJECT field found in the response")

        encoded_object = response[object_start + len("[NP]OBJECT[EQ]"):]
        object_end = encoded_object.find("[NP]") if "[NP]" in encoded_object else encoded_object.find("[EOM]")
        if object_end == -1:
            raise ValueError("End of OBJECT field not found in the response")
        return encoded_object[:object_end].strip()

    @staticmethod
    def _extract_and_decode_board_info(response: str) -> dict:
        """
        Extracts the Base64 encoded BOARDINFO content and decodes it into a dictionary.
        """
        board_info_start = response.find("[NP]BOARDINFO[EQ]")
        if board_info_start == -1:
            raise ValueError("No BOARDINFO field found in the response")

        encoded_board_info = response[board_info_start + len("[NP]BOARDINFO[EQ]"):]
        board_info_end = encoded_board_info.find("[NP]") if "[NP]" in encoded_board_info else encoded_board_info.find("[EOM]")
        if board_info_end == -1:
            raise ValueError("End of BOARDINFO field not found in the response")

        base64_string = encoded_board_info[:board_info_end].strip()
        try:
            decoded_json_str = base64.b64decode(base64_string).decode('utf-8')
            return json.loads(decoded_json_str)
        except Exception as e:
            raise ValueError(f"Error during decoding: {e}")
