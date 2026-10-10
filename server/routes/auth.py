"""Authentication routes: register and login."""
from fastapi import APIRouter, HTTPException, status

from server.models.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from server.services import auth_service
from server.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _service_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Cloud service is not configured. Please contact the administrator.",
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest) -> TokenResponse:
    """Create a new account and return a login token."""
    try:
        user = auth_service.create_user(body.full_name, body.email, body.password)
    except ValueError as exc:
        if str(exc) == "email_exists":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        raise HTTPException(status_code=400, detail="Could not create account.")
    except RuntimeError:
        raise _service_unavailable()
    except Exception:
        raise HTTPException(status_code=502, detail="Cloud database error. Try again.")

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(
        access_token=token,
        user=UserPublic(id=user["id"], full_name=user["full_name"], email=user["email"]),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Verify credentials and return a login token."""
    try:
        user = auth_service.authenticate(body.email, body.password)
    except RuntimeError:
        raise _service_unavailable()
    except Exception:
        raise HTTPException(status_code=502, detail="Cloud database error. Try again.")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(
        access_token=token,
        user=UserPublic(id=user["id"], full_name=user["full_name"], email=user["email"]),
    )
