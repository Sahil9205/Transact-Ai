from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import MerchantModel
from app.domain.schemas import (
    MerchantAuthResponse,
    MerchantLoginRequest,
    MerchantProfileResponse,
    MerchantRegisterRequest,
)
from app.services.auth_service import AuthService, get_current_merchant

router = APIRouter(prefix="/auth/merchant", tags=["Merchant Authentication"])


@router.post(
    "/register",
    response_model=MerchantAuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Merchant",
    description="Registers a vendor with business details and password. Stores salted PBKDF2 hash in database and returns an RFC 7519 JWT bearer token.",
)
async def register_merchant_endpoint(
    payload: MerchantRegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> MerchantAuthResponse:
    """Register vendor with login credentials."""
    return await AuthService.register_merchant(session, payload)


@router.post(
    "/login",
    response_model=MerchantAuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Merchant Login",
    description="Authenticates vendor via login ID (email or phone number) and password. Returns JWT bearer token scoped to their store.",
)
async def login_merchant_endpoint(
    payload: MerchantLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> MerchantAuthResponse:
    """Authenticate vendor credentials and return access token."""
    return await AuthService.login_merchant(session, payload)


@router.get(
    "/me",
    response_model=MerchantProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated Merchant Profile",
    description="Returns the profile of the currently authenticated merchant decoded from the Bearer JWT token.",
)
async def get_current_merchant_profile(
    current_merchant: MerchantModel = Depends(get_current_merchant),
) -> MerchantProfileResponse:
    """Get authenticated merchant profile."""
    return MerchantProfileResponse(
        merchant_id=current_merchant.merchant_id,
        name=current_merchant.name,
        type=current_merchant.type,
        contact_email=current_merchant.contact_email,
        contact_phone=current_merchant.contact_phone,
        business_type=current_merchant.business_type,
        location=current_merchant.location,
        pincode=current_merchant.pincode,
        operational_status=current_merchant.operational_status,
        role=current_merchant.role,
    )
