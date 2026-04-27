import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import MatchHistory from "../components/MatchHistory";
import RankChart from "../components/RankChart";
import HeroStats from "../components/HeroStats";
import LiveMatch from "../components/LiveMatch";

type Tab = "matches" | "rank" | "heroes";

export default function Player() {
  const { accountId } = useParams<{ accountId: string }>();
  const id = Number(accountId);
  const [tab, setTab] = useState<Tab>("matches");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["player", id],
    queryFn: () => api.player(id),
    enabled: !isNaN(id),
  });

  if (isNaN(id)) return <ErrorPage msg="Invalid account ID." />;
  if (isLoading) return <LoadingPage />;
  if (isError) return <ErrorPage msg="Player not found or API unavailable." />;

  const profile = data?.steam_profile;

  return (
    <div style={{ minHeight: "100vh", background: "#0d0d1a", color: "#e0e0e0", padding: "32px 24px", maxWidth: 900, margin: "0 auto" }}>
      <Link to="/" style={{ color: "#666", fontSize: 13, textDecoration: "none" }}>
        ← Back to search
      </Link>

      {/* Player header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 20, marginBottom: 24 }}>
        {profile?.avatarfull && (
          <img
            src={profile.avatarfull}
            alt={profile.personaname}
            style={{ width: 64, height: 64, borderRadius: 8, border: "2px solid #333" }}
          />
        )}
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: "#e84393" }}>
            {profile?.personaname ?? `Player #${id}`}
          </h1>
          <span style={{ color: "#555", fontSize: 13 }}>Account ID: {id}</span>
        </div>
      </div>

      {/* Live match banner */}
      <LiveMatch accountId={id} />

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid #222", marginBottom: 24 }}>
        {(["matches", "rank", "heroes"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "10px 20px",
              background: "none",
              border: "none",
              borderBottom: tab === t ? "2px solid #e84393" : "2px solid transparent",
              color: tab === t ? "#e84393" : "#888",
              fontWeight: tab === t ? 700 : 400,
              cursor: "pointer",
              fontSize: 14,
              textTransform: "capitalize",
            }}
          >
            {t === "rank" ? "Rank History" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "matches" && <MatchHistory accountId={id} />}
      {tab === "rank" && <RankChart accountId={id} />}
      {tab === "heroes" && <HeroStats accountId={id} />}
    </div>
  );
}

function LoadingPage() {
  return (
    <div style={{ minHeight: "100vh", background: "#0d0d1a", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <p style={{ color: "#666" }}>Loading player...</p>
    </div>
  );
}

function ErrorPage({ msg }: { msg: string }) {
  return (
    <div style={{ minHeight: "100vh", background: "#0d0d1a", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12 }}>
      <p style={{ color: "#f87171" }}>{msg}</p>
      <Link to="/" style={{ color: "#e84393" }}>← Back to search</Link>
    </div>
  );
}
