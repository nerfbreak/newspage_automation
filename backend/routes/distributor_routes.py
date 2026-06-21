"""Distributor API routes."""
from fastapi import APIRouter, Depends

from backend.dependencies import get_current_user
from backend.core.database import init_supabase, get_distributor_list, get_distributor_creds
from backend.models import DistributorListResponse, DistributorCredentials

router = APIRouter()


@router.get("/", response_model=DistributorListResponse)
async def list_distributors(user: dict = Depends(get_current_user)):
    supabase = init_supabase()
    dists = get_distributor_list(supabase)
    return DistributorListResponse(distributors=dists)


@router.get("/{distributor}/credentials", response_model=DistributorCredentials)
async def get_credentials(distributor: str, user: dict = Depends(get_current_user)):
    supabase = init_supabase()
    np_user, np_pass = get_distributor_creds(supabase, distributor)
    return DistributorCredentials(np_user_id=np_user, has_password=bool(np_pass))
