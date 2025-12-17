from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiKeyResponse(BaseModel):
    """Response model for API key data."""
    id: str
    apiKey: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
