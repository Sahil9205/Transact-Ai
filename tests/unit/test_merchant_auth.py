import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError, ValidationError
from app.domain.schemas import (
    MerchantLoginRequest,
    MerchantRegisterRequest,
)
from app.domain.enums import ProviderType
from app.services.auth_service import (
    AuthService,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    verify_store_access,
)


def test_password_hashing_and_verification():
    """Verify PBKDF2 password hashing and constant-time verification."""
    raw_pw = "SecretPass@123"
    hashed = hash_password(raw_pw)

    assert "$" in hashed
    parts = hashed.split("$")
    assert len(parts) == 2
    assert len(parts[0]) == 32  # 16-byte hex salt

    # Correct password verifies
    assert verify_password(raw_pw, hashed) is True

    # Incorrect password fails
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pw, None) is False


def test_jwt_token_creation_and_validation():
    """Verify RFC 7519 JWT creation, signature, and decoding."""
    claims = {
        "sub": "merchant_test_123",
        "role": "merchant",
        "name": "Gupta Provision Store",
    }
    token = create_access_token(claims)
    assert token.count(".") == 2

    # Decode valid token
    decoded = decode_access_token(token)
    assert decoded["sub"] == "merchant_test_123"
    assert decoded["role"] == "merchant"
    assert decoded["name"] == "Gupta Provision Store"
    assert "exp" in decoded
    assert "iat" in decoded

    # Tampered signature fails
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(UnauthorizedError, match="signature verification failed"):
        decode_access_token(tampered)


@pytest.mark.asyncio
async def test_merchant_registration_and_login_flow(db_session: AsyncSession):
    """Verify vendor registration, password storage, and multi-credential login."""
    reg_data = MerchantRegisterRequest(
        name="Verma General Store",
        type=ProviderType.LOCAL_MERCHANT,
        contact_email="verma.store@test.com",
        contact_phone="+919876543210",
        password="StorePassword@2026",
        business_type="kirana",
        location="Sector 18, Noida",
        pincode="201301",
    )

    # 1. Register merchant
    reg_response = await AuthService.register_merchant(db_session, reg_data)
    assert reg_response.access_token is not None
    assert reg_response.merchant.name == "Verma General Store"
    assert reg_response.merchant.contact_email == "verma.store@test.com"
    merchant_id = reg_response.merchant.merchant_id

    # 2. Duplicate registration fails
    with pytest.raises(ValidationError, match="already exists"):
        await AuthService.register_merchant(db_session, reg_data)

    # 3. Login via Email
    login_email = MerchantLoginRequest(
        login_id="verma.store@test.com",
        password="StorePassword@2026",
    )
    res_email = await AuthService.login_merchant(db_session, login_email)
    assert res_email.access_token is not None
    assert res_email.merchant.merchant_id == merchant_id

    # 4. Login via Phone Number
    login_phone = MerchantLoginRequest(
        login_id="+919876543210",
        password="StorePassword@2026",
    )
    res_phone = await AuthService.login_merchant(db_session, login_phone)
    assert res_phone.access_token is not None
    assert res_phone.merchant.merchant_id == merchant_id

    # 5. Login with invalid password fails
    with pytest.raises(UnauthorizedError, match="Invalid login credentials"):
        await AuthService.login_merchant(
            db_session,
            MerchantLoginRequest(login_id="verma.store@test.com", password="BadPassword!"),
        )

    # 6. Login with unknown identifier fails
    with pytest.raises(UnauthorizedError, match="Invalid login credentials"):
        await AuthService.login_merchant(
            db_session,
            MerchantLoginRequest(login_id="unknown@test.com", password="StorePassword@2026"),
        )


@pytest.mark.asyncio
async def test_multi_tenant_store_isolation(db_session: AsyncSession):
    """Verify strict tenant isolation: merchant can only manage their own store."""
    # Register Merchant A
    res_a = await AuthService.register_merchant(
        db_session,
        MerchantRegisterRequest(
            name="Store A",
            contact_email="store.a@test.com",
            password="PasswordA@123",
        ),
    )
    # Register Merchant B
    res_b = await AuthService.register_merchant(
        db_session,
        MerchantRegisterRequest(
            name="Store B",
            contact_email="store.b@test.com",
            password="PasswordB@123",
        ),
    )

    from app.db.repository import MerchantRepository
    merchant_a = await MerchantRepository.get_by_merchant_id(db_session, res_a.merchant.merchant_id)
    merchant_b = await MerchantRepository.get_by_merchant_id(db_session, res_b.merchant.merchant_id)

    # Merchant A accessing Store A succeeds
    verify_store_access(merchant_a.merchant_id, merchant_a)

    # Merchant A attempting to access Store B is forbidden (403)
    with pytest.raises(HTTPException) as exc_info:
        verify_store_access(merchant_b.merchant_id, merchant_a)
    assert exc_info.value.status_code == 403
    assert "Forbidden" in exc_info.value.detail
