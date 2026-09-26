import { ChatMessage } from "@/lib/types";
import PropertyCard from "./PropertyCard";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`msg-enter flex flex-col ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[85%] bg-ink px-4 py-2.5 text-[15px] leading-relaxed text-paper"
            : "max-w-[85%] bg-white/80 px-4 py-2.5 text-[15px] leading-relaxed text-ink border border-ink/10"
        }
      >
        {message.content}
      </div>

      {!isUser && message.properties && message.properties.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-4">
          {message.properties.map((m) => (
            <PropertyCard key={m.property.id} match={m} />
          ))}
        </div>
      )}
    </div>
  );
}
