import os
from fastapi import FastAPI, Depends, HTTPException
from src.models.request_models import MessageRequest
from src.clients.restaurant_client import RestaurantClient
from src.order_processor.order_chain import OrderProcessorChain
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


# Dependency that will create and return the RestaurantClient instance
def get_restaurant_client() -> RestaurantClient:
    return RestaurantClient()


def get_order_processor_chain() -> OrderProcessorChain:
    return OrderProcessorChain()


@app.post("/message/")
async def create_board_message(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
    order_processor: OrderProcessorChain = Depends(get_order_processor_chain),
):
    table_id = request.table_id
    try:
        # Access the table order from the RestaurantClient
        table_order = await client.fetch_table_content(table_id)

        # print("Table Order:", table_order)

        # Create the file name based on the table_id
        file_name = f"comanda_{table_id}.txt"
        file_path = os.path.join(os.getcwd(), file_name)

        formated_order = ""
        for index, item in enumerate(table_order.get("content", [])):
            product_name = item.get("itemName", "Não encontrado")
            quantity = item.get("quantity", 1)
            price = item.get("price", 0.0)
            total = item.get("total", 0.0)
            # Format the line
            line = (
                f"{product_name} - {quantity} X R$ {price:.2f} = R$ {total:.2f}\n"
            )
            formated_order += line

        return await order_processor.main(formated_order, file_path)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message.")
    
@app.post("/order/")
async def get_order_by_id(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
):
    table_id = request.table_id
    try:
        # Access the table order from the RestaurantClient
        table_order = await client.fetch_table_content(table_id)

        return table_order

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message.")
    
@app.get("/tables/")
async def get_tables(
    client: RestaurantClient = Depends(get_restaurant_client),
):
    try:
        # Access the table order from the RestaurantClient
        tables = await client.fetch_tables()

        return tables

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
