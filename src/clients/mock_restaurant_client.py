import asyncio
import uuid
import random
import time
import logging
from typing import Dict, List, Optional
from fastapi import HTTPException
from faker import Faker
from ..models.entity_models import Product, Table
from .token_manager import TokenManager

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels of logs

# Create handler (console in this case, but can be file or other handlers)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the logger if it doesn't have handlers already
if not logger.handlers:
    logger.addHandler(handler)

fake = Faker("pt_BR")


class RestaurantMockClient:
    def __init__(self, token_manager: TokenManager):
        """
        Initialize the RestaurantMockClient with a TokenManager.
        Loads mock products and tables.
        """
        logger.info("Initializing RestaurantMockClient.")
        self.token_manager = token_manager
        try:
            self.products = self._load_mock_products()
            logger.info(f"Loaded {len(self.products)} mock products.")
        except Exception as e:
            logger.exception("Failed to load mock products.")
            raise

        try:
            self.tables = self._load_mock_tables()
            logger.info(f"Initialized {len(self.tables)} mock tables.")
        except Exception as e:
            logger.exception("Failed to load mock tables.")
            raise

    async def load_products(self):
        """
        Mock method to simulate loading products.
        Here it's already done in __init__, so it just logs the action.
        """
        logger.debug("Called load_products, but products are already loaded in __init__.")

    def _load_mock_products(self) -> Dict[int, Product]:
        """
        Initialize a set of mock products with realistic Portuguese names and unique IDs.
        Foram adicionados produtos de buffet para testar a lógica de não cobrança de taxa.
        """
        logger.debug("Loading mock products.")
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
            # Produtos de buffet para testar a lógica de não cobrança de taxa de serviço
            {"id": 2021, "name": "BUFFET KG"},
            {"id": 2022, "name": "BUFFET AVONTADE"}
        ]

        products = {
            item["id"]: Product(id=item["id"], name=item["name"])
            for item in predefined_items
        }
        logger.debug(f"Mock products loaded: {products}")
        return products

    def _load_mock_tables(self) -> List[Table]:
        """
        Initialize 100 mock tables with random statuses and attributes.
        """
        logger.debug("Loading mock tables.")
        statuses = [1, 1, 2]  # 1: Occupied, 2: Reserved (varied distribution)
        mock_tables = []
        for i in range(1, 300):  # 99 tables (IDs 1 to 99)
            table = Table(
                id=i,
                name=str(i),
                status=random.choice(statuses),
                lockDescription=None,
                inactive=False,
                freeTable=random.choice([True, True]),
                initialUser=random.randint(0, 20),
            )
            mock_tables.append(table)
            logger.debug(f"Loaded mock table: {table}")
        logger.debug("All mock tables loaded successfully.")
        return mock_tables

    async def fetch_table_content(self, table_id: int) -> Dict:
        """
        Mock method to fetch table content with orders.
        Gera um número realista de pratos para cada mesa, com valores variados.
        """
        logger.info(f"Fetching content for table ID: {table_id}")
        try:
            # Simulate token validation
            await self.token_manager.get_token()
            if self.token_manager.is_token_expired():
                logger.warning("Token expired while fetching table content.")
                raise HTTPException(status_code=401, detail="Token expired")

            if (
                not isinstance(table_id, int)
                or table_id < 1
                or table_id > len(self.tables)
            ):
                logger.error(f"Invalid table ID: {table_id}. Mesa não encontrada.")
                raise HTTPException(status_code=404, detail="Mesa não encontrada.")

            table = self.tables[table_id - 1]
            table_status = table.status
            logger.debug(f"Table ID {table_id} status: {table_status}")

            if table_status == 0:
                # Table is available, no content
                logger.info(f"Table ID {table_id} is available. No content to fetch.")
                return {
                    "id": table_id,
                    "status": table_status,
                    "tableLocation": None,
                    "content": [],
                    "total": 0.0,
                    "globalDiscount": 0.0,
                    "serviceFee": 0.0,
                }

            # Gerar um número mais realista de pratos (entre 2 e 6 para uma mesa típica)
            num_orders = random.randint(2, 6)
            logger.debug(f"Generating {num_orders} mock orders for table ID {table_id}.")
            order_content = []
            total_value = 0.0
            
            # Categorias de produtos para criar pedidos mais realistas
            categories = {
                "entradas": [2004, 2005, 2008, 2010],  # IDs de produtos que são entradas
                "pratos_principais": [2001, 2002, 2003, 2006, 2007, 2009, 2012, 2013, 2014, 2015, 2016, 2017],  # Pratos principais
                "sobremesas": [2018, 2019, 2020],  # Sobremesas
                "buffet": [2021, 2022]  # Opções de buffet
            }
            
            # Decidir se a mesa é de buffet ou à la carte
            is_buffet_table = random.random() < 0.2  # 20% de chance de ser mesa de buffet
            
            if is_buffet_table:
                # Mesa de buffet - apenas itens de buffet
                buffet_product_id = random.choice(categories["buffet"])
                buffet_product = self.products[buffet_product_id]
                quantity = round(random.uniform(0.8, 2.5), 2) if buffet_product_id == 2021 else random.randint(1, 3)
                price = 69.90 if buffet_product_id == 2021 else 89.90  # Preço por kg ou à vontade
                item_total = price * quantity
                total_value += item_total
                
                order = {
                    "itemId": buffet_product.id,
                    "itemType": 1,  # Tipo comida
                    "parentPosition": -1,
                    "quantity": quantity,
                    "price": price,
                    "additionalInfo": "",
                    "guid": str(uuid.uuid4()),
                    "employee": random.randint(1, 50),
                    "time": int(time.time() * 1000),
                    "lineLevel": 0,
                    "ratio": 1,
                    "total": round(item_total, 2),
                    "lineDiscount": 0.0,
                    "completed": True,
                    "parentGuid": "00000000-0000-0000-0000-000000000000",
                    "itemName": buffet_product.name,
                }
                order_content.append(order)
                
                # Adicionar bebidas para mesas de buffet (opcional)
                if random.random() < 0.8:  # 80% de chance de pedir bebidas
                    num_drinks = random.randint(1, 3)
                    for _ in range(num_drinks):
                        drink_price = round(random.uniform(5.0, 15.0), 2)
                        drink_quantity = random.randint(1, 2)
                        drink_total = drink_price * drink_quantity
                        total_value += drink_total
                        
                        drink_order = {
                            "itemId": 3000 + random.randint(1, 20),  # IDs fictícios para bebidas
                            "itemType": 2,  # Tipo bebida
                            "parentPosition": -1,
                            "quantity": drink_quantity,
                            "price": drink_price,
                            "additionalInfo": "",
                            "guid": str(uuid.uuid4()),
                            "employee": random.randint(1, 50),
                            "time": int(time.time() * 1000),
                            "lineLevel": 0,
                            "ratio": 1,
                            "total": round(drink_total, 2),
                            "lineDiscount": 0.0,
                            "completed": True,
                            "parentGuid": "00000000-0000-0000-0000-000000000000",
                            "itemName": random.choice(["Água Mineral", "Refrigerante", "Suco Natural", "Cerveja"]),
                        }
                        order_content.append(drink_order)
            else:
                # Mesa à la carte - distribuir pedidos entre categorias
                # Sempre incluir pelo menos um prato principal
                main_dish_count = random.randint(1, 3)
                appetizer_count = random.randint(0, 2)
                dessert_count = random.randint(0, 2)
                drink_count = random.randint(1, 4)
                
                # Adicionar entradas
                for _ in range(appetizer_count):
                    product_id = random.choice(categories["entradas"])
                    product = self.products[product_id]
                    price = round(random.uniform(25.0, 45.0), 2)
                    quantity = random.randint(1, 2)
                    item_total = price * quantity
                    total_value += item_total
                    
                    order = {
                        "itemId": product.id,
                        "itemType": 1,  # Tipo comida
                        "parentPosition": -1,
                        "quantity": quantity,
                        "price": price,
                        "additionalInfo": fake.sentence(nb_words=6) if random.random() < 0.3 else "",
                        "guid": str(uuid.uuid4()),
                        "employee": random.randint(1, 50),
                        "time": int(time.time() * 1000) - random.randint(900000, 1800000),  # Pedido mais antigo
                        "lineLevel": 0,
                        "ratio": 1,
                        "total": round(item_total, 2),
                        "lineDiscount": 0.0,
                        "completed": True,
                        "parentGuid": "00000000-0000-0000-0000-000000000000",
                        "itemName": product.name,
                    }
                    order_content.append(order)
                
                # Adicionar pratos principais
                for _ in range(main_dish_count):
                    product_id = random.choice(categories["pratos_principais"])
                    product = self.products[product_id]
                    price = round(random.uniform(45.0, 120.0), 2)
                    quantity = 1  # Geralmente uma pessoa pede um prato principal
                    item_total = price * quantity
                    total_value += item_total
                    
                    order = {
                        "itemId": product.id,
                        "itemType": 1,  # Tipo comida
                        "parentPosition": -1,
                        "quantity": quantity,
                        "price": price,
                        "additionalInfo": fake.sentence(nb_words=6) if random.random() < 0.4 else "",
                        "guid": str(uuid.uuid4()),
                        "employee": random.randint(1, 50),
                        "time": int(time.time() * 1000) - random.randint(300000, 900000),  # Pedido intermediário
                        "lineLevel": 0,
                        "ratio": 1,
                        "total": round(item_total, 2),
                        "lineDiscount": 0.0,
                        "completed": random.random() < 0.9,  # 90% de chance de estar completo
                        "parentGuid": "00000000-0000-0000-0000-000000000000",
                        "itemName": product.name,
                    }
                    order_content.append(order)
                
                # Adicionar sobremesas
                for _ in range(dessert_count):
                    product_id = random.choice(categories["sobremesas"])
                    product = self.products[product_id]
                    price = round(random.uniform(15.0, 30.0), 2)
                    quantity = random.randint(1, 2)
                    item_total = price * quantity
                    total_value += item_total
                    
                    order = {
                        "itemId": product.id,
                        "itemType": 1,  # Tipo comida
                        "parentPosition": -1,
                        "quantity": quantity,
                        "price": price,
                        "additionalInfo": "",
                        "guid": str(uuid.uuid4()),
                        "employee": random.randint(1, 50),
                        "time": int(time.time() * 1000) - random.randint(0, 300000),  # Pedido mais recente
                        "lineLevel": 0,
                        "ratio": 1,
                        "total": round(item_total, 2),
                        "lineDiscount": 0.0,
                        "completed": random.random() < 0.7,  # 70% de chance de estar completo
                        "parentGuid": "00000000-0000-0000-0000-000000000000",
                        "itemName": product.name,
                    }
                    order_content.append(order)
                
                # Adicionar bebidas
                for _ in range(drink_count):
                    drink_price = round(random.uniform(5.0, 25.0), 2)
                    drink_quantity = random.randint(1, 2)
                    drink_total = drink_price * drink_quantity
                    total_value += drink_total
                    
                    drink_names = ["Água Mineral", "Refrigerante", "Suco Natural", "Cerveja", 
                                  "Caipirinha", "Vinho (Taça)", "Café Expresso", "Chá Gelado"]
                    
                    drink_order = {
                        "itemId": 3000 + random.randint(1, 20),  # IDs fictícios para bebidas
                        "itemType": 2,  # Tipo bebida
                        "parentPosition": -1,
                        "quantity": drink_quantity,
                        "price": drink_price,
                        "additionalInfo": "",
                        "guid": str(uuid.uuid4()),
                        "employee": random.randint(1, 50),
                        "time": int(time.time() * 1000) - random.randint(0, 1800000),  # Tempo variado
                        "lineLevel": 0,
                        "ratio": 1,
                        "total": round(drink_total, 2),
                        "lineDiscount": 0.0,
                        "completed": True,
                        "parentGuid": "00000000-0000-0000-0000-000000000000",
                        "itemName": random.choice(drink_names),
                    }
                    order_content.append(drink_order)

            # Verifica se todos os itens do pedido são de buffet (nome contendo 'buffet', ignorando caixa)
            is_buffet_only = (
                all("buffet" in order["itemName"].lower() for order in order_content)
                if order_content
                else False
            )
            
            # Se o pedido for somente buffet, não aplica taxa de serviço; caso contrário, 10% do total
            service_fee = 0.0 if is_buffet_only else round(total_value * 0.1, 2)
            logger.debug(f"Buffet only: {is_buffet_only}. Calculated service fee: {service_fee}")

            global_discount = 0.0

            # Calcular total final
            final_total = total_value - global_discount + service_fee

            mock_table_content = {
                "id": table_id,
                "status": table_status,
                "tableLocation": fake.address() if random.choice([True, False]) else None,
                "content": order_content,
                "total": round(final_total, 2),
                "globalDiscount": round(global_discount, 2),
                "serviceFee": round(service_fee, 2),
            }
            await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
            logger.debug(f"Fetched table content: {mock_table_content}")
            return mock_table_content
        except HTTPException as http_exc:
            logger.error(f"HTTPException in fetch_table_content: {http_exc.detail}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in fetch_table_content: {e}")
            raise HTTPException(status_code=500, detail="Erro interno do servidor.")

    async def fetch_tables(self) -> List[Table]:
        """
        Mock method to fetch a list of tables, simulating what fetch_tables does in RestaurantClient.
        """
        logger.info("Fetching list of tables.")
        try:
            # Simulate token validation
            await self.token_manager.get_token()
            if self.token_manager.is_token_expired():
                logger.warning("Token expired while fetching tables.")
                raise HTTPException(status_code=401, detail="Token expired")

            await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
            logger.debug(f"Fetched {len(self.tables)} mock tables.")
            return self.tables
        except HTTPException as http_exc:
            logger.error(f"HTTPException in fetch_tables: {http_exc.detail}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in fetch_tables: {e}")
            raise HTTPException(status_code=500, detail="Erro interno do servidor.")

    async def prebill(self, table_id: int) -> str:
        """
        Mock method to simulate the prebill action.
        Similar logic to RestaurantClient's prebill method:
        - Fetch table content
        - If no orders, 404
        - Otherwise, simulate posting the queue and return success.
        """
        logger.info(f"Initiating prebill for table ID: {table_id}")
        try:
            # Simulate token validation
            await self.token_manager.get_token()
            if self.token_manager.is_token_expired():
                logger.warning("Token expired while initiating prebill.")
                raise HTTPException(status_code=401, detail="Token expired")

            content = await self.fetch_table_content(table_id)
            orders = content.get("content", [])
            if not orders:
                logger.warning(f"No orders found for table ID: {table_id}. Cannot generate prebill.")
                raise HTTPException(status_code=404, detail="No orders found for the table.")

            # Simulate that the table moves to a 'reserved' state (like a prebill state)
            self.tables[table_id - 1].status = 2
            self.tables[table_id - 1].freeTable = False
            await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
            logger.info(f"Prebill posted successfully for table ID: {table_id}.")
            return "Pré-conta gerada com sucesso."
        except HTTPException as http_exc:
            logger.error(f"HTTPException in prebill: {http_exc.detail}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in prebill: {e}")
            raise HTTPException(status_code=500, detail="Erro interno do servidor.")

    async def close_table(self, table_id: int, payment_type: str) -> str:
        """
        Mock method to simulate closing a table, as per the close_table method in RestaurantClient.
        """
        logger.info(f"Closing table ID: {table_id}")
        try:
            # Simulate token validation
            await self.token_manager.get_token()
            if self.token_manager.is_token_expired():
                logger.warning("Token expired while closing table.")
                raise HTTPException(status_code=401, detail="Token expired")

            if table_id < 1 or table_id > len(self.tables):
                logger.error(f"Invalid table ID: {table_id}. Mesa não encontrada.")
                raise HTTPException(status_code=404, detail="Mesa não encontrada.")

            # Simulate closing the table (making it available again)
            self.tables[table_id - 1].status = 0  # Available
            self.tables[table_id - 1].freeTable = True
            await asyncio.sleep(random.uniform(0.05, 0.2))  # Simulate asynchronous operation
            logger.info(f"Table ID {table_id} closed successfully.")
            return "Mesa fechada com sucesso."
        except HTTPException as http_exc:
            logger.error(f"HTTPException in close_table: {http_exc.detail}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in close_table: {e}")
            raise HTTPException(status_code=500, detail="Erro interno do servidor.")