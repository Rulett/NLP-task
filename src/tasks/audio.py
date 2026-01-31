import asyncio
import json
import logging
import uuid
from typing import Any

from google.genai.errors import ClientError as GenAIClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.celery.celery import celery_app
from src.core.enums.audio import TaskStatusEnum
from src.db.models.audio import AudioProcessingTask
from src.db.session import async_session
from src.services.genai import genai_service
from src.services.minio import MinioService

logger = logging.getLogger(__name__)


@celery_app.task(name="process_audio_file")
def process_audio_file(task_id_str: str, file_key: str) -> dict[str, Any]:
    """
    Execute the background Celery task for processing an audio file.

    This task performs the following steps:
    1. Downloads the audio file from MinIO.
    2. Sends it to the GenAI service for transcription and commenting.
    3. Saves the result in PostgreSQL.

    Args:
        task_id_str (str): The string representation of the task ID (UUID).
        file_key (str): The key identifying the audio file in MinIO storage.

    Returns:
        dict[str, Any]: A dictionary containing the status of the task and additional details:
            - "status" (str): The final status of the task (e.g., SUCCESS or FAILURE).
            - "result" (str | None): The AI-generated response if successful.
            - "error" (str | None): The error message if the task failed.
            - "details" (dict | None): Additional error details, if available.

    Raises:
        ValueError: If the task with the specified ID is not found in the database.
        GenAIClientError: If an error occurs while interacting with the GenAI service.
        Exception: For any other unexpected errors during task execution.
    """
    task_id = uuid.UUID(task_id_str)
    logger.info(f"[WORKER] Received task: task_id={task_id}, file_key={file_key}")

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_process_audio_file_async(task_id, file_key))
    except Exception as e:
        error_msg = f"Critical error while running asynchronous logic for task {task_id}: {e}"
        logger.error(f"[WORKER] {error_msg}")
        return {"status": TaskStatusEnum.FAILURE.value, "error": error_msg}


async def _process_audio_file_async(task_id: uuid.UUID, file_key: str) -> dict[str, Any]:
    """
    Perform the asynchronous logic for processing an audio file.

    Args:
        task_id (uuid.UUID): The unique identifier of the task.
        file_key (str): The key identifying the audio file in MinIO storage.

    Returns:
        dict[str, Any]: A dictionary containing the status of the task and additional details:
            - "status" (str): The final status of the task (e.g., SUCCESS or FAILURE).
            - "result" (str | None): The AI-generated response if successful.
            - "error" (str | None): The error message if the task failed.
            - "details" (dict | None): Additional error details, if available.

    Raises:
        ValueError: If the task with the specified ID is not found in the database.
        GenAIClientError: If an error occurs while interacting with the GenAI service.
        Exception: For any other unexpected errors during task execution.
    """
    session: AsyncSession | None = None
    minio_service_instance: MinioService | None = None

    try:
        session = async_session()

        minio_service_instance = MinioService()
        await minio_service_instance.__aenter__()

        # 1. Update the task status to STARTED
        stmt = select(AudioProcessingTask).where(AudioProcessingTask.id == task_id).with_for_update()
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task with ID {task_id} not found in the database.")

        task.status = TaskStatusEnum.STARTED
        await session.commit()
        await session.refresh(task)
        logger.info(f"[WORKER] Task {task_id} status updated to STARTED.")

        # 2. Download the file from MinIO
        logger.info(f"[WORKER] Downloading {file_key} from MinIO...")
        audio_data = await minio_service_instance.download_file(file_key)
        logger.info(f"[WORKER] File {file_key} downloaded. Size: {len(audio_data)} bytes.")

        # 3. Send the audio to the AI service
        logger.info("[WORKER] Sending audio to AI service...")
        ai_result_text = await genai_service.transcribe_and_comment_audio(audio_data)
        logger.info(f"[WORKER] Received result from AI for task {task_id}.")

        # 4. Save the result in PostgreSQL as SUCCESS
        task.ai_response = ai_result_text
        task.status = TaskStatusEnum.SUCCESS
        await session.commit()
        await session.refresh(task)
        logger.info(f"[WORKER] Result for task {task_id} saved in the database. Status SUCCESS.")

        # Return SUCCESS status
        return {"status": TaskStatusEnum.SUCCESS.value, "result": ai_result_text}

    except GenAIClientError as e:
        error_code_http = e.code if hasattr(e, "code") else None

        error_details_from_exception = None
        if hasattr(e, "args") and e.args and isinstance(e.args[0], str):
            try:
                message_str = e.message if hasattr(e, "message") else str(e)
                if message_str:
                    json_part_start = message_str.find("{")
                    if json_part_start != -1:
                        json_str = message_str[json_part_start:]
                        error_details_from_exception = json.loads(json_str.replace("'", '"'))
            except (json.JSONDecodeError, IndexError):
                pass

        if not error_details_from_exception and hasattr(e, "response_json"):
            error_details_from_exception = e.response_json

        error_message_str = e.message if hasattr(e, "message") else str(e)
        formatted_error_message = f"GenAI error (HTTP: {error_code_http}): {error_message_str}"

        logger.error(f"[WORKER] GenAI error in task {task_id}: {formatted_error_message}")

        db_task_status = TaskStatusEnum.FAILURE
        ai_response_to_save = {
            "error_message": formatted_error_message,
            "details": error_details_from_exception,
            "http_status_code": error_code_http,
        }

        if session:
            try:
                await session.rollback()
                async with async_session() as rollback_session:
                    stmt = select(AudioProcessingTask).where(AudioProcessingTask.id == task_id).with_for_update()
                    result = await rollback_session.execute(stmt)
                    task_to_update = result.scalar_one_or_none()
                    if task_to_update:
                        task_to_update.status = db_task_status
                        task_to_update.error_message = formatted_error_message
                        task_to_update.ai_response = json.dumps(ai_response_to_save)
                        await rollback_session.commit()
                        logger.info(f"[WORKER] Task {task_id} status updated to {db_task_status.value} after GenAI error.")
            except Exception as rollback_e:
                logger.error(
                    f"[WORKER] Error rolling back/updating status after GenAI ClientError for task {task_id}: {rollback_e}"
                )

        return {
            "status": db_task_status.value,
            "error": formatted_error_message,
            "details": error_details_from_exception,
        }

    except Exception as e:
        error_msg = f"Unexpected error in task {task_id}: {e}"
        logger.error(f"[WORKER] {error_msg}")
        db_task_status = TaskStatusEnum.FAILURE

        if session:
            try:
                await session.rollback()
                async with async_session() as rollback_session:
                    stmt = select(AudioProcessingTask).where(AudioProcessingTask.id == task_id).with_for_update()
                    result = await rollback_session.execute(stmt)
                    task_to_update = result.scalar_one_or_none()
                    if task_to_update:
                        task_to_update.status = db_task_status
                        task_to_update.error_message = error_msg
                        task_to_update.ai_response = json.dumps({"general_error": error_msg})
                        await rollback_session.commit()
                        logger.info(f"[WORKER] Task {task_id} status updated to {db_task_status.value} after general error.")
            except Exception as rollback_e:
                logger.error(f"[WORKER] Error rolling back/updating status after general error for task {task_id}: {rollback_e}")

        return {"status": db_task_status.value, "error": error_msg}

    finally:
        if session:
            await session.close()
        if minio_service_instance:
            await minio_service_instance.__aexit__(None, None, None)
