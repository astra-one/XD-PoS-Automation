import configparser
from fastapi import FastAPI, Depends, HTTPException
from starlette.middleware.cors import CORSMiddleware
from src.clients.token_manager import TokenManager
from src.models.request_models import MessageRequest
from src.clients.restaurant_client import RestaurantClient
from src.clients.mock_restaurant_client import RestaurantMockClient
from src.order_processor.order_chain import OrderProcessorChain
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific domains in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


def read_config_file(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def get_token_manager():
    config = read_config_file("config.ini")["Settings"]
    APP_MODE = config.get("app_mode", "prod")  # Default to 'prod' if not specified
    use_mock = APP_MODE.lower() == "dev"
    coti_api_url = config.get("coti_cloud_services_url", "http://localhost:8005")
    token_manager = TokenManager(use_mock=use_mock, url=coti_api_url)
    return token_manager


# Dependency that will create and return the RestaurantClient or RestaurantMockClient instance
def get_restaurant_client(token_manager: TokenManager = Depends(get_token_manager)):
    if token_manager.use_mock:
        logger.info("Running in development mode. Using RestaurantMockClient.")
        return RestaurantMockClient(token_manager=token_manager)
    else:
        logger.info("Running in production mode. Using RestaurantClient.")
        return RestaurantClient(token_manager=token_manager)


# Dependency that will create and return the OrderProcessorChain instance
def get_order_processor_chain() -> OrderProcessorChain:
    return OrderProcessorChain()


def handle_request_exception(e: Exception):
    if hasattr(e, "status_code") and e.status_code == 401:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401, detail="Smart Connect Authentication Error"
        )
    else:
        logger.error(f"Unhandled exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@app.get("/is_authenticated/")
async def is_authenticated(token_manager: TokenManager = Depends(get_token_manager)):
    return {"is_authenticated": await token_manager.is_authenticated()}


@app.post("/message/")
async def create_board_message(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
    order_processor: OrderProcessorChain = Depends(get_order_processor_chain),
):
    """
    Endpoint to create a board message by fetching table content,
    formatting the order, and processing it.
    """
    table_id = request.table_id
    try:
        # Validate table_id is an integer
        if not isinstance(table_id, int):
            raise HTTPException(status_code=400, detail="table_id must be an integer.")

        # Fetch the table order from the RestaurantClient
        table_order = await client.fetch_table_content(table_id)

        if not table_order["content"]:
            raise HTTPException(status_code=404, detail="Table content not found.")

        # Create the file name based on the table_id
        file_name = f"comanda_{table_id}.txt"
        file_path = os.path.join(os.getcwd(), file_name)

        # Format the order
        formatted_order = ""
        for item in table_order.get("content", []):
            product_name = item.get("itemName", "Not found")
            quantity = item.get("quantity", 1)
            price = item.get("price", 0.0)
            total = item.get("total", 0.0)
            # Format the line
            line = f"{product_name} - {quantity} X R$ {price:.2f} = R$ {total:.2f}\n"
            formatted_order += line

        # Process the formatted order
        order = await order_processor.main(formatted_order, file_path)
        return order

    except Exception as e:
        handle_request_exception(e)


@app.post("load/products/")
async def load_products(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
):
    """
    Endpoint to load products from a file.
    """
    try:
        # Load products from file
        response = await client.load_products()
        return response

    except Exception as e:
        handle_request_exception(e)


@app.post("/order/")
async def get_order_by_id(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
):
    """
    Endpoint to retrieve the order details for a specific table.
    """
    table_id = request.table_id
    try:
        # Fetch the table order from the RestaurantClient
        table_order = await client.fetch_table_content(table_id)
        return table_order

    except Exception as e:
        handle_request_exception(e)


@app.get("/tables/")
async def get_tables(
    client: RestaurantClient = Depends(get_restaurant_client),
):
    """
    Endpoint to retrieve a list of all tables.
    """
    try:
        # Fetch the list of tables from the RestaurantClient
        tables = await client.fetch_tables()
        return tables

    except Exception as e:
        handle_request_exception(e)


@app.post("/payment/")
async def set_payment_status(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
):
    """
    Endpoint to set the payment status for a specific table.

    Args:
        request (MessageRequest): The request body containing the table_id.
        client (RestaurantClient): The RestaurantClient instance.

    Returns:
        dict: A success message with the server response.
    """
    table_id = request.table_id
    try:
        # Send a POSTQUEUE message to set the payment status
        response = await client.prebill(table_id)
        return {"status": "Payment status set successfully", "response": response}

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain consistent error responses
        logger.error(
            f"HTTP error setting payment status for table {table_id}: {http_exc.detail}"
        )
        raise http_exc
    except Exception as e:
        handle_request_exception(e)


@app.post("/close/")
async def close_table_endpoint(
    request: MessageRequest,
    client: RestaurantClient = Depends(get_restaurant_client),
):
    """
    Endpoint to close a specific table after payment.

    Args:
        request (MessageRequest): The request body containing the table_id.
        client (RestaurantClient): The RestaurantClient instance.

    Returns:
        dict: A success message with the server response.
    """
    table_id = request.table_id
    try:
        # Send a POSTQUEUE message to close the table
        response = await client.close_table(table_id)
        return {"status": "Table closed successfully", "response": response}

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions to maintain consistent error responses
        logger.error(f"HTTP error closing table {table_id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        handle_request_exception(e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
