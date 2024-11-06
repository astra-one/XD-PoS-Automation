
from fastapi import HTTPException

class AuthenticationError(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Smart Connect Authentication Error")
