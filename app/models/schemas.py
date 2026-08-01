from pydantic import BaseModel, Field


class ImageTag(BaseModel):
    subject: str
    category: str
    attributes: list[str]
    caption: str
    confidence: float = Field(ge=0.0, le=1.0)