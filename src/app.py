import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from assistant import Assistant
import uvicorn
from logger import logger, AppMessage
from config import Config
from wake_word_trainer import train_verifier


logger.reset()
assistant = Assistant()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting")
    asyncio.create_task(assistant.start())
    yield


app = FastAPI(lifespan=lifespan)

# Define FastAPI route to serve the JSON
@app.get("/json")
async def serve_json():
    return logger.get_json_file()

@app.post("/restart")
async def restart():
    assistant.stop()
    logger.reset()
    asyncio.create_task(assistant.start())
    return {"message": "Assistant restarted successfully"}


class ClassifyRequest(BaseModel):
    label: str  # "true" or "false"


@app.get("/wake-word-samples")
async def list_wake_word_samples():
    d = Config.WAKE_WORD_SAMPLES_DIR
    if not d.exists():
        return {"files": []}
    files = sorted(f.name for f in d.iterdir() if f.suffix == ".wav" and f.is_file())
    return {"files": files}


@app.get("/wake-word-samples/{filename}")
async def serve_wake_word_sample(filename: str):
    filepath = Config.WAKE_WORD_SAMPLES_DIR / filename
    if not filepath.exists() or filepath.suffix != ".wav":
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="audio/wav")


@app.post("/wake-word-samples/{filename}/classify")
async def classify_wake_word_sample(filename: str, body: ClassifyRequest):
    if body.label not in ("true", "false"):
        raise HTTPException(status_code=400, detail="label must be 'true' or 'false'")
    src = Config.WAKE_WORD_SAMPLES_DIR / filename
    if not src.exists():
        raise HTTPException(status_code=404, detail="File not found")
    dst_dir = Config.WAKE_WORD_SAMPLES_DIR / body.label
    dst_dir.mkdir(exist_ok=True)
    src.rename(dst_dir / filename)
    return {"message": f"Classified as {body.label} positive"}


@app.get("/retrain-info")
async def retrain_info():
    positive_clips = list(Config.WAKE_WORD_SAMPLES_TRUE_DIR.glob("*.wav")) if Config.WAKE_WORD_SAMPLES_TRUE_DIR.exists() else []
    negative_clips = list(Config.WAKE_WORD_SAMPLES_FALSE_DIR.glob("*.wav")) if Config.WAKE_WORD_SAMPLES_FALSE_DIR.exists() else []
    return {
        "positive_samples": len(positive_clips),
        "negative_samples": len(negative_clips),
        "min_positive_required": Config.MIN_POSITIVE_SAMPLES,
        "min_negative_required": Config.MIN_NEGATIVE_SAMPLES,
        "ready": len(positive_clips) >= Config.MIN_POSITIVE_SAMPLES and len(negative_clips) >= Config.MIN_NEGATIVE_SAMPLES,
    }


@app.post("/retrain")
async def retrain_verifier():
    positive_clips = list(Config.WAKE_WORD_SAMPLES_TRUE_DIR.glob("*.wav")) if Config.WAKE_WORD_SAMPLES_TRUE_DIR.exists() else []
    negative_clips = list(Config.WAKE_WORD_SAMPLES_FALSE_DIR.glob("*.wav")) if Config.WAKE_WORD_SAMPLES_FALSE_DIR.exists() else []

    if len(positive_clips) < Config.MIN_POSITIVE_SAMPLES:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {Config.MIN_POSITIVE_SAMPLES} positive samples, have {len(positive_clips)}",
        )
    if len(negative_clips) < Config.MIN_NEGATIVE_SAMPLES:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least {Config.MIN_NEGATIVE_SAMPLES} negative samples, have {len(negative_clips)}",
        )

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, train_verifier, [str(p) for p in positive_clips], [str(p) for p in negative_clips])

    assistant.action_listener.reload_model()
    logger.log(AppMessage(content=f"Verifier retrained: {len(positive_clips)} positive, {len(negative_clips)} negative samples"))

    return {
        "message": "Verifier retrained and reloaded successfully",
        "positive_samples": len(positive_clips),
        "negative_samples": len(negative_clips),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
