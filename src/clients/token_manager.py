import asyncio
import time
import random
from typing import Optional
from threading import Lock
from ..errors.authentication_error import AuthenticationError
from .https_client import HTTPSClient
import logging

# Configure logging
logger = logging.getLogger(__name__)


class TokenManager:
    _instance: Optional["TokenManager"] = None
    _singleton_lock = Lock()  # For thread-safe singleton implementation

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super(TokenManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, use_mock: bool = False):
        if not hasattr(self, "_initialized"):
            self.token: Optional[str] = None
            self.token_expiration: Optional[float] = None  # Epoch time
            self.state = "Unauthenticated"
            self.token_lock = asyncio.Lock()  # For async token access
            self.use_mock = use_mock
            self._initialized = True  # Prevent re-initialization

    async def authenticate(self):
        async with self.token_lock:
            print("State: ", self.state)
            print("Token: ", self.token)
            if (
                self.state == "Authenticated"
                and self.token
                and not self.is_token_expired()
            ):
                print("[TokenManager] Token is still valid.")
                return self.token  # Token is still valid

            self.state = "Authenticating"
            success = await self._perform_authentication()
            if success:
                self.state = "Authenticated"
                print("[TokenManager] Authentication successful.")
                return self.token
            else:
                self.state = "Unauthenticated"
                print("[TokenManager] Authentication failed.")
                raise AuthenticationError()

    async def _perform_authentication(self):
        if self.use_mock:
            # Simulate mock authentication with 50% chance of success
            success = random.choice([True, False])
            if success:
                # Simulate setting a random token
                self.token = f"mock_token_{random.randint(1000,9999)}"
                # Set the token expiration time randomly between 1 and 2 minutes
                random_expiration = random.randint(60, 120)  # seconds
                self.token_expiration = time.time() + random_expiration
                logger.debug(
                    f"Mock token generated, expires in {random_expiration} seconds."
                )
                return True
            else:
                logger.debug("Mock authentication failed.")
                return False
        else:
            # Implement real authentication logic using handle_authentication_and_request
            client = HTTPSClient()
            username = "info@xd.pt"
            password = "xd"
            username_app = "XDBR.105112"
            password_app = "1234"
            client_id = "mobileapps"
            client_secret = ""  # If a client secret is required, add it here.

            # Step 1: Authenticate
            success = client.authenticate(username, password, client_id, client_secret)
            if not success:
                logger.error("Authentication failed in HTTPSClient.")
                return False

            logger.info("Authentication successful in HTTPSClient.")

            # Step 2: Match credentials
            matched_credentials = client.match_credentials(username_app, password_app)
            if not matched_credentials:
                logger.error("Failed to match credentials.")
                return False

            logger.info("Credentials matched successfully.")

            # Step 3: Select the credential with the latest expiration date
            if client.select_by_latest_expiration(matched_credentials):
                # Step 4: Request device configuration
                device_config = client.request_device_configuration()
                if device_config:
                    logger.info("Device configuration received.")
                    # Assuming device_config contains 'access_token' and 'expires_in' fields
                    self.token = (
                        client.access_token
                    )  # Use the access token from HTTPSClient
                    # Set the token expiration time based on actual token lifetime
                    if hasattr(client, "token_expiration") and client.token_expiration:
                        self.token_expiration = client.token_expiration
                    else:
                        # Default to 1 hour if expiration not provided
                        self.token_expiration = time.time() + 3600
                    return True
                else:
                    logger.error("Failed to receive device configuration.")
                    return False
            else:
                logger.error("Failed to select credential by latest expiration date.")
                return False

    def is_token_expired(self):
        # Check if the token is expired
        print("Token expiration: ", self.token_expiration)
        if not self.token_expiration:
            return True
        is_expired = time.time() >= self.token_expiration
        if is_expired:
            logger.warning("Token has expired.")
        else:
            time_left = self.token_expiration - time.time()
            logger.debug(f"Token is valid for {time_left:.2f} more seconds.")
        return is_expired

    async def get_token(self):
        if self.state != "Authenticated" or self.is_token_expired():
            await self.authenticate()
        return self.token
    
    async def is_authenticated(self):
        return self.state == "Authenticated"
