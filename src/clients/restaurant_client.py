import asyncio
import uuid
import base64
import json
from typing import Dict, List, Type
from fastapi import HTTPException
from .tcp_client import TCPClient
from ..builders.pos_message_builder import MessageBuilder
from ..models.entity_models import Product, Table  # Ensure Table is imported


class RestaurantClient:
    _instance = None

    # Class-level constants
    USER_ID = "1"
    APP_VERSION = "1.0"
    PROTOCOL_VERSION = "1"
    TOKEN = "f460a145dceae95e8b39c5afa110e820a7f1d8ff"
    LIMIT = 5000

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
            products = await self._fetch_data_list(
                object_type="XDPeople.Entities.MobileItem",
                model_class=Product
            )
            self.products = {str(product.id): product for product in products}
            print(f"Product cache initialized with {len(self.products)} items.")
        except Exception as e:
            print(f"Failed to load products: {e}")

    async def _fetch_data_list(self, object_type: str, model_class: Type) -> List:
        """
        Generic method to fetch a list of data from the server via TCP.
        """
        message = self._build_get_data_list_message(object_type)
        response = await self._send_message(message)

        if response is None:
            raise HTTPException(status_code=500, detail="Failed to receive response from the TCP server")

        try:
            encoded_object = self._extract_encoded_object(response)
            decoded_json = self._decode_base64_json(encoded_object)
            return [model_class(**item) for item in decoded_json]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to decode or process the response: {str(e)}")

    async def _send_message(self, message: str) -> str:
        """
        Send a message to the TCP server and return the response.
        """
        with TCPClient() as client:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, client.send_data, message)
            return response

    def _build_get_data_list_message(self, object_type: str) -> str:
        """
        Build a GETDATALIST message using the MessageBuilder.
        """
        message_builder = MessageBuilder(
            user_id=self.USER_ID,
            app_version=self.APP_VERSION,
            protocol_version=self.PROTOCOL_VERSION,
            token=self.TOKEN
        )
        return message_builder.build_get_data_list(
            object_type=object_type,
            part=0,
            limit=self.LIMIT,
            message_id=str(uuid.uuid4()),
        )

    def _build_get_board_content_message(self, board_id: str) -> str:
        """
        Build a GET_BOARD_CONTENT message using the MessageBuilder.
        """
        message_builder = MessageBuilder(
            user_id=self.USER_ID,
            app_version=self.APP_VERSION,
            protocol_version=self.PROTOCOL_VERSION,
            token=self.TOKEN
        )
        return message_builder.build_get_board_content(board_id=board_id)

    @staticmethod
    def _extract_encoded_object(response: str) -> str:
        """
        Extracts the Base64 encoded portion of the response after '[NP]OBJECT[EQ]'.
        """
        return RestaurantClient._extract_field(response, "[NP]OBJECT[EQ]")

    @staticmethod
    def _extract_and_decode_board_info(response: str) -> dict:
        """
        Extracts the Base64 encoded BOARDINFO content and decodes it into a dictionary.
        """
        encoded_board_info = RestaurantClient._extract_field(response, "[NP]BOARDINFO[EQ]")
        return RestaurantClient._decode_base64_json(encoded_board_info)

    @staticmethod
    def _extract_field(response: str, field_identifier: str) -> str:
        """
        General method to extract a Base64 encoded field from the response.
        """
        start = response.find(field_identifier)
        if start == -1:
            raise ValueError(f"No {field_identifier.strip('[').strip(']')} field found in the response")

        encoded_field = response[start + len(field_identifier):]
        end = encoded_field.find("[NP]") if "[NP]" in encoded_field else encoded_field.find("[EOM]")
        if end == -1:
            raise ValueError(f"End of {field_identifier.strip('[').strip(']')} field not found in the response")
        return encoded_field[:end].strip()

    @staticmethod
    def _decode_base64_json(encoded_str: str) -> dict:
        """
        Decode a Base64 encoded JSON string into a dictionary.
        """
        try:
            decoded_bytes = base64.b64decode(encoded_str)
            decoded_str = decoded_bytes.decode('utf-8')
            return json.loads(decoded_str)
        except Exception as e:
            raise ValueError(f"Error during Base64 decoding or JSON parsing: {e}")

    async def fetch_table_content(self, table_id: str) -> Dict:
        """
        Fetch content for a specific table and enrich it with product names.
        """
        try:
            message = self._build_get_board_content_message(table_id)
            response = await self._send_message(message)

            if response is None:
                raise HTTPException(status_code=500, detail="Failed to receive response from the TCP server")

            # Extract and decode BOARDINFO
            table_content = self._extract_and_decode_board_info(response)

            # Enrich the table content with product names
            self._enrich_table_content_with_product_names(table_content)

            return table_content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch table content: {str(e)}")

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

            item['itemName'] = product.name if product else "Unknown Product"
            if not product:
                print(f"Product not found for itemId: {item_id}")

    async def fetch_tables(self) -> List[Table]:
        """
        Fetch a list of tables from the server via TCP.
        """
        try:
            tables = await self._fetch_data_list(
                object_type="XDPeople.Entities.MobileBoardStatus",
                model_class=Table
            )
            return tables
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch tables: {str(e)}")
