import asyncio
import uuid
import base64
import json
import time
from typing import Dict, List, Type, Optional
from fastapi import HTTPException
from .token_manager import TokenManager
from .tcp_client import TCPClient
from ..builders.pos_message_builder import MessageBuilder
from ..models.entity_models import Product, Table


class RestaurantClient:
    _instance: Optional["RestaurantClient"] = None

    # Class-level constants
    USER_ID: str = "1"
    APP_VERSION: str = "1.0"
    PROTOCOL_VERSION: str = "1"
    TOKEN: str = ""
    LIMIT: int = 5000

    def __new__(cls, token_manager: TokenManager):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.products: Dict[str, Product] = {}
            cls._instance.message_builder = MessageBuilder(
                user_id=cls.USER_ID,
                app_version=cls.APP_VERSION,
                protocol_version=cls.PROTOCOL_VERSION,
                token="",  # Inicialize com token vazio
            )
            cls._instance.token_manager = token_manager
        return cls._instance

    def __init__(self, token_manager):
        if not self.products:
            asyncio.run(self.load_products())
        self.token_manager = token_manager

    async def load_products(self):
        """Load products and store them in the cache."""
        try:
            products = await self._fetch_data_list(
                object_type="XDPeople.Entities.MobileItem", model_class=Product
            )
            self.products = {str(product.id): product for product in products}
            print(f"Product cache initialized with {len(self.products)} items.")
        except Exception as e:
            print(f"Failed to load products: {e}")

    async def _fetch_data_list(self, object_type: str, model_class: Type) -> List:
        """Generic method to fetch a list of data from the server via TCP."""
        message = self.message_builder.build_get_data_list(
            object_type=object_type,
            part=0,
            limit=self.LIMIT,
            message_id=str(uuid.uuid4()),
        )
        response = await self._send_message(message)

        if not response:
            raise HTTPException(
                status_code=500, detail="Failed to receive response from the TCP server"
            )

        try:
            encoded_object = self._extract_field(response, "[NP]OBJECT[EQ]")
            decoded_json = self._decode_base64_json(encoded_object)
            return [model_class(**item) for item in decoded_json]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decode or process the response: {str(e)}",
            )

    async def _send_message(self, message: str) -> Optional[str]:
        """Send a message to the TCP server and return the response."""
        token = await self.token_manager.get_token()
        message_with_token = self._include_token_in_message(message, token)

        with TCPClient() as client:
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None, client.send_data, message_with_token
                )
                # Verifique se a resposta contém um erro de autenticação
                if self._is_authentication_error(response):
                    # Se houver erro de autenticação, atualize o estado do TokenManager
                    await self.token_manager.set_unauthenticated()
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication error: token expired or invalid",
                    )
                return response
            except Exception as e:
                # Em caso de erro de conexão ou outro problema, também pode marcar como não autenticado
                await self.token_manager.set_unauthenticated()
                raise HTTPException(
                    status_code=500, detail=f"Failed to send message: {e}"
                )

    def _is_authentication_error(self, response: str) -> bool:
        """Check if the response indicates an authentication error."""
        # Aqui você deve implementar a lógica que identifica um erro de autenticação na resposta
        # Suponha que uma resposta específica indique erro de autenticação (exemplo: "AuthError")
        return (
            "AuthError" in response
        )  # Substitua pelo indicador real de erro de autenticação

    def _include_token_in_message(self, message: str, token: str) -> str:
        # Modify this method based on how the token should be included in your messages
        # For example, if the token is included in the headers or as a field in the message
        return f"{message}[TOKEN]{token}[ENDTOKEN]"

    async def fetch_table_content(self, table_id: int) -> Dict:
        """Fetch content for a specific table and enrich it with product names."""
        try:
            message = self.message_builder.build_get_board_content(
                board_id=str(table_id)
            )
            response = await self._send_message(message)

            if not response:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to receive response from the TCP server",
                )

            table_content = self._extract_and_decode_field(
                response, "[NP]BOARDINFO[EQ]"
            )

            self._enrich_table_content_with_product_names(table_content)
            return table_content
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch table content: {str(e)}"
            )

    def _extract_and_decode_field(self, response: str, field_identifier: str) -> Dict:
        """Extract and decode a Base64 encoded field from the response."""
        encoded_field = self._extract_field(response, field_identifier)
        return self._decode_base64_json(encoded_field)

    def _enrich_table_content_with_product_names(self, table_content: Dict):
        """Enrich the table content with product names using the product cache."""
        for item in table_content.get("content", []):
            item_id = item.get("itemId")
            product = self.products.get(str(item_id)) if item_id else None
            item["itemName"] = product.name if product else "Unknown Product"
            if not product:
                print(f"Product not found for itemId: {item_id}")

    async def fetch_tables(self) -> List[Table]:
        """Fetch a list of tables from the server via TCP."""
        try:
            return await self._fetch_data_list(
                object_type="XDPeople.Entities.MobileBoardStatus", model_class=Table
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch tables: {str(e)}"
            )

    async def post_queue(self, table_id: int) -> str:
        """Send a POSTQUEUE message to close a table's order."""
        try:
            table_content = await self.fetch_table_content(table_id)
            orders = table_content.get("content", [])
            if not orders:
                raise HTTPException(
                    status_code=404, detail="No orders found for the table."
                )

            message = self.message_builder.build_post_queue_message(
                employee_id=int(self.USER_ID), table=table_id, orders=orders
            )
            response = await self._send_message(message)

            if not response:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to receive response from the TCP server",
                )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to post queue: {str(e)}"
            )

    async def close_table(self, table_id: int) -> str:
        """Send a POSTQUEUE message to close the table after payment."""
        try:
            message = self.message_builder.build_close_table_message(
                employee_id=int(self.USER_ID), table=table_id
            )
            response = await self._send_message(message)

            if not response:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to receive response from the TCP server",
                )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to close table: {str(e)}"
            )

    @staticmethod
    def _extract_field(response: str, field_identifier: str) -> str:
        """Extract a Base64 encoded field from the response."""
        start = response.find(field_identifier)
        if start == -1:
            raise ValueError(
                f"No {field_identifier.strip('[').strip(']')} field found in the response"
            )

        encoded_field = response[start + len(field_identifier) :]
        end = (
            encoded_field.find("[NP]")
            if "[NP]" in encoded_field
            else encoded_field.find("[EOM]")
        )
        if end == -1:
            raise ValueError(
                f"End of {field_identifier.strip('[').strip(']')} field not found in the response"
            )
        return encoded_field[:end].strip()

    @staticmethod
    def _decode_base64_json(encoded_str: str) -> Dict:
        """Decode a Base64 encoded JSON string into a dictionary."""
        try:
            decoded_bytes = base64.b64decode(encoded_str)
            return json.loads(decoded_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Error during Base64 decoding or JSON parsing: {e}")
