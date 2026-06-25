export default function Header({ compareMode, setCompareMode, setCompareArr, setCompareData }) {
  return (
    <div style={{
      height: 52, background: "#ffffff",
      borderBottom: "1px solid #e2e8f0",
      display: "flex", alignItems: "center",
      justifyContent: "space-between",
      padding: "0 20px", flexShrink: 0,
      boxShadow: "0 1px 3px rgba(0,0,0,0.06)"
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{
          width: 30, height: 30,
          background: "linear-gradient(135deg, #3b82f6, #6366f1)",
          borderRadius: 8, display: "flex",
          alignItems: "center", justifyContent: "center",
          fontSize: 15
        }}>🏙</div>
        <span style={{ fontWeight: 700, fontSize: 15, color: "#1e293b" }}>
          Urban Data Explorer
        </span>
        <span style={{
          fontSize: 11, color: "#64748b",
          background: "#f1f5f9",
          padding: "2px 8px", borderRadius: 4,
          border: "1px solid #e2e8f0"
        }}>Paris · 2021–2025</span>
      </div>
      <button
        onClick={() => {
          setCompareMode(m => !m)
          setCompareArr([])
          setCompareData(null)
        }}
        style={{
          background: compareMode ? "#3b82f6" : "white",
          color: compareMode ? "#fff" : "#64748b",
          border: `1px solid ${compareMode ? "#3b82f6" : "#e2e8f0"}`,
          borderRadius: 8, padding: "6px 14px",
          fontSize: 12, cursor: "pointer",
          fontWeight: 500, transition: "all .2s"
        }}
      >
        {compareMode ? "✕ Quitter comparaison" : "⇄ Comparer 2 arrondissements"}
      </button>
    </div>
  )
}