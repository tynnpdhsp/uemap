from pydantic import BaseModel, Field, field_validator


class CommentResponse(BaseModel):
    id: str
    author_display_name: str
    content: str
    created_at_display: str


class CommentMyResponseItem(BaseModel):
    id: str
    content_preview: str
    place_name: str
    place_public_id: int
    status_label: str
    created_at_display: str


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=2000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, v: str) -> str:
        return " ".join(v.split())
