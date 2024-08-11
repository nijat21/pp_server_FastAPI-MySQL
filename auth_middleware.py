from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from auth import get_current_user
from typing import Annotated

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            # user_dependency = Annotated[dict, Depends(get_current_user)]
            request.state.user = await get_current_user(request)

            response = await call_next(request)
            return response
        except HTTPException as e:
            # Handle cases where token validation fails
            raise HTTPException(status_code=e.status_code, detail=e.detail)
