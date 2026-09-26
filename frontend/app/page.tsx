import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-paper">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-8">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-brass">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-brass" />
            AI Sales Assistant
          </div>
          <h1 className="mt-2 font-display text-4xl text-ink sm:text-5xl">
            PropertyPulse <span className="italic">AI</span>
          </h1>
          <p className="mt-2 max-w-xl text-[15px] text-slate">
            Describe what you&apos;re looking for in plain language. PropertyPulse
            searches real listings, ranks matches, explains why they fit, and
            tells you what to do next.
          </p>
        </header>

        <ChatPanel />
      </div>
    </main>
  );
}
