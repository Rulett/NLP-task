import io
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session, get_minio_service
from src.core.enums.audio import TaskStatusEnum
from src.db.models.audio import AudioProcessingTask
from src.schemas.audio import AudioProcessResponseSchema, AudioTaskResultResponseSchema
from src.services.minio import MinioService
from src.tasks.audio import process_audio_file

logger = logging.getLogger(__name__)
audio_router = APIRouter(prefix="/audiofiles")


@audio_router.post("/process", status_code=202, response_model=AudioProcessResponseSchema)
async def process_audio(
    audio_file: Annotated[UploadFile, File(description="Audiofile for processing")],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    minio_service: Annotated[MinioService, Depends(get_minio_service)],
) -> AudioProcessResponseSchema:
    """
    Accept an audio file, store it in MinIO, create a task in the database,
    and send a Celery task for processing. Return the task ID.

    Args:
        audio_file (UploadFile): The audio file to be processed. Must have a content type starting with "audio/".
        session (AsyncSession): The database session dependency.
        minio_service (MinioService): The MinIO service dependency for file uploads.

    Returns:
        AudioProcessResponseSchema: A schema containing the task ID of the created processing task.

    Raises:
        HTTPException: If the uploaded file is not a valid audio file (status code 400).
    """
    if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="The file must be an audiofile")

    file_extension = audio_file.filename.split(".")[-1] if audio_file.filename else "bin"
    file_content = await audio_file.read()

    file_stream = io.BytesIO(file_content)
    file_key = await minio_service.upload_file(file_stream, file_extension)

    new_task = AudioProcessingTask(status=TaskStatusEnum.PENDING, audio_file_key=file_key)
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)

    process_audio_file.apply_async(args=(str(new_task.id), file_key), queue="audio_processing")

    logger.info(f"API: Task {new_task.id} sent to Celery.")
    return AudioProcessResponseSchema(task_id=new_task.id)


@audio_router.get("/results/{task_id}", status_code=200, response_model=AudioTaskResultResponseSchema)
async def get_task_result(
    task_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AudioTaskResultResponseSchema:
    """
    Retrieve information about the status and result of an audio processing task by its ID.

    Args:
        task_id (UUID): The unique identifier of the audio processing task.
        session (AsyncSession): The database session dependency.

    Returns:
        AudioTaskResultResponseSchema: A schema containing the task ID, status, timestamps,
                                       and optional result or error message.

    Raises:
        HTTPException: If the task with the specified ID is not found (status code 404).
    """
    stmt = select(AudioProcessingTask).where(AudioProcessingTask.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    return AudioTaskResultResponseSchema(
        task_id=task.id,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        result=task.ai_response if task.status == TaskStatusEnum.SUCCESS else None,
        error_message=task.error_message if task.status == TaskStatusEnum.FAILURE else None,
    )
