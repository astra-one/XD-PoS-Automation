import asyncio
from src.clients.token_manager import TokenManager

async def main():
    # Inicializar o TokenManager no modo mock
    token_manager = TokenManager(use_mock=True, url="http://localhost:8001")
    
    # Executar o teste de armazenamento do token
    await token_manager.test_token_storage()

if __name__ == "__main__":
    asyncio.run(main())
