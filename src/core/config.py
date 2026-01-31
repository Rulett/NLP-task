from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Define the configuration settings for the application, loading values from environment variables.

    Attributes:
        DATABASE_URL (str): The URL for connecting to the database. Defaults to an empty string.
        REDIS_URL (str): The URL for connecting to Redis. Defaults to "redis://redis:6379/0".
        MINIO_ENDPOINT (str): The endpoint URL for MinIO storage. Defaults to an empty string.
        MINIO_ROOT_USER (str): The root username for MinIO authentication. Defaults to an empty string.
        MINIO_ROOT_PASSWORD (str): The root password for MinIO authentication. Defaults to an empty string.
        MINIO_BUCKET_NAME (str): The name of the MinIO bucket to use. Defaults to an empty string.
        GENAI_MODEL_NAME (str): The name of the GenAI model to use. Defaults to an empty string.
        API_KEY (str): The API key for authentication or external services. Defaults to an empty string.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = ""

    REDIS_URL: str = "redis://redis:6379/0"

    MINIO_ENDPOINT: str = ""
    MINIO_ROOT_USER: str = ""
    MINIO_ROOT_PASSWORD: str = ""
    MINIO_BUCKET_NAME: str = ""

    GENAI_MODEL_NAME: str = ""
    API_KEY: str = ""


settings = Settings()
