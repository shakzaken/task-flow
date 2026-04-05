from pydantic import BaseModel


class UploadResponse(BaseModel):
    upload_id: str
    path: str
    filename: str

