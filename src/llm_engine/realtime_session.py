import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from openai import AsyncOpenAI

from llm_engine.models import SessionConfig
from logger import logger, AppMessage, ErrorMessage


class RealtimeSession:
    """Manages OpenAI Realtime API connection."""

    def __init__(self, config: SessionConfig):
        self._config = config
        self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._connection = None

    @property
    def connection(self):
        """The current active connection."""
        return self._connection

    @asynccontextmanager
    async def connect(self) -> AsyncIterator:
        """
        Create and configure a realtime connection.

        Use as async context manager:
            async with session.connect() as connection:
                ...
        """
        try:
            async with self._client.realtime.connect(model=self._config.model) as connection:
                logger.log(AppMessage(content="Connected to OpenAI Realtime API"))
                self._connection = connection

                await connection.session.update(session=self._config.to_api_dict())

                yield connection
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : connect: {e}"))
            raise
        finally:
            self._connection = None

    async def send_audio(self, audio_base64: str) -> None:
        """Send audio data to the API."""
        if self._connection:
            await self._connection.input_audio_buffer.append(audio=audio_base64)

    async def commit_audio(self) -> None:
        """Commit the audio buffer and request response."""
        if self._connection:
            await self._connection.input_audio_buffer.commit()
            await self._connection.response.create()
