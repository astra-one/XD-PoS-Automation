import requests
import base64
import socket
import json
import uuid
import random
import time
from datetime import datetime, timedelta, timezone


class HTTPSClient:
    _instance = None  # Class-level variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(HTTPSClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, base_url="https://myxd1.azurewebsites.net"):
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
                # self.format_credentials(credentials)
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
            udp_socket.settimeout(5)  # Shorter timeout for faster response
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)  # Enable broadcasting

            print("[Client] Sending device auth request...")
            # Send the device auth request to the broadcast address (255.255.255.255) on port 8978
            udp_socket.sendto(message_bytes, ("255.255.255.255", self.port))
            print("[Client] Device auth request sent.")
            # Receive the response
            start_time = time.time()
            while time.time() - start_time < 5:  # Timeout after 5 seconds
                try:
                    response_bytes, _ = udp_socket.recvfrom(32768)  # Buffer size
                    response_message = response_bytes.decode("utf-8").replace("[EOM]", "")
                    
                    # Parse the response as a DeviceConfiguration
                    device_configuration = json.loads(response_message)
                    print("[Client] Device configuration received:", device_configuration)
                    return device_configuration
                except socket.timeout:
                    continue

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

    
    from datetime import datetime, timedelta, timezone

    def try_all_credentials_until_success(self, credentials):
        """Try each credential, starting with the newest, until one returns a successful device configuration."""

        # Get current UTC time as a timezone-aware datetime (current day, now)
        current_time = datetime.now(timezone.utc)

        # Filter and sort the credentials by expiration date
        sorted_credentials = [
            cred for cred in credentials
            # Check if the expiration date is greater than or equal to the current time
            if datetime.fromtimestamp(cred.get("expirationDate", 0) / 1000, tz=timezone.utc) >= current_time
        ]
        
        # Sort credentials by expiration date, from newest to oldest
        sorted_credentials.sort(key=lambda cred: cred.get("expirationDate", 0), reverse=True)

        print(f"Credentials after filtering for expiration after {current_time}:")

        try:
            for credential in sorted_credentials:
                # Store the selected credential details in class variables
                self.selected_credential_id = credential.get("credentialId")
                self.selected_username = credential.get("username")
                self.selected_terminal = credential.get("terminal")
                self.selected_authorization = credential.get("authorization")
                self.selected_expiration_date = credential.get("expirationDate")
                self.selected_active = credential.get("active")
                self.selected_type = credential.get("type")

                formatted_expiration_date = datetime.fromtimestamp(self.selected_expiration_date / 1000, tz=timezone.utc)
                
                # Attempt to request device configuration
                device_config = self.request_device_configuration()
                if device_config:
                    print("Device configuration received:", device_config)
                    return device_config

            print("[Client] No credentials succeeded in requesting device configuration.")
            return None

        except KeyboardInterrupt:
            print("\n[Client] Operation interrupted by user.")
            return None
            
    def select_by_latest_expiration(self, credentials):
        """Select the credential with the largest expiration date (as an integer)."""
        latest_credential = None
        latest_expiration_date = None

        for credential in credentials:
            expiration_date = credential.get("expirationDate")

            # Check if expiration_date exists and is an integer
            if isinstance(expiration_date, int):
                if (
                    latest_expiration_date is None
                    or expiration_date > latest_expiration_date
                ):
                    latest_expiration_date = expiration_date
                    latest_credential = credential

        if latest_credential:
            # Store the selected credential details in class variables
            self.selected_credential_id = latest_credential.get("credentialId")
            self.selected_username = latest_credential.get("username")
            self.selected_terminal = latest_credential.get("terminal")
            self.selected_authorization = latest_credential.get("authorization")
            self.selected_expiration_date = latest_expiration_date
            self.selected_active = latest_credential.get("active")
            self.selected_type = latest_credential.get("type")

            print(f"\n[Client] Credential with latest expiration date selected:")
            print(f"  Credential ID    : {self.selected_credential_id}")
            print(f"  Username         : {self.selected_username}")
            print(f"  Terminal         : {self.selected_terminal}")
            print(f"  Authorization    : {self.selected_authorization}")
            print(f"  Expiration Date  : {self.selected_expiration_date}")
            print(f"  Active           : {self.selected_active}")
            print(f"  Type             : {self.selected_type}")
            return True

        print("[Client] No credentials found with valid expiration dates.")
        return False

    def add_credentials(self):
        """Generate new credentials and send a POST request to add them to the server."""
        if not self.access_token:
            print("[Client] Error: You must authenticate first.")
            return None

        url = f"{self.base_url}/myxdcredentials"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            # Generate new credential details
            credential_id = str(uuid.uuid4())  # Generate unique credential ID
            username = "XDBR.105112"  # Fixed username
            password = "new_password"  # Could be dynamically set
            terminal = 1  # Fixed terminal as requested
            authorization = str(uuid.uuid4().hex)  # Generate random authorization code
            expiration_date = int(
                (datetime.now() + timedelta(days=365)).timestamp() * 1000
            )  # Expiration date one year from now in milliseconds
            active = False  # Fixed to False
            type = 1  # Fixed to 1

            credentials_data = {
                "credentialId": credential_id,
                "username": username,
                "password": password,
                "terminal": terminal,
                "authorization": authorization,
                "expirationDate": expiration_date,
                "active": active,
                "type": type,
            }

            response = requests.post(url, headers=headers, json=credentials_data)

            print("Response:", response.json())

            if response.status_code == 200:
                print(f"[Client] Credentials added successfully:")
                print(f"  Credential ID    : {credential_id}")
                print(f"  Username         : {username}")
                print(f"  Terminal         : {terminal}")
                print(f"  Authorization    : {authorization}")
                print(f"  Expiration Date  : {expiration_date}")
                print(f"  Active           : {active}")
                print(f"  Type             : {type}")
                return True
            else:
                print(
                    f"[Client] Failed to add credentials with status code {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            print(f"[Client] An error occurred during credential addition: {e}")
            return None

def handle_authentication_and_request(
    username,
    password,
    client_id,
    client_secret,
    username_app,
    password_app,
):
    """
    This function handles the full authentication and credential selection process.

    Args:
        username (str): The username for authentication.
        password (str): The password for authentication.
        client_id (str): The client ID for OAuth.
        client_secret (str): The client secret for OAuth (if required).
        username_app (str): The username for matching credentials.
        password_app (str): The password for matching credentials.

    Returns:
        bool: True if the process completes successfully, False otherwise.
    """
    client = HTTPSClient()

    # Step 1: Authenticate
    success = client.authenticate(username, password, client_id, client_secret)
    if not success:
        print("Authentication failed.")
        return False

    print("Authentication successful!")

    # Step 2: Match credentials
    matched_credentials = client.match_credentials(username_app, password_app)
    if not matched_credentials:
        print("Failed to match credentials.")
        return False

    print("Credentials matched successfully!")

    # Step 3: Select the credential with the latest expiration date
    if client.select_by_latest_expiration(matched_credentials):
        # Step 4: Request device configuration
        device_config = client.request_device_configuration()
        if device_config:
            print("Device configuration received:", device_config)
            return True
        else:
            print("Failed to receive device configuration.")
            return False
    else:
        print("Failed to select credential by latest expiration date.")
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

    handle_authentication_and_request(
        username, password, client_id, client_secret, username_app, password_app
    )
    # Step 1: Authenticate
    # success = client.authenticate(username, password, client_id, client_secret)
    # if success:
    #     print("Authentication successful!")

    #     # Step 2: Add new credentials
    #     client.add_credentials()
    # else:
    #     print("Authentication failed.")