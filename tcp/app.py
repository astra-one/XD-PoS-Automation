from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tcp_client import TCPClient
from message_builder import MessageBuilder
import asyncio

app = FastAPI()


# Define your BoardRequest model
class BoardRequest(BaseModel):
    board_id: str


# Define your AuthenticationRequest model
class AuthenticationRequest(BaseModel):
    username: str
    password: str
    client_id: str
    client_secret: str = ""  # Default to an empty string like in your Java code


message_builder = MessageBuilder(
    user_id="1",
    app_version="1.0",
    protocol_version="1",
    token="6a141f83b2e658377a1d585cf21a7141c115d673",
)


@app.post("/get-board-content/")
async def get_board_content(request: BoardRequest):
    client = TCPClient()
    client.connect()

    # Access board_id from the request model
    message = message_builder.build_get_board_content(request.board_id)

    # Run send_data in a thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, client.send_data, message)

    # Check for None response
    if response is None:
        raise HTTPException(
            status_code=500, detail="Failed to receive response from the TCP server"
        )

    return {
        "status": "Message sent to the server",
        "message": message,
        "response": response,
    }


@app.post("/authenticate/")
async def authenticate(request: AuthenticationRequest):
    client = TCPClient()

    # Run authenticate in a thread to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        client.authenticate,
        request.username,
        request.password,
        request.client_id,
    )

    # # Check for None response or authentication failure
    # if response is None or "access_token" not in response:
    #     raise HTTPException(status_code=500, detail="Authentication failed")

    return {"status": "Authenticated", "response": response}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
