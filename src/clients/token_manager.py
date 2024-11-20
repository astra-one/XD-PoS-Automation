import asyncio
import time
import random
from typing import Optional
from threading import Lock
from ..errors.authentication_error import AuthenticationError
from .https_client import HTTPSClient
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
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

    def __init__(self, use_mock: bool = False, url: str = "http://localhost:8001"):
        if not hasattr(self, "_initialized"):
            self.token: Optional[str] = None
            self.token_expiration: Optional[float] = None  # Epoch time
            self.state = "Unauthenticated"
            self.token_lock = asyncio.Lock()  # For async token access
            self.use_mock = use_mock
            self._initialized = True  # Prevent re-initialization
            logger.info(f"URL: {url}")
            self._url = url

    async def authenticate(self):
        logger.info(f"State: {self.state}")
        logger.info(f"Token: {self.token}")
        if (
            self.state == "Authenticated"
            and self.token
            and not self.is_token_expired()
        ):
            logger.info("[TokenManager] Token is still valid.")
            return self.token  # Token is still valid

        self.state = "Authenticating"
        logger.info("[TokenManager] Starting authentication process.")
        success = await self._perform_authentication()
        if success:
            self.state = "Authenticated"
            logger.info("[TokenManager] Authentication successful.")
            return self.token
        else:
            self.state = "Unauthenticated"
            logger.error("[TokenManager] Authentication failed.")
            raise AuthenticationError("Authentication failed.")

    async def _perform_authentication(self):
        if self.use_mock:
            # Simulate mock authentication with 50% chance of success
            success = random.choice([True, False])
            if success:
                # Simulate setting a random token
                self.token = f"mock_token_{random.randint(1000, 9999)}"
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
            # Perform authentication and token generation
            try:
                client = HTTPSClient()
                username = "info@xd.pt"
                password = "xd"
                username_app = "XDBR.105112"
                password_app = "1234"
                client_id = "mobileapps"
                client_secret = ""  # Replace with the actual client secret if required

                # Authenticate
                success = client.authenticate(username, password, client_id, client_secret)
                if not success:
                    logger.error("Authentication failed in HTTPSClient.")
                    return False
                logger.info("Authentication successful in HTTPSClient.")

                # Create a new credential
                new_credential = client.create_new_credential(username_app, password_app)
                if not new_credential:
                    logger.error("Failed to create a new credential.")
                    return False
                logger.info("New credential created.")

                # Request device configuration using the new credential
                device_config = client.request_device_configuration()
                if device_config:
                    logger.info("Device configuration received.")
                    # Use the token from device configuration
                    self.token = device_config.get("Token")
                    # Set the token expiration time (e.g., 1 day from now)
                    token_expiration = datetime.utcnow() + timedelta(days=1)
                    self.token_expiration = token_expiration.timestamp()
                    return True
                else:
                    logger.error("Failed to receive device configuration.")
                    return False
            except Exception as e:
                logger.error(f"Error authenticating: {e}", exc_info=True)
                return False


    def is_token_expired(self):
        # Check if the token is expired
        logger.info(f"Token expiration: {self.token_expiration}")
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
        # Lock access to the token to ensure a single authentication
        logger.info(f"State: {self.state}")
        async with self.token_lock:
            logger.debug("Entering get_token - Current state: %s", self.state)

            # If already authenticated and token is valid, return the token directly
            if self.state == "Authenticated" and not self.is_token_expired():
                logger.debug("Token is valid and authenticated, returning token.")
                return self.token

            # If authentication is already in progress, wait until it completes
            if self.state == "Authenticating":
                logger.debug(
                    "Authentication already in progress, waiting for it to complete."
                )
                while self.state == "Authenticating":
                    await asyncio.sleep(0.1)  # Briefly wait before checking again
                # After waiting, check if the state is now authenticated
                if self.state == "Authenticated" and not self.is_token_expired():
                    logger.debug(
                        "Authentication completed by another process, returning token."
                    )
                    return self.token
                else:
                    # If authentication failed, raise an error
                    logger.error("Authentication failed during wait.")
                    raise AuthenticationError("Authentication failed during wait.")

            # Otherwise, start a new authentication
            logger.debug("Starting new authentication process.")
            self.state = "Authenticating"
            try:
                await self.authenticate()
                logger.debug("Authentication process completed, returning token.")
                return self.token
            except AuthenticationError as e:
                logger.error(f"Authentication error: {e}")
                raise

    async def is_authenticated(self):
        return self.state == "Authenticated"
