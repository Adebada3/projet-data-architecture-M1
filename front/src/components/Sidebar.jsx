import { useState, useEffect } from "react"
import axios from "axios"
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer
} from "recharts"

const INDICATEURS = [
  {
    value: "prix_m2_median", label: "Prix au m²", unit: "€/m²", icon: "🏠", hasTime: true,
    description: "Prix médian des transactions immobilières (appartements et maisons) par arrondissement.",
    formule: null, sources: null,
    detailKeys: ["prix_m2_median", "evol_prix_2021_2024_pct", "nb_transactions", "surface_median"],
    detailLabels: ["Prix médian", "Évolution 2021-2025", "Nb transactions", "Surface médiane"],
    detailUnits: ["€/m²", "%", "", "m²"]
  },
  {
    value: "loyer_ref_median", label: "Loyer de référence", unit: "€/m²", icon: "📋", hasTime: true,
    description: "Loyer de référence légal par m² défini par la réglementation d'encadrement des loyers.",
    formule: null, sources: null,
    detailKeys: ["loyer_ref_median", "loyer_max_median"],
    detailLabels: ["Loyer référence", "Loyer majoré max"],
    detailUnits: ["€/m²", "€/m²"]
  },
  {
    value: "revenu_median", label: "Revenu médian", unit: "€/an", icon: "💶", hasTime: false,
    description: "Revenu médian annuel des habitants par zone IRIS (INSEE Filosofi 2021).",
    formule: null, sources: null,
    detailKeys: ["revenu_median", "taux_pauvrete", "indice_gini"],
    detailLabels: ["Revenu médian", "Taux de pauvreté", "Indice Gini"],
    detailUnits: ["€/an", "%", ""]
  },
  {
    value: "taux_pauvrete", label: "Taux de pauvreté", unit: "%", icon: "📊", hasTime: false,
    description: "Part de la population vivant sous le seuil de pauvreté (60% du revenu médian national).",
    formule: null, sources: null,
    detailKeys: ["taux_pauvrete", "revenu_median", "nb_logements_sociaux"],
    detailLabels: ["Taux pauvreté", "Revenu médian", "Logements sociaux"],
    detailUnits: ["%", "€/an", ""]
  },
  {
    value: "score_iau", label: "Score Attractivité (IAU)", unit: "/100", icon: "⭐", hasTime: false,
    description: "Indice d'Attractivité Urbaine : mesure l'animation et la richesse de services d'un arrondissement.",
    formule: "IAU = Commerces×25% + Restaurants/Bars×20% + Établissements scolaires×25% + Santé×20% + Monuments historiques×10%",
    sources: [
      { nom: "BPE", poids: "70%", label: "Commerces + Santé + Scolaire" },
      { nom: "OSM", poids: "20%", label: "Restaurants & bars" },
      { nom: "Min. Culture", poids: "10%", label: "Monuments protégés" },
    ],
    detailKeys: ["score_iau", "nb_commerces", "nb_restos_bars", "nb_scolaire", "nb_sante", "nb_monuments"],
    detailLabels: ["Score IAU", "Commerces", "Restos & bars", "Établissements scolaires", "Établissements santé", "Monuments historiques"],
    detailUnits: ["/100", "", "", "", "", ""]
  },
  {
    value: "score_iqv", label: "Score Qualité de Vie (IQV)", unit: "/100", icon: "🌿", hasTime: false,
    description: "Indice de Qualité de Vie Verte : mesure la présence de nature et l'accès aux soins.",
    formule: "IQV = Surface espaces verts×40% + Nombre d'arbres×30% + Professionnels de santé×30%",
    sources: [
      { poids: "40%", label: "Surface verte (m²)" },
      { poids: "30%", label: "Arbres sur voie publique" },
      { poids: "30%", label: "Médecins & spécialistes" },
    ],
    detailKeys: ["score_iqv", "surface_verte_m2", "nb_arbres", "nb_espaces_verts", "nb_pros_sante"],
    detailLabels: ["Score IQV", "Surface verte", "Nb arbres", "Nb espaces verts", "Pros de santé"],
    detailUnits: ["/100", "m²", "", "", ""]
  },
  {
    value: "score_imm", label: "Score Mobilité (IMM)", unit: "/100", icon: "🚇", hasTime: false,
    description: "Indice de Mobilité Multimodale : mesure la facilité à se déplacer sans voiture.",
    formule: "IMM = Stations transport×40% + Capacité Vélib'×30% + Tronçons cyclables×30%",
    sources: [
      { poids: "40%", label: "Stations métro/RER/tram" },
      { poids: "30%", label: "Capacité stations Vélib'" },
      { poids: "30%", label: "Tronçons de pistes cyclables" },
    ],
    detailKeys: ["score_imm", "nb_stations_transport", "nb_stations_velib", "capacite_velib", "nb_troncons_velo"],
    detailLabels: ["Score IMM", "Stations transport", "Stations Vélib'", "Capacité Vélib'", "Tronçons vélo"],
    detailUnits: ["/100", "", "", "vélos", ""]
  },
  {
    value: "score_ist", label: "Score Tranquillité (IST)", unit: "/100", icon: "🛡", hasTime: false,
    description: "Indice de Sécurité & Tranquillité : basé sur les revenus et le taux de pauvreté.",
    formule: "IST = (100 - Taux pauvreté normalisé)×50% + Revenu médian normalisé×50%",
    sources: [
      { poids: "50%", label: "Revenu médian (€/an)" },
      { poids: "50%", label: "Taux de pauvreté (%)" },
    ],
    detailKeys: ["score_ist", "revenu_median", "taux_pauvrete", "indice_gini"],
    detailLabels: ["Score IST", "Revenu médian", "Taux pauvreté", "Indice Gini"],
    detailUnits: ["/100", "€/an", "%", ""]
  },
  {
    value: "nb_logements_sociaux", label: "Logements sociaux", unit: "", icon: "🏢", hasTime: false,
    description: "Nombre total de logements sociaux financés (HLM, PLUS, PLS, PLAI) depuis 2001.",
    formule: null, sources: null,
    detailKeys: ["nb_logements_sociaux", "nb_programmes"],
    detailLabels: ["Logements sociaux", "Programmes financés"],
    detailUnits: ["", ""]
  },
]

const SCORE_COLORS = {
  prix_m2_median:       { lowLabel: "Moins cher",      highLabel: "Plus cher" },
  loyer_ref_median:     { lowLabel: "Loyer bas",        highLabel: "Loyer élevé" },
  revenu_median:        { lowLabel: "Revenus bas",      highLabel: "Revenus élevés" },
  taux_pauvrete:        { lowLabel: "Faible pauvreté",  highLabel: "Forte pauvreté" },
  score_iau:            { lowLabel: "Peu attractif",    highLabel: "Très attractif" },
  score_iqv:            { lowLabel: "Peu vert",         highLabel: "Très vert" },
  score_imm:            { lowLabel: "Peu accessible",   highLabel: "Très accessible" },
  score_ist:            { lowLabel: "Moins tranquille", highLabel: "Très tranquille" },
  nb_logements_sociaux: { lowLabel: "Peu de HLM",       highLabel: "Beaucoup de HLM" },
}

const SCORE_COLOR_BARS = {
  prix_m2_median:       ["#fef9c3","#fde68a","#fbbf24","#f59e0b","#d97706","#b45309","#78350f"],
  loyer_ref_median:     ["#fef9c3","#fde68a","#fbbf24","#f59e0b","#d97706","#b45309","#78350f"],
  revenu_median:        ["#fef9c3","#fde68a","#fbbf24","#f59e0b","#d97706","#b45309","#78350f"],
  taux_pauvrete:        ["#f0fdf4","#bbf7d0","#fde68a","#fbbf24","#f97316","#ef4444","#991b1b"],
  score_iau:            ["#f0fdf4","#bbf7d0","#86efac","#4ade80","#22c55e","#16a34a","#14532d"],
  score_iqv:            ["#f0fdf4","#bbf7d0","#86efac","#4ade80","#22c55e","#16a34a","#14532d"],
  score_imm:            ["#eff6ff","#bfdbfe","#93c5fd","#60a5fa","#3b82f6","#2563eb","#1d4ed8"],
  score_ist:            ["#fdf4ff","#f5d0fe","#e879f9","#d946ef","#a21caf","#86198f","#701a75"],
  nb_logements_sociaux: ["#f0fdf4","#bbf7d0","#86efac","#4ade80","#22c55e","#16a34a","#14532d"],
}

export default function Sidebar({ arrondissements, selected, indicateur, setIndicateur, API }) {
  const [detail, setDetail]           = useState(null)
  const [detailAnnee, setDetailAnnee] = useState(null)   // ← MANQUAIT !
  const [evolution, setEvolution]     = useState([])
  const [loyersData, setLoyersData]   = useState([])
  const [showInfo, setShowInfo]       = useState(null)
  const [annee, setAnnee]             = useState("all")

  const indConfig = INDICATEURS.find(i => i.value === indicateur)

  // Chargement quand arrondissement change
  useEffect(() => {
    if (!selected) return
    setDetailAnnee(null)
    setAnnee("all")

    axios.get(`${API}/api/arrondissements/${selected}`)
      .then(r => setDetail(r.data))

    axios.get(`${API}/api/prix/evolution?arrondissement=${selected}`)
      .then(r => {
        const agg = {}
        r.data.data.forEach(d => {
          if (!agg[d.annee]) agg[d.annee] = { annee: d.annee, prix: 0, n: 0 }
          agg[d.annee].prix += d.prix_m2_median * d.nb_transactions
          agg[d.annee].n    += d.nb_transactions
        })
        setEvolution(
          Object.values(agg)
            .map(d => ({ annee: d.annee, prix: Math.round(d.prix / d.n) }))
            .sort((a, b) => a.annee - b.annee)
        )
      })

    axios.get(`${API}/api/loyers?arrondissement=${selected}`)
      .then(r => {
        const agg = {}
        r.data.data.forEach(d => {
          if (!agg[d.annee]) agg[d.annee] = { annee: d.annee, loyer: 0, n: 0 }
          agg[d.annee].loyer += d.loyer_ref_moyen
          agg[d.annee].n++
        })
        setLoyersData(
          Object.values(agg)
            .map(d => ({ annee: d.annee, loyer: Math.round(d.loyer * 10) / 10 }))
            .sort((a, b) => a.annee - b.annee)
        )
      })
  }, [selected])

  // Quand l'année change → recharger les données filtrées
  useEffect(() => {
    if (!selected || !indConfig?.hasTime) return

    if (annee === "all") {
      setDetailAnnee(null)
      return
    }

    if (indicateur === "prix_m2_median") {
      axios.get(`${API}/api/prix?arrondissement=${selected}&annee=${annee}`)
        .then(r => {
          // L'API retourne plusieurs lignes (par type_local) → on agrège
          const rows = r.data.data
          if (!rows || rows.length === 0) { setDetailAnnee(null); return }
          // On prend les Appartements en priorité, sinon on agrège tout
          const appts = rows.filter(row => row.type_local === "Appartement")
          const source = appts.length > 0 ? appts[0] : rows[0]
          setDetailAnnee({
            prix_m2_median:  source.prix_m2_median,
            nb_transactions: rows.reduce((acc, row) => acc + Number(row.nb_transactions || 0), 0),
          })
        })
    }

    if (indicateur === "loyer_ref_median") {
      axios.get(`${API}/api/loyers?arrondissement=${selected}&annee=${annee}`)
        .then(r => {
          const rows = r.data.data
          if (!rows || rows.length === 0) { setDetailAnnee(null); return }
          const avg = rows.reduce((acc, row) => acc + Number(row.loyer_ref_moyen || 0), 0) / rows.length
          setDetailAnnee({
            loyer_ref_median: Math.round(avg * 10) / 10,
          })
        })
    }
  }, [selected, annee, indicateur])

  const fmt = (v, unit) => {
    if (v == null || v === "") return "—"
    if (unit === "€/m²" || unit === "€/an")
      return `${Number(v).toLocaleString("fr-FR")} ${unit}`
    if (unit === "%")    return `${Number(v).toFixed(1)} %`
    if (unit === "/100") return `${Number(v).toFixed(1)} / 100`
    if (unit === "m²")   return `${Number(v).toLocaleString("fr-FR")} m²`
    return `${Number(v).toLocaleString("fr-FR")}${unit ? " " + unit : ""}`
  }

  const getDisplayValue = (key, i) => {
    if (annee !== "all" && detailAnnee?.[key] !== undefined) return detailAnnee[key]
    return detail?.[key]
  }

  const allValues = arrondissements.map(a => a[indicateur]).filter(v => v != null)
  const minVal    = allValues.length ? Math.min(...allValues) : 0
  const maxVal    = allValues.length ? Math.max(...allValues) : 100
  const colors    = SCORE_COLOR_BARS[indicateur] || SCORE_COLOR_BARS.prix_m2_median

  // Données graphique filtrées
  const evolutionFiltered = annee === "all"
    ? evolution
    : evolution.filter(d => d.annee === Number(annee))
  const loyersFiltered = annee === "all"
    ? loyersData
    : loyersData.filter(d => d.annee === Number(annee))

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      height: "100%", background: "#ffffff",
      borderLeft: "1px solid #e2e8f0", overflow: "hidden"
    }}>

      {/* ── Sélecteur indicateur ── */}
      <div style={{ padding: "12px 14px", borderBottom: "1px solid #e2e8f0", flexShrink: 0 }}>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 8 }}>
          Indicateur carte
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {INDICATEURS.map(ind => (
            <div key={ind.value} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <button
                onClick={() => { setIndicateur(ind.value); setAnnee("all"); setDetailAnnee(null) }}
                style={{
                  flex: 1,
                  background: indicateur === ind.value ? "#eff6ff" : "transparent",
                  border: `1px solid ${indicateur === ind.value ? "#3b82f6" : "transparent"}`,
                  borderRadius: 6, padding: "5px 8px", cursor: "pointer",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  color: indicateur === ind.value ? "#1d4ed8" : "#64748b",
                  fontSize: 12, transition: "all .15s"
                }}
              >
                <span>{ind.icon} {ind.label}</span>
                <span style={{ fontSize: 10, color: "#94a3b8" }}>{ind.unit}</span>
              </button>
              <button
                onClick={() => setShowInfo(showInfo === ind.value ? null : ind.value)}
                style={{
                  width: 20, height: 20, borderRadius: "50%",
                  background: showInfo === ind.value ? "#3b82f6" : "#f1f5f9",
                  color: showInfo === ind.value ? "white" : "#94a3b8",
                  border: "none", cursor: "pointer", fontSize: 11, flexShrink: 0,
                  display: "flex", alignItems: "center", justifyContent: "center"
                }}
              >ℹ</button>
            </div>
          ))}
        </div>
      </div>

      {/* ── Popup info indicateur ── */}
      {showInfo && (() => {
        const ind = INDICATEURS.find(i => i.value === showInfo)
        if (!ind) return null
        return (
          <div style={{ margin: "8px 14px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10, padding: 12, flexShrink: 0 }}>
            <div style={{ fontWeight: 600, fontSize: 13, color: "#1e293b", marginBottom: 6 }}>{ind.icon} {ind.label}</div>
            <div style={{ fontSize: 12, color: "#475569", marginBottom: 8, lineHeight: 1.5 }}>{ind.description}</div>
            {ind.formule && (
              <div style={{ background: "#eff6ff", borderRadius: 6, padding: "6px 10px", marginBottom: 8, fontSize: 11, color: "#1d4ed8", fontFamily: "monospace", lineHeight: 1.6 }}>
                {ind.formule}
              </div>
            )}
            {ind.sources && (
              <div>
                <div style={{ fontSize: 10, fontWeight: 600, color: "#94a3b8", marginBottom: 4, textTransform: "uppercase", letterSpacing: ".06em" }}>
                  Sources & pondérations
                </div>
                {ind.sources.map((s, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0", borderBottom: i < ind.sources.length - 1 ? "1px solid #e2e8f0" : "none" }}>
                    <span style={{ fontSize: 11, color: "#475569" }}>{s.label}</span>
                    <span style={{ fontSize: 11, fontWeight: 700, color: "#3b82f6", background: "#eff6ff", padding: "1px 6px", borderRadius: 4 }}>{s.poids}</span>
                  </div>
                ))}
              </div>
            )}
            <button onClick={() => setShowInfo(null)} style={{ marginTop: 8, width: "100%", padding: "4px 0", background: "white", border: "1px solid #e2e8f0", borderRadius: 6, fontSize: 11, color: "#94a3b8", cursor: "pointer" }}>
              Fermer
            </button>
          </div>
        )
      })()}

      {/* ── Légende couleurs ── */}
      <div style={{ padding: "8px 14px", borderBottom: "1px solid #e2e8f0", flexShrink: 0 }}>
        <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 6 }}>
          Échelle de couleurs
        </div>
        <div style={{ display: "flex", height: 12, borderRadius: 6, overflow: "hidden", marginBottom: 4 }}>
          {colors.map((c, i) => <div key={i} style={{ flex: 1, background: c }} />)}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 10, color: "#64748b" }}>
            {SCORE_COLORS[indicateur]?.lowLabel} ({fmt(minVal, indConfig?.unit)})
          </span>
          <span style={{ fontSize: 10, color: "#64748b" }}>
            {SCORE_COLORS[indicateur]?.highLabel} ({fmt(maxVal, indConfig?.unit)})
          </span>
        </div>
      </div>

      {/* ── Filtre temporel ── */}
      {indConfig?.hasTime && (
        <div style={{ padding: "8px 14px", borderBottom: "1px solid #e2e8f0", flexShrink: 0 }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 6 }}>
            Période {annee !== "all" && <span style={{ color: "#3b82f6", marginLeft: 4 }}>— données {annee}</span>}
          </div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {["all", 2021, 2022, 2023, 2024, 2025].map(y => (
              <button
                key={y}
                onClick={() => setAnnee(y)}
                style={{
                  padding: "3px 10px", borderRadius: 20,
                  border: `1px solid ${annee === y ? "#3b82f6" : "#e2e8f0"}`,
                  background: annee === y ? "#3b82f6" : "white",
                  color: annee === y ? "white" : "#64748b",
                  fontSize: 11, cursor: "pointer", fontWeight: annee === y ? 600 : 400
                }}
              >
                {y === "all" ? "Toute la période" : y}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Contenu ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "0 14px 14px" }}>
        {detail ? (
          <>
            <div style={{ padding: "12px 0 8px", borderBottom: "1px solid #e2e8f0", marginBottom: 12 }}>
              <div style={{ fontSize: 18, fontWeight: 700, color: "#1e293b" }}>
                {detail.arrondissement}e arrondissement
              </div>
              <div style={{ fontSize: 12, color: "#94a3b8" }}>{detail.nom_arrondissement}</div>
            </div>

            {/* Détail indicateur sélectionné */}
            {indConfig && (
              <div style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 8 }}>
                  {indConfig.icon} {indConfig.label}
                  {annee !== "all" && <span style={{ color: "#3b82f6", marginLeft: 6, fontWeight: 700 }}>{annee}</span>}
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                  {indConfig.detailKeys.map((key, i) => (
                    <div key={key} style={{
                      background: "#f8fafc", borderRadius: 8, padding: "8px 10px",
                      border: i === 0 ? "1px solid #3b82f6" : "1px solid #e2e8f0",
                      gridColumn: i === 0 ? "1 / -1" : "auto"
                    }}>
                      <div style={{ fontSize: 10, color: "#94a3b8", marginBottom: 3 }}>
                        {indConfig.detailLabels[i]}
                      </div>
                      <div style={{ fontSize: i === 0 ? 18 : 14, fontWeight: 700, color: i === 0 ? "#3b82f6" : "#1e293b" }}>
                        {fmt(getDisplayValue(key, i), indConfig.detailUnits[i])}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tous les scores */}
            <div style={{ background: "#f8fafc", borderRadius: 10, padding: 12, marginBottom: 14, border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 10 }}>
                Tous les scores
              </div>
              {[
                { label: "Attractivité (IAU)", key: "score_iau", color: "#22c55e" },
                { label: "Qualité de vie (IQV)", key: "score_iqv", color: "#3b82f6" },
                { label: "Mobilité (IMM)", key: "score_imm", color: "#f59e0b" },
                { label: "Tranquillité (IST)", key: "score_ist", color: "#8b5cf6" },
              ].map(s => (
                <div key={s.key} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 3 }}>
                    <span style={{ color: "#475569" }}>{s.label}</span>
                    <span style={{ color: s.color, fontWeight: 700 }}>{detail[s.key]?.toFixed(1)}</span>
                  </div>
                  <div style={{ height: 5, background: "#e2e8f0", borderRadius: 3 }}>
                    <div style={{ height: "100%", width: `${detail[s.key] || 0}%`, background: s.color, borderRadius: 3, transition: "width .5s" }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Graphique prix */}
            {indicateur === "prix_m2_median" && evolution.length > 0 && (
              <div style={{ background: "#f8fafc", borderRadius: 10, padding: 12, border: "1px solid #e2e8f0", marginBottom: 14 }}>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 10 }}>
                  Évolution prix au m²
                  {annee !== "all" && <span style={{ color: "#3b82f6", marginLeft: 4 }}>· {annee}</span>}
                </div>
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={evolutionFiltered}>
                    <XAxis dataKey="annee" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={45} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                    <Tooltip contentStyle={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 12 }} formatter={v => [`${v.toLocaleString("fr-FR")} €/m²`]} />
                    <Line type="monotone" dataKey="prix" stroke="#3b82f6" strokeWidth={2} dot={{ fill: "#3b82f6", r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
                {annee !== "all" && evolutionFiltered.length > 0 && (
                  <div style={{ textAlign: "center", fontSize: 13, fontWeight: 700, color: "#3b82f6", marginTop: 6 }}>
                    {evolutionFiltered[0].prix.toLocaleString("fr-FR")} €/m² en {annee}
                  </div>
                )}
              </div>
            )}

            {/* Graphique loyers */}
            {indicateur === "loyer_ref_median" && loyersData.length > 0 && (
              <div style={{ background: "#f8fafc", borderRadius: 10, padding: 12, border: "1px solid #e2e8f0", marginBottom: 14 }}>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: ".08em", textTransform: "uppercase", color: "#94a3b8", marginBottom: 10 }}>
                  Évolution loyers de référence
                  {annee !== "all" && <span style={{ color: "#f59e0b", marginLeft: 4 }}>· {annee}</span>}
                </div>
                <ResponsiveContainer width="100%" height={120}>
                  <LineChart data={loyersFiltered}>
                    <XAxis dataKey="annee" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={40} tickFormatter={v => `${v}€`} />
                    <Tooltip contentStyle={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 12 }} formatter={v => [`${v} €/m²`]} />
                    <Line type="monotone" dataKey="loyer" stroke="#f59e0b" strokeWidth={2} dot={{ fill: "#f59e0b", r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
                {annee !== "all" && loyersFiltered.length > 0 && (
                  <div style={{ textAlign: "center", fontSize: 13, fontWeight: 700, color: "#f59e0b", marginTop: 6 }}>
                    {loyersFiltered[0].loyer} €/m² en {annee}
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div style={{ textAlign: "center", color: "#94a3b8", fontSize: 12, marginTop: 40, lineHeight: 1.8 }}>
            Cliquez sur un arrondissement<br />pour voir ses indicateurs
          </div>
        )}
      </div>
    </div>
  )
}