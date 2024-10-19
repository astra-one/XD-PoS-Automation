import requests
import base64
import socket
import json
import uuid
import random


class HTTPSClient:
    _instance = None  # Class-level variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(HTTPSClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_url="https://myxd1.azurewebsites.net"):
        # Initialize only if not already initialized
        if not hasattr(self, "_initialized"):
            self.base_url = base_url
            self.auth_url = f"{self.base_url}/oauth/token"
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

    def authenticate(self, username, password, client_id, client_secret):
        """Send the OAuth authentication request and receive the access token."""

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
            response = requests.post(self.auth_url, headers=headers, data=auth_data)

            if response.status_code == 200:
                token = response.json().get("access_token")

                if token:
                    self.access_token = token
                    print(f"[Client] Access token received: {self.access_token}")
                    return True
                else:
                    print("[Client] Authentication failed or token not found.")
            else:
                print(
                    f"[Client] Authentication failed with status code {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            print(f"[Client] An error occurred: {e}")

        return False

    def match_credentials(self, username, password):
        """Send a request to match credentials."""
        if not self.access_token:
            print("[Client] Error: You must authenticate first.")
            return None

        url = f"{self.base_url}/myxdcredentials/match"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        match_data = {
            "user": username,
            "pass": password,
            "appType": "1",  # Replace this with the actual appType value if necessary
        }

        try:
            response = requests.post(url, json=match_data, headers=headers)

            if response.status_code == 200:
                credentials = response.json()
                self.format_credentials(credentials)
                return credentials
            else:
                print(
                    f"[Client] Failed to match credentials with status code {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            print(f"[Client] An error occurred during credential matching: {e}")
            return None

    def format_credentials(self, credentials):
        """Format the matched credentials for better readability."""
        print("\n[Client] Matched Credentials:")
        for idx, credential in enumerate(credentials):
            print(f"\nCredential {idx + 1}:")
            print(f"  Credential ID    : {credential.get('credentialId')}")
            print(f"  Username         : {credential.get('username')}")
            print(f"  Terminal         : {credential.get('terminal')}")
            print(f"  Authorization    : {credential.get('authorization')}")
            print(f"  Expiration Date  : {credential.get('expirationDate')}")
            print(f"  Active           : {credential.get('active')}")
            print(f"  Type             : {credential.get('type')}")
            print("-" * 50)

    def select_active_credential(self, credentials):
        """Select the first credential from the list where 'active' is True."""
        for credential in credentials:
            if credential.get("active"):
                # Store the selected credential details in class variables
                self.selected_credential_id = credential.get("credentialId")
                self.selected_username = credential.get("username")
                self.selected_terminal = credential.get("terminal")
                self.selected_authorization = credential.get("authorization")
                self.selected_expiration_date = credential.get("expirationDate")
                self.selected_active = credential.get("active")
                self.selected_type = credential.get("type")

                print(
                    f"\n[Client] Active Credential {self.selected_credential_id} selected:"
                )
                print(f"  Username         : {self.selected_username}")
                print(f"  Terminal         : {self.selected_terminal}")
                print(f"  Authorization    : {self.selected_authorization}")
                print(f"  Expiration Date  : {self.selected_expiration_date}")
                print(f"  Active           : {self.selected_active}")
                print(f"  Type             : {self.selected_type}")
                return True

        print("[Client] No active credentials found.")
        return False

    def request_device_configuration(self):
        """Request device configuration over UDP using selected credentials."""
        if not self.selected_authorization:
            print("[Client] Error: No authorization code. Select a credential first.")
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

            # Send the device auth request to the broadcast address (255.255.255.255) on port 8978
            udp_socket.sendto(message_bytes, ("255.255.255.255", self.port))

            # Receive the response
            response_bytes, _ = udp_socket.recvfrom(32768)  # Buffer size
            response_message = response_bytes.decode("utf-8").replace("[EOM]", "")

            # Parse the response as a DeviceConfiguration
            device_configuration = json.loads(response_message)
            print("[Client] Device configuration received:", device_configuration)

            # You can now save or process the `device_configuration` as needed
            return device_configuration

        except socket.timeout:
            print("[Client] Error: Request timed out.")
        except Exception as e:
            print(f"[Client] Error occurred while requesting device configuration: {e}")
        finally:
            if udp_socket:
                udp_socket.close()
                print("[Client] UDP socket closed.")

        return None

    def select_random_credential(self, credentials):
        """Randomly select a credential from the list."""
        if not credentials:
            print("[Client] No credentials available to select from.")
            return False

        # Randomly select a credential
        random_credential = random.choice(credentials)

        # Store the selected credential details in class variables
        self.selected_credential_id = random_credential.get("credentialId")
        self.selected_username = random_credential.get("username")
        self.selected_terminal = random_credential.get("terminal")
        self.selected_authorization = random_credential.get("authorization")
        self.selected_expiration_date = random_credential.get("expirationDate")
        self.selected_active = random_credential.get("active")
        self.selected_type = random_credential.get("type")

        print(f"\n[Client] Random Credential {self.selected_credential_id} selected:")
        print(f"  Username         : {self.selected_username}")
        print(f"  Terminal         : {self.selected_terminal}")
        print(f"  Authorization    : {self.selected_authorization}")
        print(f"  Expiration Date  : {self.selected_expiration_date}")
        print(f"  Active           : {self.selected_active}")
        print(f"  Type             : {self.selected_type}")
        return True

    def select_by_id(self, credentials, credential_id):
        """Select a credential by its ID."""
        for credential in credentials:
            if credential.get("credentialId") == credential_id:
                # Store the selected credential details in class variables
                self.selected_credential_id = credential.get("credentialId")
                self.selected_username = credential.get("username")
                self.selected_terminal = credential.get("terminal")
                self.selected_authorization = credential.get("authorization")
                self.selected_expiration_date = credential.get("expirationDate")
                self.selected_active = credential.get("active")
                self.selected_type = credential.get("type")

                print(f"\n[Client] Credential {self.selected_credential_id} selected:")
                print(f"  Username         : {self.selected_username}")
                print(f"  Terminal         : {self.selected_terminal}")
                print(f"  Authorization    : {self.selected_authorization}")
                print(f"  Expiration Date  : {self.selected_expiration_date}")
                print(f"  Active           : {self.selected_active}")
                print(f"  Type             : {self.selected_type}")
                return True

        print(f"[Client] No credential found with ID {credential_id}.")
        return False


# Usage example
if __name__ == "__main__":
    client = HTTPSClient()
    username = "info@xd.pt"
    password = "xd"
    username_app = "XDBR.105112"
    password_app = "1234"
    client_id = "mobileapps"
    client_secret = ""  # If a client secret is required, add it here.

    # Step 1: Authenticate
    success = client.authenticate(username, password, client_id, client_secret)
    if success:
        print("Authentication successful!")

        # Step 2: Match credentials
        matched_credentials = client.match_credentials(username_app, password_app)
        if matched_credentials:
            print("Credentials matched successfully!")

            # # Step 3: Select the first active credential
            # if client.select_active_credential(matched_credentials):
            #     # Step 4: Request device configuration
            #     client.request_device_configuration()

            # # Step 3: Select a random credential
            # if client.select_random_credential(matched_credentials):
            #     # Step 4: Request device configuration
            #     client.request_device_configuration()

            # Step 3: Select a credential by ID
            credential_id = "caf13451-e5d9-492b-9265-85bf9a29b7ad"
            if client.select_by_id(matched_credentials, credential_id):
                # Step 4: Request device configuration
                client.request_device_configuration()

        else:
            print("Failed to match credentials.")
    else:
        print("Authentication failed.")
