from pydantic import BaseModel, Field
from typing import Optional


class DrugRequest(BaseModel):
    drug_name: str = Field(
        ...,
        description="Drug name",
        example="Paracetamol"
    )

    language: str = Field(
        default="English",
        description="Response language"
    )

    user_id: Optional[str] = Field(
        default=None,
        description="User identifier"
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier"
    )