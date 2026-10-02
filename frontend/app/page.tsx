import ChatPanel from "@/components/ChatPanel";

export default function Home() {
  return (
    <main className="min-h-screen bg-paper">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="font-display text-4xl text-ink sm:text-5xl">
            PropertyPulse
          </h1>
        </header>

        <ChatPanel />
      </div>
    </main>
  );
}
