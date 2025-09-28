from fastapi import APIRouter,Depends
import os
from fastapi_auth.models import User
from fastapi_auth.schema import UserCreate, UserRead, UserUpdate
from fastapi_auth.models import (
    SECRET,
    auth_backend,
    current_active_user,
    fastapi_users,
    github_oauth_client,
)
from .github import router



user_router = APIRouter()

user_router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
user_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
user_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
user_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
user_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)


github_route = fastapi_users.get_oauth_router(
    github_oauth_client, 
    auth_backend, SECRET,
    redirect_url=os.getenv("GITHUB_OAUTH_REDIRECT_URI","")
    )

github_route.routes = [
    route for route in github_route.routes 
    if not route.name.endswith(".callback")
]

user_router.include_router(
    github_route,
    prefix="/auth/github",
    tags=["auth"],
)

# callback endpoint
user_router.include_router(
    router,
    prefix="/auth/github",
    tags=["auth"],
)


@user_router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
