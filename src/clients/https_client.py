from datetime import datetime, timedelta
import hashlib
import uuid
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
import base64
import socket
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HTTPSClient:
    _instance = None  # Class-level variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HTTPSClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_url="https://myxd1.azurewebsites.net"):
        if not hasattr(self, "_initialized"):
            self.base_url = base_url
            self.auth_url = f"{self.base_url}/oauth/token"
            self.credentials_url = f"{self.base_url}/myxdcredentials"
            self.access_token = None
            self.port = 8978

            # Variables to store selected credential details
            self.selected_credential_id = None
            self.selected_username = None
            self.selected_terminal = None
            self.selected_authorization = None
            self.selected_expiration_date = None
            self.selected_active = None
            self.selected_type = None

            self._initialized = True  # Flag to prevent re-initialization

    def authenticate(
        self, username: str, password: str, client_id: str, client_secret: str
    ) -> bool:
        """Authenticate and retrieve an access token."""
        client_credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(client_credentials.encode()).decode(
            "utf-8"
        )

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        auth_data = {
            "username": username,
            "password": password,
            "client_id": client_id,
            "grant_type": "password",
        }

        try:
            logger.info("Starting authentication process...")
            response = requests.post(
                self.auth_url, headers=headers, data=auth_data, timeout=10
            )
            response.raise_for_status()  # Raises HTTPError for bad responses

            token = response.json().get("access_token")

            if token:
                self.access_token = token
                logger.info("[Client] Access token received.")
                return True
            else:
                logger.error("[Client] Authentication failed or token not found.")
                return False

        except HTTPError as http_err:
            logger.error(f"[Client] HTTP error occurred: {http_err}")
        except ConnectionError:
            logger.error("[Client] Connection error. Please check your network.")
        except Timeout:
            logger.error("[Client] Request timed out.")
        except RequestException as req_err:
            logger.error(f"[Client] Request exception: {req_err}")
        except Exception as e:
            logger.error(f"[Client] An unexpected error occurred: {e}", exc_info=True)

        return False

    def create_new_credential(self, username_app: str, password_app: str):
        """Create a new credential and obtain its authorization code."""
        if not self.access_token:
            logger.error("[Client] Error: You must authenticate first.")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        expiration_date_ms = int(
            (datetime.utcnow() + timedelta(days=1)).timestamp() * 1000
        )

        credentials_id = str(uuid.uuid4())
        terminal = 1  # Replace with actual terminal number if needed

        authorization_code = self.generate_authorization(
            username_app, terminal, credentials_id
        )

        payload = {
            "CredentialId": credentials_id,
            "Username": username_app,
            "Password": password_app,
            "Terminal": terminal,
            "Authorization": authorization_code,
            "ExpirationDate": expiration_date_ms,
            "Device": None,
            "Type": 1,
            "Active": False,
            "ModelType": "XDPeople.Entities.MyXDCredentials, XDPeople.NET, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null",
        }

        try:
            logger.info("Creating a new credential...")
            response = requests.post(
                self.credentials_url, headers=headers, json=payload, timeout=10
            )
            response.raise_for_status()  # Raises HTTPError for bad responses
            logger.info("[Client] New credential created successfully.")

            credential = response.json()
            self.selected_credential_id = credential.get("credentialId")
            self.selected_authorization = credential.get("authorization")
            return credential

        except HTTPError as http_err:
            logger.error(f"[Client] HTTP error occurred: {http_err}")
        except ConnectionError:
            logger.error("[Client] Connection error. Please check your network.")
        except Timeout:
            logger.error("[Client] Request timed out.")
        except RequestException as req_err:
            logger.error(f"[Client] Request exception: {req_err}")
        except Exception as e:
            logger.error(
                f"[Client] An unexpected error occurred: {e}", exc_info=True
            )

        return None

    def request_device_configuration(self):
        """Request device configuration over UDP using the new credential."""
        if not self.selected_authorization:
            logger.error(
                "[Client] Error: No authorization code. Create a credential first."
            )
            return None

        udp_socket = None
        try:
            # Generate a random device ID (UUID)
            device_id = str(uuid.uuid4())
            alias = "Coti"  # Fixed alias

            # Prepare the DeviceAuthenticationRequest
            device_auth_request = {
                "applicationId": 1,  # Example app ID, replace with actual
                "authorizationCode": self.selected_authorization,
                "deviceId": device_id,
                "alias": alias,
            }

            # Convert the request to JSON and append the [EOM] marker
            message = json.dumps(device_auth_request) + "[EOM]"
            message_bytes = message.encode("utf-8")

            # Send the message over UDP
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.settimeout(5)  # Timeout after 5 seconds
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Send the device auth request to the broadcast address on port 8978
            udp_socket.sendto(message_bytes, ("255.255.255.255", self.port))

            # Receive the response
            response_bytes, _ = udp_socket.recvfrom(32768)  # Buffer size
            response_message = response_bytes.decode("utf-8").replace("[EOM]", "")

            # Parse the response as a DeviceConfiguration
            device_configuration = json.loads(response_message)
            logger.info("[Client] Device configuration received.")
            return device_configuration

        except socket.timeout:
            logger.error("[Client] Error: Request timed out.")
        except socket.error as sock_err:
            logger.error(f"[Client] Socket error: {sock_err}")
        except Exception as e:
            logger.error(
                f"[Client] Error occurred while requesting device configuration: {e}",
                exc_info=True,
            )
        finally:
            if udp_socket:
                udp_socket.close()
                logger.info("[Client] UDP socket closed.")

        return None

    @staticmethod
    def generate_authorization(username, terminal, credential_id):
        # Concatenate the fields in a specific order
        data = f"{username}{terminal}{credential_id}"

        # Hash the concatenated string using MD5
        authorization = hashlib.md5(data.encode()).hexdigest()
        return authorization


# Usage example
if __name__ == "__main__":
    client = HTTPSClient()
    username = "info@xd.pt"
    password = "xd"
    username_app = "XDBR.105112"
    password_app = "1234"
    client_id = "mobileapps"
    client_secret = ""  # Replace with the actual client secret if required

    # Authenticate
    if client.authenticate(username, password, client_id, client_secret):
        logger.info("Authentication successful!")

        # Create a new credential
        new_credential = client.create_new_credential(username_app, password_app)
        if new_credential:
            logger.info("New credential created:")
            logger.info(new_credential)

            # Request device configuration using the new credential
            device_config = client.request_device_configuration()
            if device_config:
                logger.info("Device configuration received:")
                logger.info(device_config)
            else:
                logger.error("Failed to receive device configuration.")
        else:
            logger.error("Failed to create a new credential.")
    else:
        logger.error("Authentication failed.")
