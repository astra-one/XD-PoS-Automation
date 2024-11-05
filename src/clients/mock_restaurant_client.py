import asyncio
import uuid
import random
from typing import Dict, List, Optional
from fastapi import HTTPException
from faker import Faker
from ..models.entity_models import Product, Table

fake = Faker("pt_BR")


class RestaurantMockClient:
    _instance: Optional["RestaurantMockClient"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RestaurantMockClient, cls).__new__(cls)
            cls._instance.products = cls._instance._load_mock_products()
            cls._instance.tables = cls._instance._load_mock_tables()
        return cls._instance

    def __init__(self):
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
        """Initialize 500 mock tables with random statuses and attributes."""
        statuses = [1, 1, 2]  # 0: Available, 1: Occupied, 2: Reserved
        mock_tables = []
        for i in range(1, 100):  # 500 tables
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

        Args:
            table_id (int): The ID of the table.

        Returns:
            Dict: Mocked table content.
        """
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

        num_orders = random.randint(1, 10)
        order_content = []
        total = 0.0
        for _ in range(num_orders):
            product = random.choice(list(self.products.values()))
            quantity = random.randint(1, 5)
            price = round(random.uniform(20.0, 100.0), 2)
            total_price = round(quantity * price, 2)
            order = {
                "itemId": product.id,  # Changed from str(product.id) to int
                "itemType": random.choice([0, 1, 2, 3]),
                "parentPosition": -1,
                "quantity": float(quantity),
                "price": price,
                "additionalInfo": fake.sentence(nb_words=6),
                "guid": str(uuid.uuid4()),
                "employee": random.randint(1, 50),
                "time": int(asyncio.get_event_loop().time() * 1000),
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

        print("Salve")

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
        print("Table content fetched:", mock_table_content)
        return mock_table_content

    async def fetch_tables(self) -> List[Table]:
        """
        Mock method to fetch a list of tables.

        Returns:
            List[Table]: A list of mocked Table objects.
        """
        await asyncio.sleep(
            random.uniform(0.05, 0.2)
        )  # Simulate asynchronous operation
        return self.tables

    async def post_queue(self, table_id: int) -> str:
        """
        Mock method to simulate posting to the queue.

        Args:
            table_id (int): The ID of the table.

        Returns:
            str: Success message.
        """
        if table_id < 1 or table_id > len(self.tables):
            raise HTTPException(status_code=404, detail="Mesa não encontrada.")

        # Simulate updating table status to Reserved
        self.tables[table_id - 1].status = 2  # Reserved
        self.tables[table_id - 1].freeTable = False
        await asyncio.sleep(
            random.uniform(0.05, 0.2)
        )  # Simulate asynchronous operation
        return "Fila postada com sucesso."

    async def close_table(self, table_id: int) -> str:
        """
        Mock method to simulate closing a table.

        Args:
            table_id (int): The ID of the table.

        Returns:
            str: Success message.
        """
        if table_id < 1 or table_id > len(self.tables):
            raise HTTPException(status_code=404, detail="Mesa não encontrada.")

        # Simulate closing the table
        self.tables[table_id - 1].status = 0  # Available
        self.tables[table_id - 1].freeTable = True
        await asyncio.sleep(
            random.uniform(0.05, 0.2)
        )  # Simulate asynchronous operation
        return "Mesa fechada com sucesso."
