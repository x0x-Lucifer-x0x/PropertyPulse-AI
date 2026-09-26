"use client";

import { useEffect, useRef, useState } from "react";
import { ChatMessage, LeadQualification } from "@/lib/types";
import { sendChatMessage } from "@/lib/api";
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

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || loading) return;

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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
      {/* Conversation column */}
      <div className="flex h-[70vh] flex-col border border-ink/10 bg-paperDim/40">
        <div ref={scrollRef} className="chat-scroll flex-1 space-y-5 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col justify-center">
              <p className="font-display text-2xl text-ink">
                What kind of home are you looking for?
              </p>
              <p className="mt-2 text-sm text-slate">
                Tell me your budget, location and timeline — I&apos;ll search real listings and explain every match.
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
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. 3BHK in Whitefield under 1 crore, ready to move in 6 months"
            className="flex-1 bg-transparent px-2 py-2 text-[15px] text-ink placeholder:text-slate/70 focus:outline-none"
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
        <div className="border border-ink/10 bg-white/60 p-5 text-xs leading-relaxed text-slate">
          PropertyPulse AI is a demo product. Listings shown are illustrative
          sample data, not live real-world inventory.
        </div>
      </div>
    </div>
  );
}
