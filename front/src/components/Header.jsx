export default function Header({ compareMode, setCompareMode, setCompareArr, setCompareData }) {
  return (
    <div style={{
      height: 52, background: "#161820", borderBottom: "1px solid #2a2d3a",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 20px", flexShrink: 0
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 28, height: 28, background: "linear-gradient(135deg, #6366f1, #8b5cf6)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🏙</div>
        <span style={{ fontWeight: 600, fontSize: 15, color: "#e8e6df" }}>Urban Data Explorer</span>
        <span style={{ fontSize: 11, color: "#6b7280", background: "#1e2030", padding: "2px 8px", borderRadius: 4 }}>Paris · 2021–2025</span>
      </div>
      <button
        onClick={() => { setCompareMode(m => !m); setCompareArr([]); setCompareData(null) }}
        style={{
          background: compareMode ? "#6366f1" : "#1e2030",
          color: compareMode ? "#fff" : "#9ca3af",
          border: `1px solid ${compareMode ? "#6366f1" : "#2a2d3a"}`,
          borderRadius: 8, padding: "6px 14px", fontSize: 12,
          cursor: "pointer", fontWeight: 500, transition: "all .2s"
        }}
      >
        {compareMode ? "✕ Quitter comparaison" : "⇄ Comparer 2 arrondissements"}
      </button>
    </div>
  )
}