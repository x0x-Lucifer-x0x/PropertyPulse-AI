import { ChatResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) {
    throw new Error("PropertyPulse AI is temporarily unavailable. Please try again.");
  }
  return res.json();
}

export async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData();
  form.append("file", blob, "recording.webm");

  const res = await fetch(`${API_URL}/api/voice/transcribe`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || "Couldn't transcribe that. Try again?");
  }
  const data = await res.json();
  return data.text as string;
}

export async function synthesizeSpeech(text: string): Promise<string[]> {
  const res = await fetch(`${API_URL}/api/voice/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || "Voice playback is unavailable right now.");
  }
  const data = await res.json();
  return data.clips as string[]; // base64 WAV blobs, in playback order
}
