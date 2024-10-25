from pydantic import BaseModel    

# Define your BoardRequest model
class BoardRequest(BaseModel):
    board_id: str

# Define your AuthenticationRequest model
class AuthenticationRequest(BaseModel):
    username: str
    password: str
    client_id: str
    client_secret: str = ""  # Default to an empty string like in your Java code

class MessageRequest(BaseModel):
    table_id: int