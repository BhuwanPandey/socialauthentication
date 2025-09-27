# Creating our own callback route....

import jwt
import os
import httpx
from httpx_oauth.exceptions import GetProfileError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_users import models
from fastapi_users.authentication import Strategy
from fastapi_users.exceptions import UserAlreadyExists
from fastapi_users.jwt import decode_jwt
from fastapi_users.manager import BaseUserManager
from fastapi_users.router.common import ErrorCode, ErrorModel
from httpx_oauth.integrations.fastapi import OAuth2AuthorizeCallback
from httpx_oauth.oauth2 import OAuth2Token

from fastapi_auth.models import SECRET, auth_backend, get_user_manager, google_oauth_client

STATE_TOKEN_AUDIENCE = "fastapi-users:oauth-state"
PROFILE_ENDPOINT = "https://people.googleapis.com/v1/people/me"

router = APIRouter()
oauth2_authorize_callback = OAuth2AuthorizeCallback(
    google_oauth_client,
    redirect_url=os.getenv("GOOGLE_REDIRECT_URL",""),
)


async def get_id_email_name_photo(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            PROFILE_ENDPOINT,
            params={"personFields": "emailAddresses,names,photos,urls"},
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code >= 400:
            raise GetProfileError(response=response)
        data = response.json()

        user_id = data["resourceName"]
        user_email = next(
            email["value"]
            for email in data["emailAddresses"]
            if email["metadata"]["primary"]
        )
        user_name = next(
            name["displayName"] for name in data["names"] if name["metadata"]["primary"]
        )
        username = user_name.replace(" ", "")
        username = username.lower()
        user_photo = next(
            photo["url"] for photo in data["photos"] if photo["metadata"]["primary"]
        )

        return user_id, user_email, username, user_photo


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
    ) = await get_id_email_name_photo(token["access_token"])
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
            google_oauth_client.name,
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