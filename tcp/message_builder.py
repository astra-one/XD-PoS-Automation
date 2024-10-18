import uuid


class MessageBuilder:
    # Retained Constants
    error_description_parameter = "ERRORDESCRIPTION"
    error_id_parameter = "ERRORID"
    key_application_version = "APPVERSION"
    key_license = "LICENSE"
    key_message_generic_error = "MESSAGEERROR"
    key_message_id = "MESSAGEID"
    key_message_ok = "MESSAGEOK"
    key_message_server_not_authorized = "NOTAUTHORIZED"
    key_message_type = "MESSAGETYPE"
    key_pending_messages = "MESSAGES"
    key_protocol_version_identifier = "PROTOCOLVERSION"
    key_server_disconnected = "SERVERDISCONNECTED"
    key_server_identifier = "SERVERIDENTIFIER"
    key_sync_version_identifier = "SYNCVERSION"
    key_token = "TOKEN"
    key_user_id = "USERID"
    new_message_end_of_message = "[EOM]"
    new_message_parameter_key = "[NP]"
    new_message_parameter_value = "[EQ]"

    # New Constants for GETDATALIST
    key_object_type = "OBJECTTYPE"
    key_part = "PART"
    key_limit = "LIMIT"
    message_type_get_data_list = "XDPeople.Entities.GetDataListMessage"
    message_identifier_get_data_list = "GETDATALIST"

    def __init__(
        self, user_id: str, app_version: str, protocol_version: str, token: str
    ):
        self.user_id = user_id
        self.app_version = app_version
        self.protocol_version = protocol_version
        self.token = token

    def build_get_board_content(self, board_id: str, request_type: int = 1):
        """
        Constructs the GETBOARDCONTENT message.

        Args:
            board_id (str): The ID of the board to retrieve.
            request_type (int): The type of request (e.g., ONLY_CONTENT, WITH_SUBTOTAL, WITH_STATUS).

        Returns:
            str: The constructed GETBOARDCONTENT message string.
        """
        # Message Identifier
        message_identifier = "GETBOARDCONTENT"

        # Generate a unique MESSAGEID
        message_id = str(uuid.uuid4())

        # Define the message type for GETBOARDCONTENT
        message_type = "XDPeople.Entities.GetBoardInfoMessage"

        # Construct the message components
        message_components = [
            message_identifier,
            self.add_protocol_version(self.protocol_version),
            self.add_message_parameter("BOARDID", board_id),
            self.add_message_parameter("TYPE", str(request_type)),
            self.add_message_parameter(self.key_user_id, self.user_id),
            self.add_message_parameter(self.key_token, self.token),
            self.add_message_parameter(
                self.key_message_type, message_type
            ),  # Add MESSAGETYPE
            self.add_message_parameter(self.key_message_id, message_id),
            self.new_message_end_of_message,
        ]

        # Join all components into a single string
        full_message = "".join(message_components)

        # Return the message without encryption
        return full_message

    def build_get_data_list(
        self,
        object_type: str,
        part: int = 0,
        limit: int = 5000,
        message_id: str = None,
    ):
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
        # Use provided MESSAGEID or generate a new one
        if message_id is None:
            message_id = str(uuid.uuid4())

        # Message Identifier
        message_identifier = self.message_identifier_get_data_list

        # Construct the message components
        message_components = [
            message_identifier,
            self.add_protocol_version(self.protocol_version),
            self.add_message_parameter(self.key_object_type, object_type),
            self.add_message_parameter(self.key_part, str(part)),
            self.add_message_parameter(self.key_limit, str(limit)),
            self.add_message_parameter(self.key_user_id, self.user_id),
            self.add_message_parameter(self.key_token, self.token),
            self.add_message_parameter(
                self.key_message_type, self.message_type_get_data_list
            ),
            self.add_message_parameter(self.key_message_id, message_id),
            self.new_message_end_of_message,
        ]

        # Join all components into a single string
        full_message = "".join(message_components)

        # Return the message without encryption
        return full_message

    def build_get_products(
        self, part: int = 0, limit: int = 5000, message_id: str = None
    ):
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

    def add_protocol_version(self, protocol_version: str) -> str:
        """
        Adds the protocol version parameter to the message.

        Args:
            protocol_version (str): The protocol version.

        Returns:
            str: Formatted protocol version parameter.
        """
        return f"{self.new_message_parameter_key}{self.key_protocol_version_identifier}{self.new_message_parameter_value}{protocol_version}"

    def add_message_parameter(self, key: str, value: str) -> str:
        """
        Formats a message parameter.

        Args:
            key (str): The parameter key.
            value (str): The parameter value.

        Returns:
            str: Formatted message parameter.
        """
        return f"{self.new_message_parameter_key}{key}{self.new_message_parameter_value}{value}"

    # Optional: Retain the encrypt_message method for future use
    def encrypt_message(self, message: str) -> str:
        """Convert each character of the message to its hexadecimal ASCII code representation."""
        hex_encrypted_message = "".join(format(ord(char), "x") for char in message)
        return hex_encrypted_message
