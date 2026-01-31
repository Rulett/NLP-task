from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session
from src.services.minio import MinioService


async def get_minio_service() -> AsyncGenerator[MinioService]:
    """
    Provide a MinioService instance within the context.

    Use this dependency to obtain an instance of MinioService for handling MinIO operations.
    The instance is created and managed within an asynchronous context, ensuring proper resource cleanup.

    Yields:
        MinioService: An instance of MinioService to interact with MinIO storage.

    """
    async with MinioService() as service:
        yield service


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """
    Provide an asynchronous database session for FastAPI dependencies.

    Yields:
        AsyncSession: An instance of the asynchronous database session.

    """
    async with async_session() as session:
        yield session
