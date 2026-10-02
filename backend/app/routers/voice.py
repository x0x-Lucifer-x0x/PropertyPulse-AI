import base64

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.voice import transcribe_audio, synthesize_speech, VoiceUnavailableError

router = APIRouter(prefix="/api/voice", tags=["voice"])

MAX_AUDIO_BYTES = 15 * 1024 * 1024  # 15 MB


class SpeakRequest(BaseModel):
    text: str
    voice: str | None = None


class TranscribeResponse(BaseModel):
    text: str


class SpeakResponse(BaseModel):
    clips: list[str]  # base64-encoded WAV blobs, in playback order


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio received.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=400, detail="Audio clip is too long.")

    try:
        text = transcribe_audio(audio_bytes, file.filename or "recording.webm")
    except VoiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not text:
        raise HTTPException(status_code=422, detail="Couldn't make out any speech in that clip.")

    return TranscribeResponse(text=text)


@router.post("/speak", response_model=SpeakResponse)
def speak(req: SpeakRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="No text to speak.")

    try:
        clips = synthesize_speech(req.text, voice=req.voice or "autumn")
    except VoiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return SpeakResponse(clips=[base64.b64encode(c).decode("ascii") for c in clips])
