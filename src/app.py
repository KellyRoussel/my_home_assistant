from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from assistant import Assistant
import uvicorn
import asyncio
from logger import logger
# Initialize FastAPI app
app = FastAPI()

logger.reset()
assistant = Assistant()


# Define FastAPI route to serve the JSON
@app.get("/json")
async def serve_json():
    return logger.get_json_file()

@app.post("/restart")
async def restart():
    assistant.stop()
    logger.reset()
    assistant.start()
    return {"message": "Assistant restarted successfully"}


async def run_fastapi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    assistant.start()
    # Run FastAPI and assistant concurrently
    await asyncio.gather(
        run_fastapi(),
        # You can add other async tasks here if necessary
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Main program interrupted.")
