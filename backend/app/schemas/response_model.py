from pydantic import BaseModel, Field
from typing import List


class DrugResponse(BaseModel):
    drug_name: str = Field(
        ...,
        description="Drug name"
    )

    usage: str = Field(
        ...,
        description="Drug usage information"
    )

    dosage: str = Field(
        ...,
        description="Recommended dosage"
    )

    side_effects: List[str] = Field(
        default_factory=list,
        description="Common side effects"
    )

    source: str = Field(
        default="Drug Knowledge Base",
        description="Information source"
    )

    status: str = Field(
        default="SUCCESS",
        description="Request status"
    )