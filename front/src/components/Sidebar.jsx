import { useState, useEffect } from "react"
import axios from "axios"
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts"

const INDICATEURS = [
  { value: "prix_m2_median",       label: "Prix au m²",           unit: "€/m²" },
  { value: "loyer_ref_median",     label: "Loyer de référence",   unit: "€/m²" },
  { value: "revenu_median",        label: "Revenu médian",        unit: "€/an" },
  { value: "taux_pauvrete",        label: "Taux de pauvreté",     unit: "%" },
  { value: "score_iau",            label: "Score Attractivité",   unit: "/100" },
  { value: "score_iqv",            label: "Score Qualité de Vie", unit: "/100" },
  { value: "score_imm",            label: "Score Mobilité",       unit: "/100" },
  { value: "score_ist",            label: "Score Tranquillité",   unit: "/100" },
]

export default function Sidebar({ arrondissements, selected, indicateur, setIndicateur, API }) {
  const [detail, setDetail] = useState(null)
  const [evolution, setEvolution] = useState([])

  useEffect(() => {
    if (!selected) return
    axios.get(`${API}/api/arrondissements/${selected}`).then(r => setDetail(r.data))
    axios.get(`${API}/api/prix/evolution?arrondissement=${selected}`).then(r => {
      const agg = {}
      r.data.data.forEach(d => {
        if (!agg[d.annee]) agg[d.annee] = { annee: d.annee, prix: 0, n: 0 }
        agg[d.annee].prix += d.prix_m2_median * d.nb_transactions
        agg[d.annee].n += d.nb_transactions
      })
      setEvolution(Object.values(agg).map(d => ({ annee: d.annee, prix: Math.round(d.prix / d.n) })).sort((a, b) => a.annee - b.annee))
    })
  }, [selected])

  const fmt = (v, unit) => {
    if (v == null) return "—"
    if (unit === "€/m²" || unit === "€/an") return `${Number(v).toLocaleString("fr-FR")} ${unit}`
    if (unit === "%") return `${v} %`
    return `${v} ${unit}`
  }

  return (
    <div style={{ padding: 16 }}>
      {/* Sélecteur indicateur */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 8 }}>Indicateur carte</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {INDICATEURS.map(ind => (
            <button key={ind.value} onClick={() => setIndicateur(ind.value)}
              style={{
                background: indicateur === ind.value ? "#1e2030" : "transparent",
                border: `1px solid ${indicateur === ind.value ? "#6366f1" : "transparent"}`,
                borderRadius: 6, padding: "6px 10px", cursor: "pointer",
                display: "flex", justifyContent: "space-between", alignItems: "center",
                color: indicateur === ind.value ? "#e8e6df" : "#6b7280",
                fontSize: 12, transition: "all .15s"
              }}>
              <span>{ind.label}</span>
              <span style={{ fontSize: 10, color: "#4b5563" }}>{ind.unit}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Détail arrondissement sélectionné */}
      {detail && (
        <div>
          <div style={{ borderTop: "1px solid #2a2d3a", paddingTop: 16, marginBottom: 12 }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: "#e8e6df" }}>
              {detail.arrondissement}e arrondissement
            </div>
            <div style={{ fontSize: 11, color: "#6b7280" }}>{detail.nom_arrondissement}</div>
          </div>

          {/* KPIs principaux */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
            {[
              { label: "Prix médian", value: detail.prix_m2_median, unit: "€/m²" },
              { label: "Loyer réf.", value: detail.loyer_ref_median, unit: "€/m²" },
              { label: "Revenu médian", value: detail.revenu_median, unit: "€/an" },
              { label: "Taux pauvreté", value: detail.taux_pauvrete, unit: "%" },
            ].map(kpi => (
              <div key={kpi.label} style={{ background: "#1e2030", borderRadius: 8, padding: "10px 12px" }}>
                <div style={{ fontSize: 10, color: "#6b7280", marginBottom: 4 }}>{kpi.label}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "#e8e6df" }}>{fmt(kpi.value, kpi.unit)}</div>
              </div>
            ))}
          </div>

          {/* Scores */}
          <div style={{ background: "#1e2030", borderRadius: 8, padding: 12, marginBottom: 16 }}>
            <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 10 }}>Scores indicateurs</div>
            {[
              { label: "Attractivité (IAU)", value: detail.score_iau, color: "#22c55e" },
              { label: "Qualité de vie (IQV)", value: detail.score_iqv, color: "#3b82f6" },
              { label: "Mobilité (IMM)", value: detail.score_imm, color: "#f59e0b" },
              { label: "Tranquillité (IST)", value: detail.score_ist, color: "#8b5cf6" },
            ].map(s => (
              <div key={s.label} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                  <span style={{ color: "#9ca3af" }}>{s.label}</span>
                  <span style={{ color: s.color, fontWeight: 600 }}>{s.value}</span>
                </div>
                <div style={{ height: 4, background: "#2a2d3a", borderRadius: 2 }}>
                  <div style={{ height: "100%", width: `${s.value}%`, background: s.color, borderRadius: 2, transition: "width .5s" }} />
                </div>
              </div>
            ))}
          </div>

          {/* Evolution prix */}
          {evolution.length > 0 && (
            <div style={{ background: "#1e2030", borderRadius: 8, padding: 12 }}>
              <div style={{ fontSize: 10, fontWeight: 500, letterSpacing: ".08em", textTransform: "uppercase", color: "#6b7280", marginBottom: 10 }}>Évolution prix au m²</div>
              <ResponsiveContainer width="100%" height={120}>
                <LineChart data={evolution}>
                  <XAxis dataKey="annee" tick={{ fontSize: 10, fill: "#6b7280" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#6b7280" }} axisLine={false} tickLine={false} width={45} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ background: "#0f1117", border: "1px solid #2a2d3a", borderRadius: 6, fontSize: 12 }}
                    formatter={v => [`${v.toLocaleString("fr-FR")} €/m²`]}
                  />
                  <Line type="monotone" dataKey="prix" stroke="#6366f1" strokeWidth={2} dot={{ fill: "#6366f1", r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {!selected && (
        <div style={{ textAlign: "center", color: "#4b5563", fontSize: 12, marginTop: 40, lineHeight: 1.6 }}>
          Cliquez sur un arrondissement<br />pour voir ses indicateurs
        </div>
      )}
    </div>
  )
}