import uuid
import base64
import json
import time
from typing import Dict, List, Optional


class MessageBuilder:
    # Constants
    ERROR_DESCRIPTION_PARAM = "ERRORDESCRIPTION"
    ERROR_ID_PARAM = "ERRORID"
    APP_VERSION_KEY = "APPVERSION"
    LICENSE_KEY = "LICENSE"
    MESSAGE_GENERIC_ERROR_KEY = "MESSAGEERROR"
    MESSAGE_ID_KEY = "MESSAGEID"
    MESSAGE_OK_KEY = "MESSAGEOK"
    MESSAGE_SERVER_NOT_AUTHORIZED_KEY = "NOTAUTHORIZED"
    MESSAGE_TYPE_KEY = "MESSAGETYPE"
    PENDING_MESSAGES_KEY = "MESSAGES"
    PROTOCOL_VERSION_ID = "PROTOCOLVERSION"
    SERVER_DISCONNECTED_KEY = "SERVERDISCONNECTED"
    SERVER_IDENTIFIER_KEY = "SERVERIDENTIFIER"
    SYNC_VERSION_ID = "SYNCVERSION"
    TOKEN_KEY = "TOKEN"
    USER_ID_KEY = "USERID"

    END_OF_MESSAGE = "[EOM]"
    PARAMETER_KEY = "[NP]"
    PARAMETER_VALUE = "[EQ]"

    # Message Identifiers
    MESSAGE_TYPE_GET_DATA_LIST = "XDPeople.Entities.GetDataListMessage"
    MESSAGE_IDENTIFIER_GET_DATA_LIST = "GETDATALIST"
    MESSAGE_IDENTIFIER_POST_QUEUE = "POSTQUEUE"
    MESSAGE_TYPE_POST_ACTION = "XDPeople.Entities.PostActionMessage"
    MESSAGE_IDENTIFIER_GET_BOARD_CONTENT = "GETBOARDCONTENT"
    MESSAGE_TYPE_GET_BOARD_CONTENT = "XDPeople.Entities.GetBoardInfoMessage"

    def __init__(
        self, user_id: str, app_version: str, protocol_version: str, token: str
    ):
        self.user_id = user_id
        self.app_version = app_version
        self.protocol_version = protocol_version
        self.token = token

    def build_message(
        self,
        message_identifier: str,
        message_type: str,
        parameters: Dict[str, str],
    ) -> str:
        """
        Generic method to construct a message.

        Args:
            message_identifier (str): The identifier of the message (e.g., "GETDATALIST").
            message_type (str): The type of the message (e.g., "XDPeople.Entities.GetDataListMessage").
            parameters (Dict[str, str]): A dictionary of key-value pairs to include in the message.

        Returns:
            str: The constructed message string.
        """
        # Generate a unique MESSAGEID if not already provided
        if self.MESSAGE_ID_KEY not in parameters:
            parameters[self.MESSAGE_ID_KEY] = str(uuid.uuid4())

        # Add common parameters
        parameters[self.MESSAGE_TYPE_KEY] = message_type
        parameters[self.USER_ID_KEY] = self.user_id
        parameters[self.TOKEN_KEY] = self.token
        parameters[self.PROTOCOL_VERSION_ID] = self.protocol_version

        # Construct the message
        message_components = [message_identifier]
        for key, value in parameters.items():
            message_components.append(self.add_message_parameter(key, value))
        message_components.append(self.END_OF_MESSAGE)

        return "".join(message_components)

    def build_get_board_content(self, board_id: str, request_type: int = 1) -> str:
        """
        Constructs the GETBOARDCONTENT message.

        Args:
            board_id (str): The ID of the board to retrieve.
            request_type (int): The type of request (e.g., ONLY_CONTENT, WITH_SUBTOTAL, WITH_STATUS).

        Returns:
            str: The constructed GETBOARDCONTENT message string.
        """
        parameters = {
            "BOARDID": board_id,
            "TYPE": str(request_type),
        }
        return self.build_message(
            message_identifier=self.MESSAGE_IDENTIFIER_GET_BOARD_CONTENT,
            message_type=self.MESSAGE_TYPE_GET_BOARD_CONTENT,
            parameters=parameters,
        )

    def build_post_queue_message(
        self, employee_id: int, table: int, orders: List[Dict], guid: Optional[str] = None
    ) -> str:
        """
        Constructs the POSTQUEUE message with a base64-encoded queue.

        Args:
            employee_id (int): The ID of the employee (same as USER_ID).
            table (int): The ID of the table being closed.
            orders (list): A list of orders for the table.
            guid (str, optional): A unique identifier for the transaction. If not provided, a new UUID will be generated.

        Returns:
            str: The constructed POSTQUEUE message string.
        """
        queue_data = {
            "appVersion": 0,
            "employeeId": employee_id,
            "guid": guid or str(uuid.uuid4()),
            "id": 4,
            "orders": orders,
            "personsNumber": 1,
            "status": 1,
            "table": table,
            "tableLocation": [0, 0],
            "time": int(time.time() * 1000),
            "Action": 1,
        }
        queue_encoded = self._encode_queue(queue_data)

        parameters = {
            "QUEUE": queue_encoded,
        }

        return self.build_message(
            message_identifier=self.MESSAGE_IDENTIFIER_POST_QUEUE,
            message_type=self.MESSAGE_TYPE_POST_ACTION,
            parameters=parameters,
        )

    def build_close_table_message(
        self, employee_id: int, table: int, guid: Optional[str] = None
    ) -> str:
        """
        Constructs the POSTQUEUE message to close the table.

        Args:
            employee_id (int): The ID of the employee (same as USER_ID).
            table (int): The ID of the table being closed.
            guid (str, optional): A unique identifier for the transaction. If not provided, a new UUID will be generated.

        Returns:
            str: The constructed POSTQUEUE message string to close the table.
        """
        queue_data = {
            "appVersion": 0,
            "employeeId": employee_id,
            "guid": guid or str(uuid.uuid4()),
            "id": 5,
            "orders": [],
            "personsNumber": 0,
            "status": 1,
            "table": table,
            "time": int(time.time() * 1000),
            "Action": 3,
        }
        queue_encoded = self._encode_queue(queue_data)

        parameters = {
            "QUEUE": queue_encoded,
        }

        return self.build_message(
            message_identifier=self.MESSAGE_IDENTIFIER_POST_QUEUE,
            message_type=self.MESSAGE_TYPE_POST_ACTION,
            parameters=parameters,
        )

    def build_get_data_list(
        self,
        object_type: str,
        part: int = 0,
        limit: int = 5000,
        message_id: Optional[str] = None,
    ) -> str:
        """
        Constructs the GETDATALIST message.

        Args:
            object_type (str): The type of object to retrieve (e.g., "XDPeople.Entities.MobileItemFamily").
            part (int): The part of the data list to retrieve.
            limit (int): The maximum number of items to retrieve.
            message_id (str, optional): A unique identifier for the message. If not provided, a UUID will be generated.

        Returns:
            str: The constructed GETDATALIST message string.
        """
        parameters = {
            "OBJECTTYPE": object_type,
            "PART": str(part),
            "LIMIT": str(limit),
        }
        if message_id:
            parameters[self.MESSAGE_ID_KEY] = message_id
        return self.build_message(
            message_identifier=self.MESSAGE_IDENTIFIER_GET_DATA_LIST,
            message_type=self.MESSAGE_TYPE_GET_DATA_LIST,
            parameters=parameters,
        )

    def build_get_products(
        self, part: int = 0, limit: int = 5000, message_id: Optional[str] = None
    ) -> str:
        """
        Constructs the GETDATALIST message specifically for retrieving products.

        Args:
            part (int, optional): The part of the data list to retrieve. Defaults to 0.
            limit (int, optional): The maximum number of products to retrieve. Defaults to 5000.
            message_id (str, optional): A unique identifier for the message. If not provided, a UUID will be generated.

        Returns:
            str: The constructed GETDATALIST message string for products.
        """
        return self.build_get_data_list(
            object_type="XDPeople.Entities.MobileItemFamily",
            part=part,
            limit=limit,
            message_id=message_id,
        )

    def _encode_queue(self, queue_data: Dict) -> str:
        """
        Encode the queue data to a base64 string.

        Args:
            queue_data (Dict): The queue data to encode.

        Returns:
            str: The base64-encoded queue string.
        """
        queue_json = json.dumps(queue_data)
        return base64.b64encode(queue_json.encode('utf-8')).decode('utf-8')

    def add_protocol_version(self, protocol_version: str) -> str:
        """
        Adds the protocol version parameter to the message.

        Args:
            protocol_version (str): The protocol version.

        Returns:
            str: Formatted protocol version parameter.
        """
        return self.add_message_parameter(
            self.PROTOCOL_VERSION_ID, protocol_version
        )

    def add_message_parameter(self, key: str, value: str) -> str:
        """
        Formats a message parameter.

        Args:
            key (str): The parameter key.
            value (str): The parameter value.

        Returns:
            str: Formatted message parameter.
        """
        return f"{self.PARAMETER_KEY}{key}{self.PARAMETER_VALUE}{value}"

    # Optional: Retain the encrypt_message method for future use
    def encrypt_message(self, message: str) -> str:
        """Convert each character of the message to its hexadecimal ASCII code representation."""
        return ''.join(format(ord(char), 'x') for char in message)
