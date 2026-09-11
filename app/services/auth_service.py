from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, UnauthorizedError, ValidationError
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import MerchantModel
from app.db.repository import MerchantRepository
from app.domain.schemas import (
    MerchantAuthResponse,
    MerchantLoginRequest,
    MerchantProfileResponse,
    MerchantRegisterRequest,
)

logger = get_logger(__name__)
settings = get_settings()
security = HTTPBearer(auto_error=False)


# --- Cryptographic Helpers (PBKDF2-HMAC-SHA256 & RFC 7519 JWT) ---

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()
    return f"{salt}${pw_hash}"


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verifies a plain password against a stored salt$hash string using constant-time comparison."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, expected_hash = hashed_password.split("$", 1)
        computed_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()
        return hmac.compare_digest(computed_hash, expected_hash)
    except Exception as e:
        logger.warning(f"Error during password verification: {e}")
        return False


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data_str: str) -> bytes:
    padding = "=" * ((4 - len(data_str) % 4) % 4)
    return base64.urlsafe_b64decode(data_str + padding)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generates an RFC 7519 compliant JSON Web Token signed with HMAC-SHA256."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    })

    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    header_b64 = _base64url_encode(header_json)
    payload_b64 = _base64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    signature_b64 = _base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Validates and decodes an RFC 7519 JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise UnauthorizedError("Invalid token format")

        header_b64, payload_b64, signature_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        expected_sig = hmac.new(
            settings.JWT_SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        actual_sig = _base64url_decode(signature_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise UnauthorizedError("Token signature verification failed")

        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp and exp < datetime.now(timezone.utc).timestamp():
            raise UnauthorizedError("Token has expired")

        return payload
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.warning(f"Failed to decode token: {e}")
        raise UnauthorizedError(f"Token invalid: {e}")


# --- Merchant Authentication Service ---

class AuthService:
    """Manages merchant credentials, registration, login, and token issuance."""

    @staticmethod
    async def register_merchant(
        session: AsyncSession,
        payload: MerchantRegisterRequest,
    ) -> MerchantAuthResponse:
        """Registers a new vendor account with hashed credentials in the database."""
        # 1. Check for existing account by email or phone
        if payload.contact_email:
            existing = await MerchantRepository.get_by_login_id(session, payload.contact_email)
            if existing:
                raise ValidationError("A merchant with this email address already exists")
        if payload.contact_phone:
            existing = await MerchantRepository.get_by_login_id(session, payload.contact_phone)
            if existing:
                raise ValidationError("A merchant with this phone number already exists")

        # 2. Hash password
        hashed_pw = hash_password(payload.password)

        # 3. Create merchant model
        merchant = MerchantModel(
            name=payload.name,
            type=payload.type.value if hasattr(payload.type, "value") else str(payload.type),
            contact_email=payload.contact_email.lower().strip() if payload.contact_email else None,
            contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
            password_hash=hashed_pw,
            business_type=payload.business_type or "kirana",
            location=payload.location,
            pincode=payload.pincode,
            description=payload.description,
            role="merchant",
            onboarding_status="active",
            operational_status="open",
        )
        session.add(merchant)
        await session.flush()
        await session.refresh(merchant)
        logger.info(f"Registered new merchant {merchant.name} (id={merchant.merchant_id})")

        # 4. Generate JWT
        token = create_access_token({
            "sub": merchant.merchant_id,
            "role": merchant.role,
            "name": merchant.name,
        })

        return MerchantAuthResponse(
            access_token=token,
            token_type="bearer",
            merchant=MerchantProfileResponse(
                merchant_id=merchant.merchant_id,
                name=merchant.name,
                type=merchant.type,
                contact_email=merchant.contact_email,
                contact_phone=merchant.contact_phone,
                business_type=merchant.business_type,
                location=merchant.location,
                pincode=merchant.pincode,
                operational_status=merchant.operational_status,
                role=merchant.role,
            ),
        )

    @staticmethod
    async def login_merchant(
        session: AsyncSession,
        payload: MerchantLoginRequest,
    ) -> MerchantAuthResponse:
        """Authenticates a merchant via login ID (email or phone) and password."""
        clean_id = payload.login_id.strip()
        merchant = await MerchantRepository.get_by_login_id(session, clean_id)

        if not merchant:
            logger.warning(f"Login failed: merchant not found for identifier '{clean_id}'")
            raise UnauthorizedError("Invalid login credentials")

        # Verify password (handle seeded accounts without password or check hash)
        if not merchant.password_hash:
            # For backward compatibility with initial seeded merchants, permit default testing password
            if payload.password == "Merchant@2026":
                # Upgrade and persist hash on first login
                merchant.password_hash = hash_password(payload.password)
                await session.flush()
            else:
                raise UnauthorizedError("Invalid login credentials")
        elif not verify_password(payload.password, merchant.password_hash):
            logger.warning(f"Login failed: incorrect password for merchant '{merchant.merchant_id}'")
            raise UnauthorizedError("Invalid login credentials")

        if not merchant.is_active:
            raise UnauthorizedError("Merchant account is deactivated")

        logger.info(f"Merchant logged in successfully: {merchant.name} ({merchant.merchant_id})")

        token = create_access_token({
            "sub": merchant.merchant_id,
            "role": merchant.role,
            "name": merchant.name,
        })

        return MerchantAuthResponse(
            access_token=token,
            token_type="bearer",
            merchant=MerchantProfileResponse(
                merchant_id=merchant.merchant_id,
                name=merchant.name,
                type=merchant.type,
                contact_email=merchant.contact_email,
                contact_phone=merchant.contact_phone,
                business_type=merchant.business_type,
                location=merchant.location,
                pincode=merchant.pincode,
                operational_status=merchant.operational_status,
                role=merchant.role,
            ),
        )


# --- Multi-Tenant Store Isolation Dependency ---

async def get_current_merchant(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> MerchantModel:
    """FastAPI dependency: authenticates the Bearer JWT token and retrieves the current Merchant."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    merchant_id = payload.get("sub")
    if not merchant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        merchant = await MerchantRepository.get_by_merchant_id(session, merchant_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Merchant not found or has been removed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return merchant


def verify_store_access(merchant_id: str, current_merchant: MerchantModel) -> None:
    """Enforces strict multi-tenant isolation: a merchant can only access their own store."""
    if current_merchant.role != "admin" and current_merchant.merchant_id != merchant_id:
        logger.warning(
            f"Access forbidden: merchant {current_merchant.merchant_id} attempted access to store {merchant_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You only have access to manage your own store.",
        )
