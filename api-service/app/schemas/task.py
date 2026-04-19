from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PositiveInt, TypeAdapter


class TaskType(str, Enum):
    RESIZE_IMAGE = "resize_image"
    SEND_EMAIL = "send_email"
    MERGE_PDFS = "merge_pdfs"
    SUMMARIZE_PDF = "summarize_pdf"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SendEmailPayload(BaseModel):
    to: EmailStr
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class ResizeImagePayload(BaseModel):
    image_path: str = Field(min_length=1)
    width: PositiveInt
    height: PositiveInt


class MergePdfsPayload(BaseModel):
    first_pdf_path: str = Field(min_length=1)
    second_pdf_path: str = Field(min_length=1)


class SummarizePdfPayload(BaseModel):
    pdf_path: str = Field(min_length=1)


PayloadModel = SendEmailPayload | ResizeImagePayload | MergePdfsPayload | SummarizePdfPayload

PAYLOAD_TYPE_MAP: dict[TaskType, TypeAdapter[PayloadModel]] = {
    TaskType.SEND_EMAIL: TypeAdapter(SendEmailPayload),
    TaskType.RESIZE_IMAGE: TypeAdapter(ResizeImagePayload),
    TaskType.MERGE_PDFS: TypeAdapter(MergePdfsPayload),
    TaskType.SUMMARIZE_PDF: TypeAdapter(SummarizePdfPayload),
}


class CreateTaskRequest(BaseModel):
    task_type: TaskType
    payload: dict[str, Any]

    def validate_payload(self) -> PayloadModel:
        return PAYLOAD_TYPE_MAP[self.task_type].validate_python(self.payload)


class CreateTaskResponse(BaseModel):
    task_id: UUID
    status: TaskStatus


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: TaskType
    status: TaskStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
