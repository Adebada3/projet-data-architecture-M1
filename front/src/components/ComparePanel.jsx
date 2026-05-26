import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts"

export default function ComparePanel({ compareArr, compareData, arrondissements }) {
  if (compareArr.length < 2 || !compareData) {
    return (
      <div style={{ padding: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 12 }}>Mode comparaison</div>
        <div style={{ color: "#4b5563", fontSize: 12, lineHeight: 1.8 }}>
          Sélectionnez <strong style={{ color: "#9ca3af" }}>2 arrondissements</strong> sur la carte
          {compareArr.length === 1 && <><br /><span style={{ color: "#6366f1" }}>1er sélectionné : {compareArr[0]}e ✓</span><br />Sélectionnez le 2e</>}
        </div>
      </div>
    )
  }

  const a1 = compareData.arrondissement_1
  const a2 = compareData.arrondissement_2

  const radarData = [
    { subject: "Attractivité", A: a1.score_iau, B: a2.score_iau },
    { subject: "Qualité vie", A: a1.score_iqv, B: a2.score_iqv },
    { subject: "Mobilité",    A: a1.score_imm, B: a2.score_imm },
    { subject: "Tranquillité",A: a1.score_ist, B: a2.score_ist },
  ]

  const fmt = (v, unit = "") => v != null ? `${Number(v).toLocaleString("fr-FR")} ${unit}`.trim() : "—"

  const Row = ({ label, v1, v2, unit = "", better = "high" }) => {
    const winner = better === "high" ? (v1 > v2 ? 1 : v1 < v2 ? 2 : 0) : (v1 < v2 ? 1 : v1 > v2 ? 2 : 0)
    return (
      <tr>
        <td style={{ padding: "5px 0", fontSize: 11, color: "#9ca3af", width: "40%" }}>{label}</td>
        <td style={{ textAlign: "right", fontSize: 11, fontWeight: winner === 1 ? 600 : 400, color: winner === 1 ? "#22c55e" : "#e8e6df", padding: "5px 6px" }}>{fmt(v1, unit)}</td>
        <td style={{ textAlign: "right", fontSize: 11, fontWeight: winner === 2 ? 600 : 400, color: winner === 2 ? "#22c55e" : "#e8e6df", padding: "5px 0" }}>{fmt(v2, unit)}</td>
      </tr>
    )
  }

  return (
    <div style={{ padding: 16 }}>
      <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 12 }}>Comparaison</div>

      {/* Headers */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
        {[a1, a2].map((a, i) => (
          <div key={i} style={{ background: "#1e2030", borderRadius: 8, padding: "10px 12px", borderTop: `2px solid ${i === 0 ? "#6366f1" : "#f59e0b"}` }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: i === 0 ? "#6366f1" : "#f59e0b" }}>{a.arrondissement}e</div>
            <div style={{ fontSize: 10, color: "#6b7280" }}>{a.nom_arrondissement}</div>
          </div>
        ))}
      </div>

      {/* Radar */}
      <div style={{ background: "#1e2030", borderRadius: 8, padding: 12, marginBottom: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 8 }}>Scores radar</div>
        <ResponsiveContainer width="100%" height={180}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#2a2d3a" />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: "#6b7280" }} />
            <Radar name={`${a1.arrondissement}e`} dataKey="A" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
            <Radar name={`${a2.arrondissement}e`} dataKey="B" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
            <Tooltip contentStyle={{ background: "#0f1117", border: "1px solid #2a2d3a", fontSize: 11 }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Table comparaison */}
      <div style={{ background: "#1e2030", borderRadius: 8, padding: 12 }}>
        <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 8 }}>Détail indicateurs</div>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ fontSize: 10, color: "#4b5563", textAlign: "left", paddingBottom: 6 }}></th>
              <th style={{ fontSize: 11, color: "#6366f1", textAlign: "right", paddingBottom: 6, paddingRight: 6 }}>{a1.arrondissement}e</th>
              <th style={{ fontSize: 11, color: "#f59e0b", textAlign: "right", paddingBottom: 6 }}>{a2.arrondissement}e</th>
            </tr>
          </thead>
          <tbody>
            <Row label="Prix médian" v1={a1.prix_m2_median} v2={a2.prix_m2_median} unit="€/m²" better="low" />
            <Row label="Loyer réf." v1={a1.loyer_ref_median} v2={a2.loyer_ref_median} unit="€/m²" better="low" />
            <Row label="Revenu médian" v1={a1.revenu_median} v2={a2.revenu_median} unit="€/an" better="high" />
            <Row label="Taux pauvreté" v1={a1.taux_pauvrete} v2={a2.taux_pauvrete} unit="%" better="low" />
            <Row label="Log. sociaux" v1={a1.nb_logements_sociaux} v2={a2.nb_logements_sociaux} better="high" />
            <Row label="Score IAU" v1={a1.score_iau} v2={a2.score_iau} better="high" />
            <Row label="Score IQV" v1={a1.score_iqv} v2={a2.score_iqv} better="high" />
            <Row label="Score IMM" v1={a1.score_imm} v2={a2.score_imm} better="high" />
            <Row label="Commerces" v1={a1.nb_commerces} v2={a2.nb_commerces} better="high" />
            <Row label="Stations transport" v1={a1.nb_stations_transport} v2={a2.nb_stations_transport} better="high" />
            <Row label="Surface verte" v1={a1.surface_verte_m2} v2={a2.surface_verte_m2} unit="m²" better="high" />
          </tbody>
        </table>
      </div>
    </div>
  )
}