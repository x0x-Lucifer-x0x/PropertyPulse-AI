"""
Voice layer: Groq-hosted Whisper for speech-to-text, Groq-hosted Orpheus
for text-to-speech. Reuses the same GROQ_API_KEY and client as the chat
agent — no extra service or provider to configure.
"""
import logging
import re

from app.config import settings
from app.llm import client  # reuse the already-initialized Groq client

logger = logging.getLogger("property_pulse")

STT_MODEL = "whisper-large-v3-turbo"
TTS_MODEL = "canopylabs/orpheus-v1-english"
TTS_VOICE = "autumn"

# Orpheus' input is capped at 200 characters per call, so long replies are
# split on sentence boundaries into playable chunks and returned as a
# sequence of clips for the frontend to play back-to-back.
TTS_MAX_CHARS = 190


class VoiceUnavailableError(Exception):
    pass


def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    if client is None:
        raise VoiceUnavailableError("GROQ_API_KEY is not configured.")
    try:
        transcription = client.audio.transcriptions.create(
            file=(filename, file_bytes),
            model=STT_MODEL,
            response_format="json",
        )
        return (transcription.text or "").strip()
    except Exception as e:
        logger.exception("Groq transcription failed")
        raise VoiceUnavailableError(str(e)) from e


def _split_for_tts(text: str, max_chars: int = TTS_MAX_CHARS) -> list[str]:
    text = text.strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        # A single sentence longer than the limit is hard-split on words.
        while len(sentence) > max_chars:
            cut = sentence.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            piece, sentence = sentence[:cut].strip(), sentence[cut:].strip()
            if current:
                chunks.append(current)
                current = ""
            chunks.append(piece)
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks


def synthesize_speech(text: str, voice: str = TTS_VOICE) -> list[bytes]:
    """Returns a list of WAV byte blobs, one per chunk, to be played in
    order on the frontend."""
    if client is None:
        raise VoiceUnavailableError("GROQ_API_KEY is not configured.")

    chunks = _split_for_tts(text)
    clips: list[bytes] = []
    for chunk in chunks:
        try:
            response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=voice,
                input=chunk,
                response_format="wav",
            )
            clips.append(response.read())
        except Exception as e:
            logger.exception("Groq TTS failed for chunk: %r", chunk[:50])
            raise VoiceUnavailableError(str(e)) from e
    return clips
