import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.enums.audio import TaskStatusEnum


class AudioProcessResponseSchema(BaseModel):
    """
    Define the response schema for the `/audiofiles/process` endpoint.

    Attributes:
        task_id (uuid.UUID): The unique identifier of the created audio processing task.
    """

    task_id: uuid.UUID = Field(description="The unique ID of the created audio processing task.")


class AudioTaskResultResponseSchema(BaseModel):
    """
    Define the response schema for the `/audiofiles/results/{task_id}` endpoint.

    Attributes:
        task_id (uuid.UUID): The unique identifier of the task.
        status (TaskStatusEnum): The current status of the task.
        created_at (datetime): The creation timestamp of the task.
        updated_at (datetime | None): The last update timestamp of the task, if available.
        result (Any | None): The result of the audio processing, if the status is SUCCESS.
        error_message (str | None): The error message, if the status is FAILURE.
    """

    task_id: uuid.UUID = Field(description="The unique ID of the task.")
    status: TaskStatusEnum = Field(description="The current status of the task.")
    created_at: datetime = Field(description="The creation timestamp of the task.")
    updated_at: datetime | None = Field(None, description="The last update timestamp of the task, if available.")
    result: Any | None = Field(None, description="The result of the audio processing, if the status is SUCCESS.")
    error_message: str | None = Field(None, description="The error message, if the status is FAILURE.")
