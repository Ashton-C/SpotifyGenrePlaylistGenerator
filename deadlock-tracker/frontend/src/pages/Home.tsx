import PlayerSearch from "../components/PlayerSearch";

export default function Home() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0d0d1a",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 32,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <h1 style={{ color: "#e84393", fontSize: 42, fontWeight: 800, margin: 0, letterSpacing: -1 }}>
          Deadlock Tracker
        </h1>
        <p style={{ color: "#666", marginTop: 8 }}>Match history, ranks, and hero stats</p>
      </div>
      <PlayerSearch />
      <p style={{ color: "#444", fontSize: 12, maxWidth: 400, textAlign: "center" }}>
        Enter a Steam64 ID (17 digits), account ID, or Steam vanity URL name.
        Data powered by{" "}
        <a href="https://deadlock-api.com" style={{ color: "#666" }} target="_blank" rel="noreferrer">
          deadlock-api.com
        </a>
      </p>
    </div>
  );
}
