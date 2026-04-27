import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { HeroStat } from "../api/client";
import { heroName } from "../utils/heroes";

interface Props {
  accountId: number;
}

type SortKey = "games" | "win_rate" | "avg_kda" | "avg_kills" | "avg_deaths";

export default function HeroStats({ accountId }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("games");

  const { data, isLoading, isError } = useQuery<HeroStat[]>({
    queryKey: ["heroes", accountId],
    queryFn: () => api.heroStats(accountId),
  });

  if (isLoading) return <p style={{ color: "#aaa" }}>Loading hero stats...</p>;
  if (isError) return <p style={{ color: "#f87171" }}>Failed to load hero stats.</p>;

  const stats = Array.isArray(data) ? [...data].sort((a, b) => (b[sortKey] as number) - (a[sortKey] as number)) : [];

  function SortBtn({ k, label }: { k: SortKey; label: string }) {
    return (
      <th
        style={{ ...th, cursor: "pointer", color: sortKey === k ? "#e84393" : "#888" }}
        onClick={() => setSortKey(k)}
      >
        {label} {sortKey === k ? "↓" : ""}
      </th>
    );
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ borderBottom: "1px solid #333", fontSize: 13 }}>
          <th style={{ ...th, color: "#888" }}>Hero</th>
          <SortBtn k="games" label="Games" />
          <SortBtn k="win_rate" label="Win %" />
          <SortBtn k="avg_kda" label="Avg KDA" />
          <SortBtn k="avg_kills" label="Avg K" />
          <SortBtn k="avg_deaths" label="Avg D" />
        </tr>
      </thead>
      <tbody>
        {stats.map((s) => (
          <tr key={s.hero_id} style={{ borderBottom: "1px solid #222" }}>
            <td style={td}>{heroName(s.hero_id)}</td>
            <td style={td}>{s.games}</td>
            <td style={{ ...td, color: s.win_rate >= 0.5 ? "#22c55e" : "#f87171" }}>
              {(s.win_rate * 100).toFixed(1)}%
            </td>
            <td style={td}>{s.avg_kda}</td>
            <td style={td}>{s.avg_kills}</td>
            <td style={td}>{s.avg_deaths}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", fontWeight: 500 };
const td: React.CSSProperties = { padding: "10px 12px", color: "#e0e0e0", fontSize: 14 };
