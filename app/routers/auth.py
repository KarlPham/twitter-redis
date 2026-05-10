from fastapi import APIRouter, HTTPException
from app.database import get_primary, get_replica
from app.auth import hash_password, verify_password, create_token
from app.models import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest):
    """
    Steps:
      1. Check username/email not already taken
      2. Hash the password
      3. Insert into users table
      4. Return JWT so user is logged in immediately
    """
    # 1. Check for duplicates — read from replica
    db = get_replica()
    existing = await db.fetchrow(
        "SELECT id FROM users WHERE username = $1 OR email = $2",
        body.username, body.email,
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username or email already taken")

    # 2 + 3. Hash password and insert — write to primary
    hashed = hash_password(body.password)
    primary = get_primary()
    user = await primary.fetchrow(
        """
        INSERT INTO users (username, email, password_hash)
        VALUES ($1, $2, $3)
        RETURNING id, username, email, created_at
        """,
        body.username, body.email, hashed,
    )

    # 4. Issue JWT
    token = create_token(str(user["id"]))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    """
    Steps:
      1. Find user by username
      2. Verify password against bcrypt hash
      3. Return JWT
    """
    # 1. Find user — read from replica
    db = get_replica()
    user = await db.fetchrow(
        "SELECT id, password_hash FROM users WHERE username = $1",
        body.username,
    )

    # Use generic message — don't reveal whether username exists
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2. Verify password
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 3. Issue JWT
    token = create_token(str(user["id"]))
    return TokenResponse(access_token=token)