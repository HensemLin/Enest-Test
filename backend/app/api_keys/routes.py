from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from .schemas import ApiKeyResponse
from .service import create_api_key, delete_api_key, get_all_api_keys, get_api_key_by_id

router = APIRouter(prefix="/api/keys", tags=["API KEY"])


@router.get("/", response_model=List[ApiKeyResponse])
async def get_api_keys_endpoint(db: Session = Depends(get_db)):
    """Get all API keys."""
    return await get_all_api_keys(db)


@router.get("/{id}", response_model=ApiKeyResponse)
async def get_api_key_endpoint(id: str, db: Session = Depends(get_db)):
    """Get a specific API key by ID."""
    return await get_api_key_by_id(id, db)


@router.post("/", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key_endpoint(db: Session = Depends(get_db)):
    """Create a new API key."""
    return await create_api_key(db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key_endpoint(id: str, db: Session = Depends(get_db)):
    """Delete an API key by ID."""
    return await delete_api_key(id, db)
