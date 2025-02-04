import asyncio
import base64
import os
import subprocess
import time
import numpy as np
from openai import AsyncOpenAI
from session.assistant_context import Conversation
from stt.record import Record
from tools.tool import Tool
from logger import logger, ErrorMessage


class RealTimeEngine:

    def __init__(self, tools: list[Tool] = None):
        try:
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._model = "gpt-4o"
            self.tools = tools if tools is not None else []
            self.player_process = None
            self.is_first_chunk = True
            self.output_sample_rate = 24000  # 24kHz sample rate
            self.bytes_per_sample = 2  # s16le = 2 bytes per sample
            self.stream_start_time = None
            self.total_audio_duration = 0
             # Input audio format (matching your Recorder)
            self.input_sample_rate = 44100
            self.input_format = np.int16
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : __init__: {e}"))
            raise Exception(f"{self.__class__.__name__} : __init__: {e}")
        

    async def convert_audio_format(self, audio_base64: str) -> str:
        """Convert audio from input format to OpenAI API format"""
        try:
            # Decode base64 to raw bytes
            audio_bytes = base64.b64decode(audio_base64)
            
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_bytes, dtype=self.input_format)
            
            # Create temporary files for conversion
            input_file = "temp_input.raw"
            output_file = "temp_output.raw"
            
            # Save raw input audio
            with open(input_file, 'wb') as f:
                f.write(audio_bytes)
            
            # Use ffmpeg to convert sample rate and ensure format
            subprocess.run([
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-f', 's16le',  # Input format
                '-ar', str(self.input_sample_rate),
                '-ac', '1',
                '-i', input_file,
                '-f', 's16le',  # Output format
                '-ar', str(self.output_sample_rate),
                '-ac', '1',
                output_file
            ], check=True, capture_output=True)
            
            # Read converted audio
            with open(output_file, 'rb') as f:
                converted_audio = f.read()
            
            # Clean up temporary files
            os.remove(input_file)
            os.remove(output_file)
            
            # Convert back to base64
            return base64.b64encode(converted_audio).decode('utf-8')
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : convert_audio_format: {e}"))
            raise Exception(f"{self.__class__.__name__} : convert_audio_format: {e}")


    async def start(self, record: Record):
        response = None
        audio_input_base64_bytes = record.get_base64_raw_bytes()
        converted_audio = await self.convert_audio_format(audio_input_base64_bytes)
            
        #connection = await self._client.beta.realtime.connect(model="gpt-4o-realtime-preview").enter()
       # print("Connection established: ", connection)
        async with self._client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
            await connection.session.update(session={'modalities': ['audio', 'text'],
                                                     "voice": "echo", 
                                                     "input_audio_transcription": {
            "model": "whisper-1"
        },})

            await connection.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_audio", "audio": converted_audio}],
                }
            )
            await connection.response.create()
            #print("self.connection._connection: ", type(connection._connection))

            try:
                async for event in connection:
                    if event.type == "error":
                        print(f"Error event: {event.error}")
                    #elif event.type == "conversation.item.input_audio_transcription.completed":
                     #   print(f"User Transcription: {event.transcript}")
                    #elif event.type == "response.audio_transcript.delta":
                     #   print(f"Transcript: {event.delta}")
                    elif event.type == "response.audio_transcript.done":
                        response = event.transcript
                        
                    elif event.type == "response.audio.delta":
                        await self.stream_audio(event.delta)
                    elif event.type == "response.done":
                        if self.player_process and self.player_process.poll() is None:
                            # Calculate how long we've been playing
                            time_elapsed = time.time() - self.stream_start_time
                            # Calculate how much audio we should play in total
                            remaining_duration = max(0, self.total_audio_duration - time_elapsed) + 1
                            print(f"Elapsed: {time_elapsed:.2f}s, Total: {self.total_audio_duration:.2f}s, Remaining: {remaining_duration:.2f}s")
                            if remaining_duration > 0:
                                await asyncio.sleep(remaining_duration)
                        await self.cleanup_player()
                        return response
                    else:
                        print(event.type)
            except Exception as e:
                print(f"Error in event loop: {e}")
                await self.cleanup_player()

    async def cleanup_player(self):
        if self.player_process:
            try:
                if self.player_process.stdin:
                    self.player_process.stdin.close()
                self.player_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.player_process.kill()
            finally:
                self.player_process = None
                self.is_first_chunk = True
                self.stream_start_time = None
                self.total_audio_duration = 0

    async def stream_audio(self, audio_chunk: str):
        try:
            decoded_data = base64.b64decode(audio_chunk)
            # Calculate duration of this chunk
            chunk_samples = len(decoded_data) // self.bytes_per_sample
            chunk_duration = chunk_samples / self.output_sample_rate
            self.total_audio_duration += chunk_duration
            
            if self.is_first_chunk:
                await self.cleanup_player()
                
                
                self.player_process = subprocess.Popen(
                    ['ffplay',
                     '-f', 's16le',     # Signed 16-bit little-endian
                     '-ar', f'{self.output_sample_rate}',  # Sample rate 24kHz
                     '-ac', '1',        # Mono audio
                     '-i', 'pipe:0',    # Read from stdin
                     '-nodisp',         # No display
                     '-autoexit',       # Exit when done
                     '-volume', '100',  # Full volume
                     '-sync', 'ext'     # Use external clock for timing
                    ],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    bufsize=0
                )
                self.stream_start_time = time.time()
                self.is_first_chunk = False
            
            if self.player_process and self.player_process.stdin:
                if self.player_process.poll() is None:
                    self.player_process.stdin.write(decoded_data)
                    self.player_process.stdin.flush()
                else:
                    print("Player process has terminated unexpectedly")
                    await self.cleanup_player()
                    
        except BrokenPipeError:
            print("Broken pipe - player process may have terminated")
            await self.cleanup_player()
        except Exception as e:
            print(f"Error streaming audio: {e}")
            await self.cleanup_player()
        
        