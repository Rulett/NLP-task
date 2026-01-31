from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.types import created_at, updated_at, uuidpk
from src.core.enums.audio import TaskStatusEnum
from src.db.models.base import Base


class AudioProcessingTask(Base):
    """
    Define the model for storing information about audio processing tasks.

    This class represents the `audio_processing_tasks` table in the database. It includes fields
    for tracking the status, file key, AI response, error messages, and timestamps of audio processing tasks.

    Attributes:
        id (Mapped[uuidpk]): The unique identifier (UUID) of the task.
        status (Mapped[TaskStatusEnum]): The current status of the task. Defaults to `PENDING`.
        audio_file_key (Mapped[str]): The key identifying the audio file in storage. Cannot be null.
        ai_response (Mapped[str | None]): The AI-generated response for the task, if available. Can be null.
        error_message (Mapped[str | None]): The error message if the task failed. Can be null.
        created_at (Mapped[created_at]): The timestamp when the task was created.
        updated_at (Mapped[updated_at]): The timestamp when the task was last updated.
    """

    __tablename__ = "audio_processing_tasks"

    id: Mapped[uuidpk]
    status: Mapped[TaskStatusEnum] = mapped_column(default=TaskStatusEnum.PENDING, nullable=False)
    audio_file_key: Mapped[str] = mapped_column(String, nullable=False)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    def __repr__(self) -> str:
        """Return a string representation of the task for debugging purposes."""
        return f"<AudioProcessingTask(id='{self.id}', status='{self.status}', audio_file_key='{self.audio_file_key}')>"
