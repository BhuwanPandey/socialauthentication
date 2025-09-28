import jwt
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import models
from fastapi_users.authentication import Strategy
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.jwt import decode_jwt
from fastapi_users.manager import BaseUserManager
from fastapi_users.router.common import ErrorCode, ErrorModel
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import OAuth2Token

from fastapi_auth.models import SECRET, auth_backend, get_user_manager, github_oauth_client

STATE_TOKEN_AUDIENCE = "fastapi-users:oauth-state"
router = APIRouter()
oauth2_authorize_callback = OAuth2AuthorizeCallback(
    github_oauth_client,
    redirect_url=os.getenv("GITHUB_OAUTH_REDIRECT_URI",""),
)


@router.get(
    "/callback",
    name="callback_route_name",
    description="The response varies based on the authentication backend used.",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        "INVALID_STATE_TOKEN": {
                            "summary": "Invalid state token.",
                            "value": None,
                        },
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary": "User is inactive.",
                            "value": {"detail": ErrorCode.LOGIN_BAD_CREDENTIALS},
                        },
                    }
                }
            },
        },
    },
)
async def callback(
    request: Request,
    access_token_state: tuple[OAuth2Token, str] = Depends(oauth2_authorize_callback),
    user_manager: BaseUserManager[models.UP, models.ID] = Depends(get_user_manager),
    strategy: Strategy[models.UP, models.ID] = Depends(auth_backend.get_strategy),
):
    token, state = access_token_state
    (
        account_id,
        account_email,
        account_name,
        account_photo,
    ) = await github_oauth_client.get_id_email_name_photo(token["access_token"])

    if account_email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.OAUTH_NOT_AVAILABLE_EMAIL,
        )

    try:
        decode_jwt(state, SECRET, [STATE_TOKEN_AUDIENCE])
    except jwt.DecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        user = await user_manager.oauth_callback(
            github_oauth_client.name,
            token["access_token"],
            account_id,
            account_email,
            account_name,
            account_photo,
            token.get("expires_at"),
            token.get("refresh_token"),
            request,
            associate_by_email=False,
            is_verified_by_default=False,
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.OAUTH_USER_ALREADY_EXISTS,
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    response = await auth_backend.login(strategy, user)
    await user_manager.on_after_login(user, request, response)
    return response
