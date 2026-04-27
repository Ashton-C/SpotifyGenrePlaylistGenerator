// Hero ID → name mapping sourced from deadlock-api /v1/info/heroes
// This list will grow as Valve adds heroes; fill in from API at runtime if needed.
const HERO_NAMES: Record<number, string> = {
  1: "Infernus",
  2: "Seven",
  3: "Vindicta",
  4: "Lady Geist",
  6: "Abrams",
  7: "Wraith",
  8: "McGinnis",
  10: "Paradox",
  11: "Dynamo",
  12: "Kelvin",
  13: "Haze",
  14: "Holliday",
  15: "Bebop",
  16: "Grey Talon",
  17: "Mo & Krill",
  18: "Shiv",
  19: "Ivy",
  20: "Warden",
  25: "Lash",
  27: "Viscous",
  31: "Yamato",
  35: "Mirage",
  50: "Calico",
  52: "Sinclair",
  53: "Wrecker",
  54: "Fathom",
  55: "Viper",
  58: "Tokamak",
  59: "Pocket",
};

export function heroName(id: number): string {
  return HERO_NAMES[id] ?? `Hero #${id}`;
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export function timeAgo(unixTs: number): string {
  const diff = Math.floor(Date.now() / 1000) - unixTs;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
