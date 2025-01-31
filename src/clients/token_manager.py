import asyncio
from http.client import HTTPException
import time
import random
from typing import Optional
from threading import Lock
from .https_client import HTTPSClient
import logging
from datetime import datetime, timedelta
import json
import os

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
            self.token_expiration: Optional[float] = None  # Use float para timestamp
            self.state = "Authenticated" if self.token else "Unauthenticated"
            self.token_lock = asyncio.Lock()  # For async token access
            self.use_mock = use_mock
            self._url = url
            self._state_file = "token_manager_state.json"  # Nome do arquivo de estado
            self._load_token_from_file()  # Tenta carregar o token do arquivo
            self._initialized = True  # Prevent re-initialization
            logger.info(f"URL: {url}")

    def _load_token_from_file(self):
        """Carrega o token e a data de expiração do arquivo JSON, se existir."""
        if os.path.exists(self._state_file):
            try:
                with open(self._state_file, "r") as f:
                    data = json.load(f)
                    self.token = data.get("token")
                    self.token_expiration = data.get("token_expiration")
                    logger.info("Token carregado do arquivo.")
                    if self.token and not self.is_token_expired():
                        self.state = "Authenticated"
                        logger.info("Token válido carregado. Estado definido como 'Authenticated'.")
                    else:
                        logger.info("Token expirado ou inválido no arquivo.")
                        self.token = None
                        self.token_expiration = None
                        self.state = "Unauthenticated"
                        self._delete_token_file()
            except Exception as e:
                logger.error(f"Erro ao carregar o token do arquivo: {e}")
                self.token = None
                self.token_expiration = None
                self.state = "Unauthenticated"
                self._delete_token_file()
        else:
            logger.info("Arquivo de estado do token não encontrado. Estado definido como 'Unauthenticated'.")

    def _save_token_to_file(self):
        """Salva o token e a data de expiração no arquivo JSON."""
        try:
            with open(self._state_file, "w") as f:
                json.dump({
                    "token": self.token,
                    "token_expiration": self.token_expiration
                }, f)
            logger.info("Token salvo no arquivo com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao salvar o token no arquivo: {e}")

    def _delete_token_file(self):
        """Remove o arquivo de estado do token, se existir."""
        try:
            if os.path.exists(self._state_file):
                os.remove(self._state_file)
                logger.info("Arquivo de estado do token removido.")
        except Exception as e:
            logger.error(f"Erro ao remover o arquivo de estado do token: {e}")

    async def authenticate(self):
        logger.info(f"[TokenManager] State: {self.state}")
        logger.info(f"[TokenManager] Token: {self.token}")
        if self.state == "Authenticated" and self.token and not self.is_token_expired():
            logger.info("[TokenManager] Token is still valid.")
            return self.token  # Token is still valid

        self.state = "Authenticating"
        logger.info("[TokenManager] Starting authentication process.")
        success = await self._perform_authentication()
        if success:
            self.state = "Authenticated"
            logger.info("[TokenManager] Authentication successful.")
            self._save_token_to_file()  # Salva o token após sucesso
            return self.token
        else:
            self.state = "Unauthenticated"
            logger.error("[TokenManager] Authentication failed.")
            self._delete_token_file()  # Remove o arquivo se a autenticação falhar
            raise HTTPException(status_code=401, detail="Authentication failed.")

    async def _perform_authentication(self):
        if self.use_mock:
            # Simulate mock authentication with 50% chance of success
            success = random.choice([True, True])
            if success:
                # Simulate setting a random token
                self.token = f"mock_token_{random.randint(1000, 9999)}"
                # Set the token expiration time randomly between 1 and 2 minutes
                random_expiration = time.time() + random.randint(60, 120)  # timestamp
                self.token_expiration = random_expiration
                logger.debug(
                    f"Mock token generated, expires at {datetime.fromtimestamp(random_expiration)}."
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
            logger.debug("Autenticando com HTTPSClient.")
            success = client.authenticate(username, password, client_id, client_secret)
            if not success:
                logger.error("Authentication failed in HTTPSClient.")
                return False

            logger.info("Authentication successful in HTTPSClient.")

            # Step 2: Match credentials
            logger.debug("Matching credentials.")
            matched_credentials = client.match_credentials(username_app, password_app)
            if not matched_credentials:
                logger.error("Failed to match credentials.")
                return False

            logger.info("Credentials matched successfully.")

            # Step 3: Try each credential until one works
            device_config = client.try_all_credentials_until_success(
                matched_credentials
            )
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

                logger.debug(
                    f"Token set to '{self.token}' with expiration at {datetime.fromtimestamp(self.token_expiration)}."
                )
                return True
            else:
                logger.error(
                    "Failed to receive device configuration with all credentials."
                )
                return False

    def is_token_expired(self):
        # Check if the token is expired
        logger.info(f"Token expiration timestamp: {self.token_expiration}")
        if not self.token_expiration:
            logger.warning("Token expiration not set. Considered expired.")
            return True
        is_expired = time.time() >= self.token_expiration
        if is_expired:
            logger.warning("Token has expired.")
            self.token = None
            self.token_expiration = None
            self._delete_token_file()  # Remove o arquivo se o token expirou
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
                    raise HTTPException(
                        status_code=401, detail="Authentication failed."
                    )

            # Otherwise, start a new authentication
            logger.debug("Starting new authentication process.")
            self.state = "Authenticating"
            try:
                await self.authenticate()
                logger.debug("Authentication process completed, returning token.")
                return self.token
            except HTTPException as e:
                logger.error("Error during authentication.")
                raise e

    async def is_authenticated(self):
        self.state = "Authenticated" if self.token and not self.is_token_expired() else "Unauthenticated"
        return self.state == "Authenticated"

    async def set_unauthenticated(self):
        self.state = "Unauthenticated"
        self.token = None
        self.token_expiration = None
        self._delete_token_file()  # Remove o arquivo ao definir como não autenticado
        logger.info("Estado definido como 'Unauthenticated' e token removido.")
        return self.state

    async def test_token_storage(self):
        """
        Testa se o armazenamento do token está funcionando corretamente no modo mock.
        """
        if not self.use_mock:
            logger.warning("Token storage test is only available in mock mode.")
            return

        logger.info("Starting token storage test in mock mode.")

        # Autenticar para gerar e salvar o token
        token_before = await self.authenticate()

        # Verificar se o arquivo de estado foi criado
        if not os.path.exists(self._state_file):
            logger.error("Token storage test failed: State file does not exist.")
            return

        try:
            with open(self._state_file, "r") as f:
                data = json.load(f)
                token_saved = data.get("token")
                expiration_saved = data.get("token_expiration")
        except Exception as e:
            logger.error(f"Error reading state file during storage test: {e}")
            return

        # Comparar o token e a expiração salvos com os atuais
        if token_before == token_saved and self.token_expiration == expiration_saved:
            logger.info("Token storage test passed: Token and expiration correctly saved.")
        else:
            logger.error("Token storage test failed: In-memory token and saved token do not match.")

        # Opcional: Recarregar o token a partir do arquivo para verificar a consistência
        original_token = self.token
        original_expiration = self.token_expiration

        # Simular recarregamento do token
        self._load_token_from_file()

        if self.token == original_token and self.token_expiration == original_expiration:
            logger.info("Token storage test passed: Loaded token matches the original token.")
        else:
            logger.error("Token storage test failed: Loaded token does not match the original token.")
