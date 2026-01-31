import logging
import uuid
from typing import BinaryIO

import aiobotocore.session
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from src.core.config import settings

logger = logging.getLogger(__name__)


class MinioService:
    """
    Define a service for interacting with MinIO storage.

    This class provides asynchronous methods for uploading and downloading files to/from MinIO.
    It uses aiobotocore for asynchronous S3 client operations.

    Attributes:
        session (aiobotocore.session.Session): The session object for creating the S3 client.
        bucket_name (str): The name of the MinIO bucket to interact with.
        _s3_client (BaseClient | None): The S3 client instance, initialized in an async context.

    Raises:
        RuntimeError: If the MinioService is used outside of an async context manager.
        ClientError: If there is an issue with MinIO operations, such as missing buckets or file access errors.
    """

    def __init__(self) -> None:
        self.session = aiobotocore.session.get_session()
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._s3_client: BaseClient | None = None

    async def __aenter__(self) -> "MinioService":
        """
        Initialize the MinIO S3 client and ensure the bucket exists.

        Creates an asynchronous S3 client using the MinIO endpoint and credentials from the application settings.
        Ensures the specified bucket exists before returning the service instance.

        Returns:
            MinioService: The initialized MinioService instance.
        """
        self.client_context = self.session.create_client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT.split(':')[0]}:9000",
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
            config=Config(signature_version="s3v4"),
        )
        self._s3_client = await self.client_context.__aenter__()
        await self._ensure_bucket_exists()
        return self

    async def __aexit__(
        self,
        exc_type: BaseException | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Clean up the MinIO S3 client and context.

        Ensures the S3 client and its context are properly closed after use.
        """
        if self._s3_client and self.client_context:
            await self.client_context.__aexit__(exc_type, exc_val, exc_tb)
        self._s3_client = None
        self.client_context = None

    async def _ensure_bucket_exists(self) -> None:
        """
        Ensure the MinIO bucket exists.

        Checks if the bucket exists and creates it if it does not.

        Raises:
            ClientError: If an error occurs while checking or creating the bucket.
            RuntimeError: If the MinioService is used outside of an async context manager.
        """
        if not self._s3_client:
            raise RuntimeError("MinioService must be used within an async context manager.")
        try:
            await self._s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                await self._s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"MinIO: Bucket '{self.bucket_name}' created.")
            else:
                raise
        logger.info(f"MinIO: Bucket '{self.bucket_name}' is ready.")

    async def upload_file(self, file_content: BinaryIO, file_extension: str) -> str:
        """
        Upload a file to MinIO and return its key.

        Uses `put_object` to upload the file content as a stream. The file key is generated using a UUID.

        Args:
            file_content (BinaryIO): The file content to upload, typically a BytesIO object.
            file_extension (str): The file extension (e.g., "mp3") to append to the generated key.

        Returns:
            str: The unique key of the uploaded file in MinIO.

        Raises:
            RuntimeError: If the MinioService is used outside of an async context manager.
            ClientError: If an error occurs during the upload process.
        """
        if not self._s3_client:
            raise RuntimeError("MinioService must be used within an async context manager.")

        file_key = f"{uuid.uuid4()}.{file_extension}"
        try:
            await self._s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=f"audio/{file_extension}",
            )
            logger.info(f"MinIO: File '{file_key}' uploaded.")
            return file_key
        except ClientError as e:
            logger.error(f"MinIO: Error uploading file: {e}")
            raise

    async def download_file(self, file_key: str) -> bytes:
        """
        Download a file from MinIO and return its content as bytes.

        Uses `get_object` to retrieve the file and reads its content asynchronously.

        Args:
            file_key (str): The key of the file to download from MinIO.

        Returns:
            bytes: The content of the downloaded file.

        Raises:
            RuntimeError: If the MinioService is used outside of an async context manager.
            ClientError: If an error occurs during the download process.
        """
        if not self._s3_client:
            raise RuntimeError("MinioService must be used within an async context manager.")

        try:
            response = await self._s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            async with response["Body"] as stream:
                audio_data = await stream.read()
            logger.info(f"MinIO: File '{file_key}' downloaded. Size: {len(audio_data)} bytes.")
            return bytes(audio_data)
        except ClientError as e:
            logger.error(f"MinIO: Error downloading file '{file_key}': {e}")
            raise
