import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from assistant import Assistant
import uvicorn
from logger import logger


logger.reset()
assistant = Assistant()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting")
    assistant.start()
    yield
    assistant.stop()
    task.cancel()


app = FastAPI(lifespan=lifespan)

# Define FastAPI route to serve the JSON
@app.get("/json")
async def serve_json():
    return logger.get_json_file()

@app.post("/restart")
async def restart():
    assistant.stop()
    logger.reset()
    await assistant.start()
    return {"message": "Assistant restarted successfully"}

async def run_assistant():
    await assistant.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
