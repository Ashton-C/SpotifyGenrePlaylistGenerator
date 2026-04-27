import { useQuery } from "@tanstack/react-query";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { api } from "../api/client";
import type { RankPoint } from "../api/client";

interface Props {
  accountId: number;
}

export default function RankChart({ accountId }: Props) {
  const { data, isLoading, isError } = useQuery<RankPoint[]>({
    queryKey: ["rank-history", accountId],
    queryFn: () => api.rankHistory(accountId),
  });

  if (isLoading) return <p style={{ color: "#aaa" }}>Loading rank history...</p>;
  if (isError || !data?.length) return <p style={{ color: "#888" }}>No rank history available.</p>;

  const points = Array.isArray(data) ? data : [];
  const chartData = points.map((p, i) => ({
    game: i + 1,
    mmr: p.player_score,
  }));

  const min = Math.min(...chartData.map((d) => d.mmr));
  const max = Math.max(...chartData.map((d) => d.mmr));
  const current = chartData[chartData.length - 1]?.mmr;

  return (
    <div>
      <div style={{ marginBottom: 12, color: "#e84393", fontSize: 18, fontWeight: 700 }}>
        {current} MMR
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />
          <XAxis dataKey="game" tick={{ fill: "#666", fontSize: 11 }} label={{ value: "Game", position: "insideBottom", fill: "#555", fontSize: 12 }} />
          <YAxis domain={[min - 50, max + 50]} tick={{ fill: "#666", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#1a1a2e", border: "1px solid #444", borderRadius: 6 }}
            labelStyle={{ color: "#888" }}
            itemStyle={{ color: "#e84393" }}
            formatter={(v) => [`${Number(v).toFixed(1)} MMR`, ""]}
          />
          <Line type="monotone" dataKey="mmr" stroke="#e84393" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
