import { MatchedProperty } from "@/lib/types";
import { formatINR } from "@/lib/format";

export default function PropertyCard({ match }: { match: MatchedProperty }) {
  const p = match.property;
  const amenities = (p.amenities || "")
    .split(",")
    .map((a) => a.trim())
    .filter(Boolean)
    .slice(0, 4);

  return (
    <div className="w-full max-w-md border border-ink/10 bg-white/70 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium text-sage">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-sage" />
          {match.match_score}% match
        </div>
        <span className="text-lg leading-none">{p.image_emoji || "🏢"}</span>
      </div>

      <h3 className="mt-2 font-display text-xl leading-snug text-ink">{p.name}</h3>
      <p className="text-sm text-slate">
        {p.location} · {p.builder}
      </p>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <span className="font-display text-2xl text-ink">{formatINR(p.price)}</span>
        <span className="text-sm text-slate">
          {p.bedrooms > 0 ? `${p.bedrooms} BHK · ` : ""}
          {p.area_sqft.toLocaleString("en-IN")} sq.ft.
        </span>
      </div>

      {p.possession_date && (
        <p className="mt-1 text-xs text-slate">{p.possession_date}</p>
      )}

      {amenities.length > 0 && (
        <p className="mt-2 text-xs text-slate">{amenities.join(" · ")}</p>
      )}

      {match.match_reasons.length > 0 && (
        <div className="mt-4 border-t border-ink/10 pt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate">
            Why it matches
          </p>
          <ul className="mt-1.5 space-y-1">
            {match.match_reasons.map((reason, i) => (
              <li key={i} className="flex items-start gap-1.5 text-sm text-ink/80">
                <span className="mt-0.5 text-sage">✓</span>
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
