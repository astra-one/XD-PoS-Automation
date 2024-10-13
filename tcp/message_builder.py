import uuid

class MessageBuilder:
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

    def __init__(
        self, user_id: str, app_version: str, protocol_version: str, token: str
    ):
        self.user_id = user_id
        self.app_version = app_version
        self.protocol_version = protocol_version
        self.token = token

    def build_get_board_content(self, board_id: str):
        message_type = "XDPeople.Entities.GetBoardInfoMessage"
        message_id = str(uuid.uuid4())

        # Construct the message
        message = [
            "GETBOARDCONTENT",
            f"{self.new_message_parameter_key}{self.key_protocol_version_identifier}{self.new_message_parameter_value}{self.protocol_version}",
            f"{self.new_message_parameter_key}BOARDID{self.new_message_parameter_value}{board_id}",
            f"{self.new_message_parameter_key}TYPE{self.new_message_parameter_value}{message_type}",
            f"{self.new_message_parameter_key}{self.key_user_id}{self.new_message_parameter_value}{self.user_id}",
            f"{self.new_message_parameter_key}{self.key_token}{self.new_message_parameter_value}{self.token}",
            f"{self.new_message_parameter_key}{self.key_message_type}{self.new_message_parameter_value}{self.key_message_server_not_authorized}",
            f"{self.new_message_parameter_key}{self.key_message_id}{self.new_message_parameter_value}{message_id}{self.new_message_end_of_message}",
        ]

        # Join the message components into a single string
        full_message = "".join(message)

        # Encrypt the message using ASCII code representation
        return self.encrypt_message(full_message)

    def encrypt_message(self, message: str) -> str:
        """Convert each character of the message to its hexadecimal ASCII code representation."""
        hex_encrypted_message = ''.join(format(ord(char), 'x') for char in message)
        return hex_encrypted_message


