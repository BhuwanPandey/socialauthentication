import os
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, models
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.github import GitHubOAuth2
from dotenv import load_dotenv
from fastapi.security import HTTPBearer
from fastapi_users import exceptions
from httpx_oauth.exceptions import GetProfileError,GetIdEmailError

from .db import User, get_user_db
load_dotenv()


SECRET = "SECRET"

github_oauth_client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
github_oauth_client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")


class CustomGitHubOAuth2(GitHubOAuth2):
    async def get_id_email_name_photo(self, token: str) -> tuple[str, Optional[str]]:
        try:
            profile = await self.get_profile(token)
        except GetProfileError as e:
            raise GetIdEmailError(response=e.response) from e

        id = profile["id"]
        email = profile.get("email")
        name = profile.get("login","")
        photo = profile.get("avatar_url","")


        # No public email, make a separate call to /user/emails
        if email is None:
            try:
                emails = await self.get_emails(token)
            except GetProfileError as e:
                raise GetIdEmailError(response=e.response) from e

            # Use the primary email if it exists, otherwise the first
            email = next(
                (e["email"] for e in emails if e.get("primary")), emails[0]["email"]
            )
        return str(id), email,name,photo


github_oauth_client = CustomGitHubOAuth2(
    github_oauth_client_id,
    github_oauth_client_secret
)


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def oauth_callback(
        self: "BaseUserManager[models.UOAP, models.ID]",
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        username:str,
        photo:str,
        expires_at: Optional[int] = None,
        refresh_token: Optional[str] = None,
        request: Optional[Request] = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> models.UOAP:
        oauth_account_dict = {
            "oauth_name": oauth_name,
            "access_token": access_token,
            "account_id": account_id,
            "account_email": account_email,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
        }
        try:
            user = await self.get_by_oauth_account(oauth_name, account_id)
        except exceptions.UserNotExists:
            try:
                # Associate account
                user = await self.get_by_email(account_email)

                if not associate_by_email:
                    raise exceptions.UserAlreadyExists()

                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
            except exceptions.UserNotExists:
                # Create account
                password = self.password_helper.generate()
                user_dict = {
                    "email": account_email,
                    "hashed_password": self.password_helper.hash(password),
                    "is_verified": is_verified_by_default,
                    "username": username,
                    "avatar": photo
                }
                user = await self.user_db.create(user_dict)
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
                await self.on_after_register(user, request)
        else:
            # Update oauth
            for existing_oauth_account in user.oauth_accounts:
                if (
                    existing_oauth_account.account_id == account_id
                    and existing_oauth_account.oauth_name == oauth_name
                ):
                    user = await self.user_db.update_oauth_account(
                        user, existing_oauth_account, oauth_account_dict
                    )
        return user
    
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


class HTTPBearerTokenOnly(HTTPBearer):
    async def __call__(self, request: Request):
        credentials = await super().__call__(request)
        if credentials:
            return credentials.credentials
        return None


class SimpleBearerTransport(BearerTransport):
    def __init__(self):
        self.scheme = HTTPBearerTokenOnly()

bearer_transport = SimpleBearerTransport()


def get_jwt_strategy() -> JWTStrategy[models.UP, models.ID]:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
