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
        # Removed the lock acquisition here to prevent deadlock
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
        print("[TokenManager] Starting authentication process.")
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
            # Real authentication logic using HTTPSClient
            client = HTTPSClient()
            username = "info@xd.pt"
            password = "xd"
            username_app = "XDBR.105112"
            password_app = "1234"
            client_id = "mobileapps"
            client_secret = ""  # If a client secret is required, add it here.

            # Step 1: Authenticate
            print("Autenticando")
            success = client.authenticate(username, password, client_id, client_secret)
            if not success:
                logger.error("Authentication failed in HTTPSClient.")
                return False

            logger.info("Authentication successful in HTTPSClient.")

            # Step 2: Match credentials
            print("Match credentials")
            matched_credentials = client.match_credentials(username_app, password_app)
            if not matched_credentials:
                logger.error("Failed to match credentials.")
                return False

            logger.info("Credentials matched successfully.")

            # Step 3: Try each credential until one works
            device_config = client.try_all_credentials_until_success(matched_credentials)
            if device_config:
                logger.info("Device configuration received.")

                # Use the access token from HTTPSClient
                self.token = device_config["Token"]

                # Set the token expiration time based on actual token lifetime
                if hasattr(client, "token_expiration") and client.token_expiration:
                    self.token_expiration = client.token_expiration
                else:
                    # Default to 1 day if no expiration time is provided
                    self.token_expiration = time.time() + 86400  # 1 day
                return True
            else:
                logger.error("Failed to receive device configuration with all credentials.")
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
        # Bloqueia o acesso ao token para garantir uma única autenticação
        print("State: ", self.state)
        print("Token Lock: ", self.token_lock)
        async with self.token_lock:
            print("Salve")
            logger.debug("Entering get_token - Current state: %s", self.state)

            # Se já está autenticado e o token ainda é válido, retorna o token diretamente
            if self.state == "Authenticated" and not self.is_token_expired():
                logger.debug("Token is valid and authenticated, returning token.")
                return self.token

            # Se a autenticação já está em progresso, espera que o estado mude para "Authenticated" ou "Unauthenticated"
            if self.state == "Authenticating":
                logger.debug("Authentication already in progress, waiting for it to complete.")
                while self.state == "Authenticating":
                    await asyncio.sleep(0.1)  # Espera brevemente antes de verificar novamente
                # Após a espera, verifica se o estado agora é autenticado
                if self.state == "Authenticated":
                    logger.debug("Authentication completed by another process, returning token.")
                    return self.token
                else:
                    # Se a autenticação falhou, tenta iniciar uma nova autenticação
                    logger.debug("Previous authentication attempt failed, retrying.")
                    self.state = "Authenticating"
                    await self.authenticate()
                    return self.token

            # Caso contrário, inicia uma nova autenticação
            logger.debug("Starting new authentication process.")
            self.state = "Authenticating"
            print("Começou")
            await self.authenticate()
            logger.debug("Authentication process completed, returning token.")
            return self.token

    async def is_authenticated(self):
        return self.state == "Authenticated"
