export function formatINR(amount: number): string {
  if (amount >= 10_000_000) {
    return `₹${(amount / 10_000_000).toFixed(amount % 10_000_000 === 0 ? 0 : 2)} Cr`;
  }
  if (amount >= 100_000) {
    return `₹${(amount / 100_000).toFixed(amount % 100_000 === 0 ? 0 : 1)} Lakh`;
  }
  return `₹${amount.toLocaleString("en-IN")}`;
}
