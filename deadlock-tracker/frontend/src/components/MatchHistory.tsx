import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../api/client";
import type { Match } from "../api/client";
import { heroName, formatDuration, timeAgo } from "../utils/heroes";

interface Props {
  accountId: number;
}

const PAGE_SIZE = 20;

export default function MatchHistory({ accountId }: Props) {
  const [offset, setOffset] = useState(0);

  const { data, isLoading, isError } = useQuery<Match[]>({
    queryKey: ["matches", accountId, offset],
    queryFn: () => api.matches(accountId, PAGE_SIZE, offset),
  });

  if (isLoading) return <p style={{ color: "#aaa" }}>Loading matches...</p>;
  if (isError) return <p style={{ color: "#f87171" }}>Failed to load matches.</p>;

  const matches = Array.isArray(data) ? data : [];

  return (
    <div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid #333", color: "#888", fontSize: 13 }}>
            <th style={th}>Result</th>
            <th style={th}>Hero</th>
            <th style={th}>KDA</th>
            <th style={th}>Duration</th>
            <th style={th}>Net Worth</th>
            <th style={th}>Level</th>
            <th style={th}>When</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((m) => {
            const won = m.match_result === m.player_team;
            return (
              <tr key={m.match_id} style={{ borderBottom: "1px solid #222" }}>
                <td style={{ ...td, color: won ? "#22c55e" : "#f87171", fontWeight: 700 }}>
                  {won ? "W" : "L"}
                </td>
                <td style={td}>{heroName(m.hero_id)}</td>
                <td style={td}>
                  {m.player_kills}/{m.player_deaths}/{m.player_assists}
                </td>
                <td style={td}>{formatDuration(m.match_duration_s)}</td>
                <td style={td}>{m.net_worth ? `${(m.net_worth / 1000).toFixed(1)}k` : "—"}</td>
                <td style={td}>{m.hero_level ? `Lvl ${m.hero_level}` : "—"}</td>
                <td style={{ ...td, color: "#888" }}>{timeAgo(m.start_time)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <button
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
          disabled={offset === 0}
          style={btn}
        >
          Previous
        </button>
        <button
          onClick={() => setOffset(offset + PAGE_SIZE)}
          disabled={matches.length < PAGE_SIZE}
          style={btn}
        >
          Next
        </button>
      </div>
    </div>
  );
}

const th: React.CSSProperties = { textAlign: "left", padding: "8px 12px", fontWeight: 500 };
const td: React.CSSProperties = { padding: "10px 12px", color: "#e0e0e0", fontSize: 14 };
const btn: React.CSSProperties = {
  padding: "7px 18px",
  borderRadius: 6,
  border: "1px solid #444",
  background: "#1e1e2e",
  color: "#ccc",
  cursor: "pointer",
};
