import asyncio
import base64
from datetime import datetime
import os
import queue
import subprocess
import time
import numpy as np
from openai import AsyncOpenAI
from session.assistant_context import Conversation
from stt.record import Record
from tools.tool import Tool
from logger import AppMessage, logger, ErrorMessage
import sounddevice as sd

class RealTimeEngine:
    FORMAT = np.int16
    CHANNELS = 1
    RATE = 24000
    CHUNK = 1024
    MAX_DURATION = 60

    def __init__(self, tools: list[Tool] = None):
        try:
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._model = "gpt-4o"
            self.connection = None
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
          
           # Use a regular Queue for thread-safe operations
            self.audio_queue = queue.Queue()
            self.is_processing = True
            self.recording_start_time = None
            self.event_processing_task = None
            self.audio_processing_task = None
            self.stop_event = asyncio.Event()
            self.loop = None  # Store the event loop
            self.timeout_reached = False


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


    async def start(self):
        response = None
        self.loop = asyncio.get_running_loop()
        
        async with self._client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
            self.connection = connection
            await connection.session.update(session={
                'modalities': ['audio', 'text'],
                "voice": "echo",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "input_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 1000,
                    "create_response": True
                },
            })

            try:
                print("About to start recording...")
                self.notify()
                await self.start_recording()
                print("Recording started, now starting event and audio processing...")

                self.event_processing_task = asyncio.create_task(self.process_events(connection))
                self.audio_processing_task = asyncio.create_task(self.process_audio_queue())
                
                response = await self.event_processing_task
                print("Start is over")
                
            except Exception as e:
                print(f"Error in main loop: {e}")
            finally:
                print("Finally")
                self.stop_event.set()
                self.is_processing = False
                if self.audio_processing_task:
                    print("Cancelling audio processing task...")
                    await self.audio_processing_task
                print("Audio processing task done")
                await self.cleanup_player()
                self.connection = None
                return response

    async def process_events(self, connection):
        """Separate task for processing events from the connection"""
        response = None
        try:
            print("Processing events...")
            async for event in connection:
                #print(f"Event: {event.type}")
                if event.type == "error":
                    print(f"Error event: {event.error}")
                elif event.type == "input_audio_buffer.committed":
                    print("Audio buffer committed, stopping recording...")
                    self.stop_event.set()  # Stop recording when audio is committed
                elif event.type == "conversation.item.input_audio_transcription.completed":
                    #print("Input audio transcription completed")
                    print(f"User Transcript: {event.transcript}")
                elif event.type == "response.audio_transcript.done":
                    response = event.transcript
                elif event.type == "response.audio.delta":
                    await self.stream_audio(event.delta)
                elif event.type == "response.done":
                    print("Response done")
                    print(event.response)
                    self.stop_event.set()  # Signal to stop recording
                    await self._handle_response_done()
                    return response
                #else:
                 #   print(event.type)
        except Exception as e:
            print(f"Error in event processing: {e}")
            raise

    async def _handle_response_done(self):
        print("Response done, waiting for audio to finish...")
        if self.player_process and self.player_process.poll() is None:
            # Calculate how long we've been playing
            time_elapsed = time.time() - self.stream_start_time
            # Calculate how much audio we should play in total
            remaining_duration = max(0, self.total_audio_duration - time_elapsed) + 1
            print(f"Elapsed: {time_elapsed:.2f}s, Total: {self.total_audio_duration:.2f}s, Remaining: {remaining_duration:.2f}s")
            if remaining_duration > 0:
                await asyncio.sleep(remaining_duration)
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
        
    async def start_recording(self):
        try:
            print("Starting recording...")
            self.is_recording = True
            self.frames = []
            self.recording_start_time = time.time()
            
            self.stream = sd.InputStream(
                samplerate=self.RATE,
                channels=self.CHANNELS,
                dtype=self.FORMAT,
                callback=self.audio_callback
            )
            
            
            self.stream.start()
            logger.log(AppMessage(content=f"{self.__class__.__name__}: Start recording"))
            
            # Create monitoring task
            asyncio.create_task(self._monitor_recording())
            
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : start_recording: {e}"))
            raise Exception(f"{self.__class__.__name__} : start_recording: {e}")

    async def _monitor_recording(self):
        """Monitor the recording and stop it when either the stop event is set or max duration is reached"""
        while not self.stop_event.is_set():
            # Check for timeout
            if self.recording_start_time and time.time() - self.recording_start_time >= self.MAX_DURATION:
                print("Recording timeout reached...")
                self.timeout_reached = True
                self.stop_event.set()
                break
            await asyncio.sleep(0.1)  # Small sleep to prevent busy waiting
        
        print("Stop event received, stopping recording...")
        self.stop_recording()
        

    def audio_callback(self, indata, frames, time_info, status):
        if status:
            print(status, flush=True)
        
        try:
            if not self.stop_event.is_set():
                raw_audio_data = indata.copy().astype(self.FORMAT).tobytes()
                base64_audio = base64.b64encode(raw_audio_data).decode('utf-8')
                
                # Put the audio data in the queue
                self.audio_queue.put_nowait(base64_audio)
                
                self.frames.append(indata.copy())

                # Check for timeout
                if self.recording_start_time and time.time() - self.recording_start_time >= self.MAX_DURATION:
                    if self.loop:
                        # Create a proper coroutine to set the stop event
                        async def set_stop():
                            self.timeout_reached = True
                            self.stop_event.set()
                        # Run it in the event loop
                        asyncio.run_coroutine_threadsafe(set_stop(), self.loop)
                    
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : audio_callback: {e}"))
            print(f"Error in audio callback: {e}")

    async def process_audio_queue(self):
        """Process audio chunks from the queue"""
        print("Processing audio queue...")
        try:
            while self.is_processing and not self.stop_event.is_set():
                try:
                    # Non-blocking check for audio data
                    base64_audio = self.audio_queue.get_nowait()
                    if self.connection:
                        await self.connection.input_audio_buffer.append(audio=base64_audio)
                except queue.Empty:
                    # No audio data available, wait a bit
                    await asyncio.sleep(0.01)
                    continue
                except Exception as e:
                    print(f"Error processing audio chunk: {e}")
                    await asyncio.sleep(0.01)

            if self.timeout_reached and self.connection:
                print("Sending commit event due to timeout...")
                try:
                    await self.connection.input_audio_buffer.commit()
                    await self.connection.response.create()
                    print("Commit event sent successfully")
                except Exception as e:
                    print(f"Error sending commit event: {e}")
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : process_audio_queue: {e}"))
            print(f"Error in process_audio_queue: {e}")

    def notify(self, retries=1):
        try:
            print("Playing notification sound...")
            player_command = ["ffplay", "-nodisp", "-autoexit", "./listening.mp3"]
            start_time = time.perf_counter()
            subprocess.run(player_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1.5)
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.log(AppMessage(content=f"ffplay duration {duration:.2f} seconds."))
            print(f"ffplay duration {duration:.2f} seconds.")
        except subprocess.TimeoutExpired:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : notify : ffplay timed out - remaining {retries} attempts"))
            if retries > 0:
                return self.notify(retries=retries-1)
            
    def stop_recording(self):
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
            
        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : stop_recording: {e}"))
            raise Exception(f"{self.__class__.__name__} : stop_recording: {e}")