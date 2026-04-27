import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function PlayerSearch() {
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const result = await api.search(query.trim());
      navigate(`/player/${result.account_id}`);
    } catch {
      setError("Player not found. Try a Steam64 ID, account ID, or vanity URL name.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center" }}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Steam ID, account ID, or vanity URL..."
        style={{
          width: 380,
          padding: "12px 16px",
          fontSize: 16,
          borderRadius: 8,
          border: "1px solid #444",
          background: "#1a1a2e",
          color: "#e0e0e0",
          outline: "none",
        }}
      />
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: "10px 32px",
          fontSize: 15,
          borderRadius: 8,
          border: "none",
          background: "#e84393",
          color: "#fff",
          cursor: loading ? "not-allowed" : "pointer",
          opacity: loading ? 0.7 : 1,
        }}
      >
        {loading ? "Searching..." : "Search"}
      </button>
      {error && <p style={{ color: "#f87171", margin: 0 }}>{error}</p>}
    </form>
  );
}
