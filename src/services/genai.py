import asyncio
import logging
import os
import tempfile

from google import genai

from src.core.config import settings

logger = logging.getLogger(__name__)


class GenAIService:
    def __init__(self) -> None:
        """
        Initialize the processor with the Google GenAI SDK.

        Initializes a `genai.Client` instance using the provided API key and model name from the application settings.

        Attributes:
            client (genai.Client): The client used to interact with the Google GenAI API.
            model_name (str): The name of the GenerativeModel to use for processing.
            default_prompt (str): The default prompt used for transcribing and commenting on audio files.
        """
        self.client = genai.Client(api_key=settings.API_KEY)
        self.model_name = settings.GENAI_MODEL_NAME
        self.default_prompt = (
            "Listen to the audio. Write a transcription of the text. Then respond to or comment on what was said."
        )
        logger.info(f"GenAI: Initialized model '{self.model_name}'")

    async def transcribe_and_comment_audio(self, audio_data: bytes) -> str | None:
        """
        Save audio data to a temporary file, upload it to Google Files, send it to the GenerativeModel, and retrieve the response.

        Args:
            audio_data (bytes): The raw audio data to be processed.

        Returns:
            str | None: The response text from the GenerativeModel if successful, or None if an error occurs.

        Raises:
            Exception: If any error occurs during file handling, uploading, or interaction with the Google GenAI API.
        """
        logger.info(f"GenAI: Received audio for processing (size: {len(audio_data)} bytes).")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            temp_audio_file.write(audio_data)
            temp_file_path = temp_audio_file.name

        uploaded_file = None

        try:
            logger.info(f"Starting processing of temporary file: {temp_file_path}")

            uploaded_file = await asyncio.to_thread(self.client.files.upload, file=temp_file_path)

            logger.info(f"File '{temp_file_path}' uploaded to Google Files as '{uploaded_file.uri}'.")

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=[self.default_prompt, uploaded_file],
            )

            logger.info("Received response from the neural network.")
            return response.text

        except Exception as e:
            logger.error(f"Error interacting with Google GenAI: {e}", exc_info=True)
            raise e
        finally:
            if os.path.exists(temp_file_path):
                await asyncio.to_thread(os.remove, temp_file_path)

            if uploaded_file and uploaded_file.name:
                try:
                    await asyncio.to_thread(self.client.files.delete, name=uploaded_file.name)
                    logger.info(f"File '{uploaded_file.name}' deleted from Google Files.")
                except Exception as delete_e:
                    logger.error(f"Error deleting file from Google Files: {delete_e}", exc_info=True)


genai_service = GenAIService()
