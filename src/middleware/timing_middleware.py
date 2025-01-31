import time
import json
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
        except Exception as e:
            # Optionally handle exceptions here
            raise e
        
        process_time = time.time() - start_time
        
        # Check if the response is JSON
        if response.headers.get("Content-Type", "").startswith("application/json"):
            # Read the original response body
            body = [section async for section in response.body_iterator]
            body_str = b"".join(body).decode()
            data = json.loads(body_str) if body_str else {}
            
            # Add the processing time
            data["response_time"] = process_time
            
            # Create a new JSON response with the updated data
            new_response = JSONResponse(content=data, status_code=response.status_code)
            
            return new_response
        else:
            # For non-JSON responses, you can add a header instead
            response.headers["X-Process-Time"] = str(process_time)
            return response
