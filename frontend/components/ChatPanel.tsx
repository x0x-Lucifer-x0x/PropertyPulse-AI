"use client";

import { useEffect, useRef, useState } from "react";
import { ChatMessage, LeadQualification } from "@/lib/types";
import { sendChatMessage, transcribeAudio, synthesizeSpeech } from "@/lib/api";
import { playClipsSequentially } from "@/lib/audio";
import MessageBubble from "./MessageBubble";
import LeadPanel from "./LeadPanel";

const SUGGESTED_PROMPTS = [
  "Find me a 3BHK in Whitefield under ₹1 crore",
  "Show me villas near Sarjapur under ₹2 crore",
  "I'm looking for a property for my family within 6 months",
];

function newSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ChatPanel() {
  const [sessionId] = useState(newSessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lead, setLead] = useState<LeadQualification | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Voice: push-to-talk recording
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Voice: spoken replies
  const [voiceMode, setVoiceMode] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const stopPlaybackRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    return () => stopPlaybackRef.current?.();
  }, []);

  async function speak(text: string) {
    stopPlaybackRef.current?.();
    try {
      setIsSpeaking(true);
      const clips = await synthesizeSpeech(text);
      const { done, stop } = playClipsSequentially(clips);
      stopPlaybackRef.current = stop;
      await done;
    } catch {
      // Voice playback failing shouldn't block the (already-shown) text reply.
    } finally {
      setIsSpeaking(false);
    }
  }

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

    stopPlaybackRef.current?.();
    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content }]);
    setLoading(true);

    try {
      const res = await sendChatMessage(sessionId, content);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply, properties: res.properties },
      ]);
      if (res.lead) setLead(res.lead);
      if (voiceMode && res.reply) speak(res.reply);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function startRecording() {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        if (blob.size === 0) return;
        setIsTranscribing(true);
        try {
          const text = await transcribeAudio(blob);
          if (text) handleSend(text);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Couldn't transcribe that.");
        } finally {
          setIsTranscribing(false);
        }
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch {
      setError("Couldn't access your microphone. Check your browser's permission settings.");
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      {/* Conversation column */}
      <div className="flex h-[70vh] flex-col border border-ink/10 bg-paperDim/40">
        <div className="flex items-center justify-end border-b border-ink/10 bg-paper px-3 py-2">
          <button
            type="button"
            onClick={() => {
              setVoiceMode((v) => !v);
              if (voiceMode) stopPlaybackRef.current?.();
            }}
            aria-pressed={voiceMode}
            className={`flex items-center gap-1.5 border px-2.5 py-1 text-xs font-medium transition-colors ${
              voiceMode
                ? "border-brass bg-brassDim/30 text-ink"
                : "border-ink/15 text-slate hover:border-ink/30"
            }`}
          >
            <span className={`inline-block h-1.5 w-1.5 rounded-full ${isSpeaking ? "bg-sage animate-pulse" : voiceMode ? "bg-brass" : "bg-slate"}`} />
            {voiceMode ? "Spoken replies on" : "Spoken replies off"}
          </button>
        </div>

        <div ref={scrollRef} className="chat-scroll flex-1 space-y-5 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col justify-center">
              <p className="font-display text-2xl text-ink">
                What kind of home are you looking for?
              </p>
              <div className="mt-6 flex flex-col gap-2">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="w-fit border border-ink/15 bg-white/70 px-4 py-2 text-left text-sm text-ink transition-colors hover:border-brass hover:bg-brassDim/30"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}

          {loading && (
            <div className="flex items-center gap-1.5 px-1 text-slate">
              <span className="typing-dot inline-block h-1.5 w-1.5 rounded-full bg-slate [animation-delay:0s]" />
              <span className="typing-dot inline-block h-1.5 w-1.5 rounded-full bg-slate [animation-delay:0.15s]" />
              <span className="typing-dot inline-block h-1.5 w-1.5 rounded-full bg-slate [animation-delay:0.3s]" />
            </div>
          )}

          {error && (
            <div className="border border-clay/30 bg-clay/5 px-4 py-2.5 text-sm text-clay">
              {error}
            </div>
          )}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2 border-t border-ink/10 bg-paper p-3"
        >
          <button
            type="button"
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onMouseLeave={() => isRecording && stopRecording()}
            onTouchStart={(e) => {
              e.preventDefault();
              startRecording();
            }}
            onTouchEnd={(e) => {
              e.preventDefault();
              stopRecording();
            }}
            disabled={isTranscribing || loading}
            title="Hold to talk"
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border transition-colors disabled:opacity-40 ${
              isRecording
                ? "border-clay bg-clay/10 text-clay"
                : "border-ink/15 text-slate hover:border-ink/30"
            }`}
          >
            {isRecording ? (
              <span className="h-2.5 w-2.5 rounded-sm bg-clay" />
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4" />
              </svg>
            )}
          </button>

          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isTranscribing
                ? "Transcribing..."
                : isRecording
                ? "Listening — release to send"
                : "e.g. 3BHK in Whitefield under 1 crore, ready to move in 6 months"
            }
            disabled={isRecording || isTranscribing}
            className="flex-1 bg-transparent px-2 py-2 text-[15px] text-ink placeholder:text-slate/70 focus:outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-ink px-4 py-2 text-sm font-medium text-paper transition-opacity disabled:opacity-30"
          >
            Send
          </button>
        </form>
      </div>

      {/* Sidebar */}
      <div className="flex flex-col gap-4">
        <LeadPanel lead={lead} />
      </div>
    </div>
  );
}
