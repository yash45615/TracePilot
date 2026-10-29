from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReleaseCreate(BaseModel):
    version: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)


class ReleaseRead(BaseModel):
    id: int
    version: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
