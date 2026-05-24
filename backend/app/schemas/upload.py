from typing import List
from pydantic import BaseModel

class UploadMediaResponse(BaseModel):
    object_key: str
    preview_url: str

class UploadImagesResponse(BaseModel):
    object_keys: List[str]
    preview_urls: List[str]
