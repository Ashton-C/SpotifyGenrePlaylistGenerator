import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { LiveMatch as LiveMatchType } from "../api/client";
import { heroName } from "../utils/heroes";

interface Props {
  accountId: number;
}

export default function LiveMatch({ accountId }: Props) {
  const { data, isError } = useQuery<LiveMatchType>({
    queryKey: ["live", accountId],
    queryFn: () => api.liveMatch(accountId),
    retry: false,
    refetchInterval: 60_000,
  });

  if (isError || !data) return null;

  const duration = data.duration_s ?? 0;
  const mins = Math.floor(duration / 60);
  const secs = String(duration % 60).padStart(2, "0");

  return (
    <div
      style={{
        background: "linear-gradient(90deg, #1a3a1a, #1a2a1a)",
        border: "1px solid #22c55e",
        borderRadius: 10,
        padding: "14px 20px",
        marginBottom: 24,
        display: "flex",
        alignItems: "center",
        gap: 12,
      }}
    >
      <span style={{ color: "#22c55e", fontWeight: 700, fontSize: 14 }}>LIVE</span>
      <span style={{ color: "#e0e0e0" }}>
        Currently in a match
        {data.hero_id ? ` as ${heroName(data.hero_id)}` : ""}
        {duration ? ` — ${mins}:${secs}` : ""}
      </span>
      <span style={{ marginLeft: "auto", color: "#aaa", fontSize: 13 }}>Match #{data.match_id}</span>
    </div>
  );
}
