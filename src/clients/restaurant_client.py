import asyncio
import uuid
import base64
import json
import time
import logging
from typing import Dict, List, Type, Optional
from fastapi import HTTPException
from .token_manager import TokenManager
from .tcp_client import TCPClient
from ..builders.pos_message_builder import MessageBuilder
from ..models.entity_models import Product, Table

# Configure the logger
logger = logging.getLogger("RestaurantClient")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of log messages

# Create handlers
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Adjust as needed

file_handler = logging.FileHandler("restaurant_client.log")
file_handler.setLevel(logging.INFO)  # File handler can be set to INFO or higher

# Create formatters and add them to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)


class RestaurantClient:
    _instance: Optional["RestaurantClient"] = None

    # Class-level constants
    USER_ID: str = "1"
    APP_VERSION: str = "1.0"
    PROTOCOL_VERSION: str = "1"
    TOKEN: str = ""
    LIMIT: int = 5000

    message_builder: MessageBuilder
    products: Dict[str, Product]
    token_manager: TokenManager

    def __new__(cls, token_manager: TokenManager):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.products = {}
            cls._instance.message_builder = MessageBuilder(
                user_id=cls.USER_ID,
                app_version=cls.APP_VERSION,
                protocol_version=cls.PROTOCOL_VERSION,
            )
            cls._instance.token_manager = token_manager
            logger.debug("RestaurantClient instance created.")
        return cls._instance

    def __init__(self, token_manager: TokenManager):
        if not self.products:
            logger.debug("Initializing product cache.")
            asyncio.run(self.load_products())
        self.token_manager: TokenManager = token_manager

    async def load_products(self):
        """Load products and store them in the cache."""
        logger.info("Loading products into cache.")
        try:
            products = await self._fetch_data_list(
                object_type="XDPeople.Entities.MobileItem", model_class=Product
            )
            self.products = {str(product.id): product for product in products}
            logger.info(f"Product cache initialized with {len(self.products)} items.")
        except Exception as e:
            logger.error(f"Failed to load products: {e}", exc_info=True)
            raise

    async def _fetch_product(self, product_id: str) -> Optional[Product]:
        """Fetch a product from the cache by ID, reloading if necessary."""
        if not self.products:
            logger.warning("Product cache is empty. Attempting to reload products.")
            try:
                await self.load_products()
            except Exception as e:
                logger.error(f"Failed to reload products: {e}", exc_info=True)
                return None

        product = self.products.get(product_id)
        if not product:
            logger.warning(f"Product not found in cache for product_id: {product_id}")
        return product

    async def _fetch_data_list(self, object_type: str, model_class: Type) -> List:
        """Generic method to fetch a list of data from the server via TCP."""
        message = await self.message_builder.build_get_data_list(
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
        except ValueError as e:
            # Verifica se a exceção diz respeito ao campo "[NP]OBJECT[EQ]" não encontrado
            if "No NP]OBJECT[EQ field found in the response" in str(e):
                # Marca o token como não autenticado
                await self.token_manager.set_unauthenticated()
                raise HTTPException(
                    status_code=401,
                    detail="Authentication error: token expired or invalid",
                )
            # Se não for esse caso específico, trata como erro genérico
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decode or process the response: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to decode or process the response: {str(e)}",
            )

    async def _send_message(self, message: str) -> Optional[str]:
        """Send a message to the TCP server and return the response."""
        logger.debug(f"Sending message to TCP server: {message}")
        with TCPClient() as client:
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(None, client.send_data, message)
                logger.debug(f"Received response: {response}")

                if self._is_authentication_error(response):
                    logger.warning("Authentication error detected in response.")
                    await self.token_manager.set_unauthenticated()
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication error: token expired or invalid",
                    )
                return response
            except Exception as e:
                logger.error(f"Failed to send message: {e}", exc_info=True)
                await self.token_manager.set_unauthenticated()
                raise HTTPException(
                    status_code=500, detail=f"Failed to send message: {e}"
                )

    def _is_authentication_error(self, response: str) -> bool:
        """Check if the response indicates an authentication error."""
        auth_error = "AuthError" in response  # Replace with actual auth error indicator
        if auth_error:
            logger.debug("Authentication error found in response.")
        return auth_error

    async def fetch_table_content(self, table_id: int) -> Dict:
        """Fetch content for a specific table and enrich it with product names."""
        logger.info(f"Fetching content for table ID: {table_id}")
        try:
            message = await self.message_builder.build_get_board_content(
                board_id=str(table_id)
            )
            response = await self._send_message(message)

            if not response:
                logger.error(
                    "No response received from TCP server while fetching table content."
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to receive response from the TCP server",
                )

            logger.debug(f"Response: {response}")

            table_content = self._extract_and_decode_field(
                response, "[NP]BOARDINFO[EQ]"
            )
            logger.debug(f"Raw table content: {table_content}")

            # Call the enriched method (updated to use _fetch_product)
            await self._enrich_table_content_with_product_names(table_content)
            logger.info(f"Enriched table content for table ID {table_id}.")
            return table_content
        except Exception as e:
            logger.error(f"Failed to fetch table content: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch table content: {str(e)}"
            )

    def _extract_and_decode_field(self, response: str, field_identifier: str) -> Dict:
        """Extract and decode a Base64 encoded field from the response."""
        logger.debug(f"Extracting field '{field_identifier}' from response.")
        encoded_field = self._extract_field(response, field_identifier)
        decoded = self._decode_base64_json(encoded_field)
        logger.debug(f"Decoded field '{field_identifier}': {decoded}")
        return decoded

    async def _enrich_table_content_with_product_names(self, table_content: Dict):
        """Enrich the table content with product names using the product cache."""
        logger.debug("Enriching table content with product names.")
        for item in table_content.get("content", []):
            item_id = item.get("itemId")
            if not item_id:
                logger.warning("Item ID is missing in table content.")
                item["itemName"] = "Unknown Product"
                continue

            product = await self._fetch_product(str(item_id))
            item["itemName"] = product.name if product else "Unknown Product"

    async def fetch_tables(self) -> List[Table]:
        """Fetch a list of tables from the server via TCP."""
        logger.info("Fetching list of tables.")
        try:
            tables = await self._fetch_data_list(
                object_type="XDPeople.Entities.MobileBoardStatus", model_class=Table
            )
            logger.info(f"Fetched {len(tables)} tables.")
            return tables
        except Exception as e:
            logger.error(f"Failed to fetch tables: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch tables: {str(e)}"
            )

    async def prebill(self, table_id: int) -> str:
        """Send a POSTQUEUE message to close a table's order."""
        logger.info(f"Initiating prebill for table ID: {table_id}")
        try:
            table_content = await self.fetch_table_content(table_id)
            orders = table_content.get("content", [])
            if not orders:
                logger.warning(f"No orders found for table ID: {table_id}")
                raise HTTPException(
                    status_code=404, detail="No orders found for the table."
                )

            message = await self.message_builder.build_prebill_message(
                employee_id=int(self.USER_ID), table=table_id, orders=orders
            )
            response = await self._send_message(message)

            if not response:
                logger.error(
                    "No response received from TCP server while sending prebill."
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to receive response from the TCP server",
                )

            logger.info(f"Prebill response for table ID {table_id}: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to post queue: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to post queue: {str(e)}"
            )

    async def close_table(self, table_id: int) -> str:
        """Send a POSTQUEUE message to close the table after payment."""
        logger.info(f"Closing table ID: {table_id}")
        try:
            message = await self.message_builder.build_close_table_message(
                employee_id=int(self.USER_ID), table=table_id
            )
            logger.debug(f"Close Table Message: {message}")
            response = await self._send_message(message)

            if not response:
                logger.error(
                    "No response received from TCP server while closing table."
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to receive response from the TCP server",
                )

            logger.info(f"Close table response for table ID {table_id}: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to close table: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to close table: {str(e)}"
            )

    @staticmethod
    def _extract_field(response: str, field_identifier: str) -> str:
        """Extract a Base64 encoded field from the response."""
        logger.debug(f"Extracting field '{field_identifier}' from response.")
        start = response.find(field_identifier)
        if start == -1:
            error_msg = f"No {field_identifier.strip('[').strip(']')} field found in the response"
            logger.error(error_msg)
            raise ValueError(error_msg)

        encoded_field = response[start + len(field_identifier) :]
        end = (
            encoded_field.find("[NP]")
            if "[NP]" in encoded_field
            else encoded_field.find("[EOM]")
        )
        if end == -1:
            error_msg = f"End of {field_identifier.strip('[').strip(']')} field not found in the response"
            logger.error(error_msg)
            raise ValueError(error_msg)

        extracted = encoded_field[:end].strip()
        logger.debug(f"Extracted encoded field: {extracted}")
        return extracted

    @staticmethod
    def _decode_base64_json(encoded_str: str) -> Dict:
        """Decode a Base64 encoded JSON string into a dictionary."""
        logger.debug("Decoding Base64 JSON string.")
        try:
            decoded_bytes = base64.b64decode(encoded_str)
            decoded_str = decoded_bytes.decode("utf-8")
            decoded_json = json.loads(decoded_str)
            logger.debug(f"Decoded JSON: {decoded_json}")
            return decoded_json
        except Exception as e:
            error_msg = f"Error during Base64 decoding or JSON parsing: {e}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
