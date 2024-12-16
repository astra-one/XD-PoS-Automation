import asyncio
import uuid
import random
import time
from typing import Dict, List, Optional
from fastapi import HTTPException
from faker import Faker
from ..models.entity_models import Product, Table
from .token_manager import TokenManager
import logging

# Configure logging
logger = logging.getLogger(__name__)
fake = Faker("pt_BR")


class RestaurantMockClient:
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.products = self._load_mock_products()
        self.tables = self._load_mock_tables()

    async def load_products(self):
        """Mock method to simulate loading products. Here it's already done in __init__."""
        # Since we're already loading products in __init__, we just pass
        pass

    def _load_mock_products(self) -> Dict[int, Product]:
        """Initialize a large set of mock products with realistic Portuguese names and unique IDs."""
        predefined_items = [
            {"id": 2001, "name": "Picanha na Chapa"},
            {"id": 2002, "name": "Costela de Cordeiro"},
            {"id": 2003, "name": "Fraldinha Grelhada"},
            {"id": 2004, "name": "Asinha de Frango"},
            {"id": 2005, "name": "Linguiça Artesanal"},
            {"id": 2006, "name": "Bife de Ancho"},
            {"id": 2007, "name": "Maminha Assada"},
            {"id": 2008, "name": "Espetinho Misto"},
            {"id": 2009, "name": "Churrasco de Picanha"},
            {"id": 2010, "name": "Tábua de Frios"},
            {"id": 2011, "name": "Salada Caesar com Frango"},
            {"id": 2012, "name": "Risoto de Cogumelos"},
            {"id": 2013, "name": "Moqueca de Peixe"},
            {"id": 2014, "name": "Feijoada Completa"},
            {"id": 2015, "name": "Bacalhau à Brás"},
            {"id": 2016, "name": "Camarão na Moranga"},
            {"id": 2017, "name": "Bobó de Camarão"},
            {"id": 2018, "name": "Pudim de Leite"},
            {"id": 2019, "name": "Brigadeiro Gourmet"},
            {"id": 2020, "name": "Quindim Tradicional"},
        ]

        return {
            item["id"]: Product(id=item["id"], name=item["name"])
            for item in predefined_items
        }

    def _load_mock_tables(self) -> List[Table]:
        """Initialize 100 mock tables with random statuses and attributes."""
        statuses = [1, 1, 2]  # 1: Occupied, 2: Reserved (varied distribution)
        mock_tables = []
        for i in range(1, 100):  # 100 tables
            table = Table(
                id=i,
                name=str(i),
                status=random.choice(statuses),
                lockDescription=None,
                inactive=False,
                freeTable=random.choice([True, False]),
                initialUser=random.randint(0, 20),
            )
            mock_tables.append(table)
        return mock_tables

    async def fetch_table_content(self, table_id: int) -> Dict:
        """
        Mock method to fetch table content with random orders.
        This simulates what fetch_table_content does in RestaurantClient.
        """
        # Simulate token validation
        await self.token_manager.get_token()
        if self.token_manager.is_token_expired():
            logger.warning("Token expired.")
            raise HTTPException(status_code=401, detail="Token expired")

        if not isinstance(table_id, int) or table_id < 1 or table_id > len(self.tables):
            raise HTTPException(status_code=404, detail="Mesa não encontrada.")
        table = self.tables[table_id - 1]
        table_status = table.status
        if table_status == 0:
            # Mesa está disponível, sem conteúdo
            return {
                "id": table_id,
                "status": table_status,
                "tableLocation": None,
                "content": [],
                "total": 0.0,
                "globalDiscount": 0.0,
            }

        num_orders = random.randint(1, 2)
        order_content = []
        total = 0.0
        for _ in range(num_orders):
            product = random.choice(list(self.products.values()))
            quantity = random.randint(1, 2)
            price = round(random.uniform(20.0, 100.0), 2)
            total_price = round(quantity * price, 2)
            order = {
                "itemId": product.id,
                "itemType": random.choice([0, 1, 2, 3]),
                "parentPosition": -1,
                "quantity": float(quantity),
                "price": price,
                "additionalInfo": fake.sentence(nb_words=6),
                "guid": str(uuid.uuid4()),
                "employee": random.randint(1, 50),
                "time": int(time.time() * 1000),
                "lineLevel": 0,
                "ratio": random.choice([0, 1]),
                "total": total_price,
                "lineDiscount": round(random.uniform(0.0, 10.0), 2),
                "completed": random.choice([True, False]),
                "parentGuid": "00000000-0000-0000-0000-000000000000",
                "itemName": product.name,
            }
            order_content.append(order)
            total += total_price

        mock_table_content = {
            "id": table_id,
            "status": table_status,
            "tableLocation": fake.address() if random.choice([True, False]) else None,
            "content": order_content,
            "total": round(total, 2),
            "globalDiscount": round(random.uniform(0.0, 20.0), 2),
        }
        await asyncio.sleep(
            random.uniform(0.05, 0.2)
        )  # Simulate asynchronous operation
        logger.debug(f"Table content fetched: {mock_table_content}")
        return mock_table_content

    async def fetch_tables(self) -> List[Table]:
        """
        Mock method to fetch a list of tables, simulating what fetch_tables does in RestaurantClient.
        """
        # Simulate token validation
        await self.token_manager.get_token()
        if self.token_manager.is_token_expired():
            logger.warning("Token expired.")
            raise HTTPException(status_code=401, detail="Token expired")

        await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
        logger.debug("Tables fetched.")
        return self.tables

    async def prebill(self, table_id: int) -> str:
        """
        Mock method to simulate the prebill action.
        Similar logic to RestaurantClient's prebill method:
        - Fetch table content
        - If no orders, 404
        - Otherwise, simulate posting the queue and return success.
        """
        # Simulate token validation
        await self.token_manager.get_token()
        if self.token_manager.is_token_expired():
            logger.warning("Token expired.")
            raise HTTPException(status_code=401, detail="Token expired")

        content = await self.fetch_table_content(table_id)
        orders = content.get("content", [])
        if not orders:
            raise HTTPException(status_code=404, detail="No orders found for the table.")

        # Simulate that the table moves to a 'reserved' state (like a prebill state)
        self.tables[table_id - 1].status = 2
        self.tables[table_id - 1].freeTable = False
        await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
        logger.info(f"Prebill posted for table {table_id}.")
        return "Pré-conta gerada com sucesso."

    async def close_table(self, table_id: int) -> str:
        """
        Mock method to simulate closing a table, as per the close_table method in RestaurantClient.
        """
        # Simulate token validation
        await self.token_manager.get_token()
        if self.token_manager.is_token_expired():
            logger.warning("Token expired.")
            raise HTTPException(status_code=401, detail="Token expired")

        if table_id < 1 or table_id > len(self.tables):
            raise HTTPException(status_code=404, detail="Mesa não encontrada.")

        # Simulate closing the table (making it available again)
        self.tables[table_id - 1].status = 0  # Available
        self.tables[table_id - 1].freeTable = True
        await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
        logger.info(f"Table {table_id} closed.")
        return "Mesa fechada com sucesso."
