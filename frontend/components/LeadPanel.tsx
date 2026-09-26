import { LeadQualification } from "@/lib/types";

function intentColor(intent: string) {
  if (intent === "High") return "text-sage";
  if (intent === "Low") return "text-clay";
  return "text-brass";
}

export default function LeadPanel({ lead }: { lead: LeadQualification | null }) {
  if (!lead) {
    return (
      <div className="border border-ink/10 bg-white/60 p-5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate">
          Lead intelligence
        </p>
        <p className="mt-2 text-sm text-slate">
          Tell the assistant what you&apos;re looking for — budget, location,
          and timeline — and a lead score will build up here as you chat.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-ink/10 bg-white/60 p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-slate">
        Lead intelligence
      </p>

      <div className="mt-3 flex items-end justify-between">
        <span className="font-display text-4xl text-ink">{lead.score}</span>
        <span className="pb-1 text-sm text-slate">/ 100</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-ink/10">
        <div
          className="h-full rounded-full bg-brass transition-all duration-500"
          style={{ width: `${lead.score}%` }}
        />
      </div>

      <div className="mt-4 flex items-center justify-between text-sm">
        <span className="text-slate">Intent</span>
        <span className={`font-medium ${intentColor(lead.intent)}`}>{lead.intent}</span>
      </div>

      <div className="mt-3 border-t border-ink/10 pt-3">
        <p className="text-xs font-medium uppercase tracking-wide text-slate">
          Factors considered
        </p>
        <ul className="mt-1.5 space-y-1">
          {lead.factors.map((f, i) => (
            <li key={i} className="text-sm text-ink/80">
              · {f}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4 border-t border-ink/10 pt-3">
        <p className="text-xs font-medium uppercase tracking-wide text-slate">
          Recommended next step
        </p>
        <p className="mt-1 font-display text-lg text-ink">{lead.next_action}</p>
      </div>
    </div>
  );
}
