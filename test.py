from datetime import datetime, timedelta
import hashlib
import uuid
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
import base64
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
            self._initialized = True  # Prevent re-initialization

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

    def request_credentials(self):
        """Make a POST request to the /myxdcredentials endpoint using the Bearer token."""
        if not self.access_token:
            logger.error("[Client] Error: You must authenticate first.")
            return None

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        print("Access token:", self.access_token)

        expiration_date_ms = int(
            (datetime.utcnow() + timedelta(days=1)).timestamp() * 1000
        )

        credentials_id = str(uuid.uuid4())

        print("ExpirationDate (ms since epoch):", expiration_date_ms)

        payload = {
            "CredentialId": credentials_id,
            "Username": "XDBR.105112",
            "Password": "1234",
            "Terminal": 1,
            "Authorization": generate_authorization("XDBR.105112", 1, credentials_id),
            "ExpirationDate": expiration_date_ms,
            "Device": None,
            "Type": 1,
            "Active": False,
            "ModelType": "XDPeople.Entities.MyXDCredentials, XDPeople.NET, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null",
        }

        try:
            logger.info("Sending POST request to /myxdcredentials...")
            response = requests.post(
                self.credentials_url, headers=headers, timeout=10, json=payload
            )
            response.raise_for_status()  # Raises HTTPError for bad responses
            logger.info("[Client] Request to /myxdcredentials was successful.")
            return response.json()

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

        return None

    def revoke_token(self, token: str) -> bool:
        """
        Revoke the given token to prevent further use.

        Args:
            token (str): The access token to revoke.

        Returns:
            bool: True if revocation was successful, False otherwise.
        """
        if not token:
            logger.error("[Client] Error: Token is required for revocation.")
            return False

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        revoke_url = f"{self.base_url}/myxdcredentials/{token}"

        try:
            logger.info(f"Revoking token: {token[:10]}... (truncated for security)")
            response = requests.delete(revoke_url, headers=headers, timeout=10)
            response.raise_for_status()  # Raises HTTPError for bad responses

            logger.info("[Client] Token revoked successfully.")
            return True

        except HTTPError as http_err:
            logger.error(
                f"[Client] HTTP error occurred during token revocation: {http_err}"
            )
        except ConnectionError:
            logger.error("[Client] Connection error. Please check your network.")
        except Timeout:
            logger.error("[Client] Request timed out.")
        except RequestException as req_err:
            logger.error(
                f"[Client] Request exception during token revocation: {req_err}"
            )
        except Exception as e:
            logger.error(
                f"[Client] An unexpected error occurred during token revocation: {e}",
                exc_info=True,
            )

        return False


def generate_authorization(username, terminal, credential_id):
    # Concatenate the fields in a specific order
    data = f"{username}{terminal}{credential_id}"

    # Hash the concatenated string using MD5
    authorization = hashlib.md5(data.encode()).hexdigest()
    return authorization


if __name__ == "__main__":
    client = HTTPSClient()
    username = "info@xd.pt"
    password = "xd"
    client_id = "mobileapps"
    client_secret = ""  # Replace with the actual client secret

    # Authentication step
    if client.authenticate(username, password, client_id, client_secret):
        logger.info("Authentication successful!")

        # Request credentials
        response = client.revoke_token("f41e9b59-b578-44b3-bb58-efd3a8cb01cc")
        if response:
            logger.info("Response received:")
            logger.info(response)
        else:
            logger.error("Failed to retrieve credentials.")
    else:
        logger.error("Authentication failed.")
