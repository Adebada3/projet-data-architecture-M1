import { useEffect, useRef } from "react"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"

const PALETTES = {
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

const INDICATEUR_LABELS = {
  prix_m2_median: { label: "Prix médian", unit: "€/m²" },
  loyer_ref_median: { label: "Loyer référence", unit: "€/m²" },
  revenu_median: { label: "Revenu médian", unit: "€/an" },
  taux_pauvrete: { label: "Taux de pauvreté", unit: "%" },
  score_iau: { label: "Score Attractivité (IAU)", unit: "/100" },
  score_iqv: { label: "Score Qualité de vie (IQV)", unit: "/100" },
  score_imm: { label: "Score Mobilité (IMM)", unit: "/100" },
  score_ist: { label: "Score Tranquillité (IST)", unit: "/100" },
  nb_logements_sociaux: { label: "Logements sociaux", unit: "" },
}

function getColor(value, values, indicateur) {
  const palette = PALETTES[indicateur] || PALETTES.prix_m2_median
  const sorted = [...values].filter(v => v != null).sort((a, b) => a - b)
  const min = sorted[0], max = sorted[sorted.length - 1]
  if (max === min) return palette[3]
  const pct = (value - min) / (max - min)
  const idx = Math.min(Math.floor(pct * palette.length), palette.length - 1)
  return palette[idx]
}

const ARR_CENTERS = {
  1:[2.3470,48.8603], 2:[2.3467,48.8669], 3:[2.3561,48.8633],
  4:[2.3526,48.8543], 5:[2.3474,48.8462], 6:[2.3346,48.8492],
  7:[2.3136,48.8560], 8:[2.3100,48.8746], 9:[2.3389,48.8770],
  10:[2.3596,48.8770], 11:[2.3790,48.8590], 12:[2.4122,48.8407],
  13:[2.3608,48.8275], 14:[2.3266,48.8277], 15:[2.2930,48.8415],
  16:[2.2680,48.8637], 17:[2.3095,48.8843], 18:[2.3488,48.8924],
  19:[2.3893,48.8836], 20:[2.3990,48.8654],
}

export default function Map({ geoData, indicateur, onArrClick, selected, compareArr, compareMode }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const markersRef = useRef([])
  const popupRef = useRef(null)
  const geoDataRef = useRef(null)
  const indicateurRef = useRef(null)
  const readyRef = useRef(false)
  const selectedRef = useRef(null)
  const compareArrRef = useRef([])
  const compareModeRef = useRef(false)
  const onArrClickRef = useRef(null)
  const irisDataRef = useRef(null)

  onArrClickRef.current = onArrClick
  selectedRef.current = selected
  compareArrRef.current = compareArr
  compareModeRef.current = compareMode

  const renderLayers = (map) => {
    const gd = geoDataRef.current
    const ind = indicateurRef.current
    if (!gd || !ind) return
    const values = gd.features.map(f => f.properties[ind]).filter(v => v != null)

    ;["arr-fill","arr-line","arr-selected"].forEach(id => {
      if (map.getLayer(id)) map.removeLayer(id)
    })
    if (map.getSource("arr")) map.removeSource("arr")

    const enriched = {
      ...gd,
      features: gd.features.map(f => ({
        ...f,
        properties: {
          ...f.properties,
          color: getColor(f.properties[ind], values, ind)
        }
      }))
    }

    map.addSource("arr", { type: "geojson", data: enriched })
    map.addLayer({
      id: "arr-fill", type: "fill", source: "arr",
      paint: {
        "fill-color": ["get","color"],
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 12, 0.65, 13.5, 0.0]
      }
    })
    map.addLayer({
      id: "arr-line", type: "line", source: "arr",
      paint: { "line-color": "#94a3b8", "line-width": 1.5 }
    })
    map.addLayer({
      id: "arr-selected", type: "line", source: "arr",
      paint: { "line-color": "#3b82f6", "line-width": 3 },
      filter: ["in", "arrondissement",
        ...(compareModeRef.current ? compareArrRef.current : selectedRef.current ? [selectedRef.current] : [-1])
      ]
    })

    map.off("click", "arr-fill")
    map.on("click", "arr-fill", e => {
      onArrClickRef.current(e.features[0].properties.arrondissement)
    })
    map.on("mouseenter", "arr-fill", () => { map.getCanvas().style.cursor = "pointer" })
    map.on("mouseleave", "arr-fill", () => { map.getCanvas().style.cursor = "" })

    // Mettre à jour les IRIS si déjà chargés
    if (irisDataRef.current) {
      renderIrisLayer(map, irisDataRef.current, ind)
    }
  }

  const renderIrisLayer = (map, irisData, ind) => {
    const palette = PALETTES[ind] || PALETTES.prix_m2_median
    // Pour l'IRIS on utilise toujours le prix au m²
    const irisValues = irisData.features
      .map(f => f.properties.prix_m2_median)
      .filter(v => v != null)
    const irisMin = Math.min(...irisValues)
    const irisMax = Math.max(...irisValues)

    const enrichedIris = {
      ...irisData,
      features: irisData.features.map(f => ({
        ...f,
        properties: {
          ...f.properties,
          color: getColor(f.properties.prix_m2_median, irisValues, ind)
        }
      }))
    }

    ;["iris-fill","iris-line"].forEach(id => {
      if (map.getLayer(id)) map.removeLayer(id)
    })
    if (map.getSource("iris")) map.removeSource("iris")

    map.addSource("iris", { type: "geojson", data: enrichedIris })

    map.addLayer({
      id: "iris-fill", type: "fill", source: "iris",
      minzoom: 12.5,
      paint: {
        "fill-color": ["get","color"],
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 12.5, 0.0, 13.5, 0.75]
      }
    })
    map.addLayer({
      id: "iris-line", type: "line", source: "iris",
      minzoom: 12.5,
      paint: {
        "line-color": "#ffffff",
        "line-width": 0.8,
        "line-opacity": ["interpolate", ["linear"], ["zoom"], 12.5, 0.0, 13.5, 0.8]
      }
    })

    // Tooltip IRIS avec l'indicateur courant
    map.off("mouseenter", "iris-fill")
    map.off("mouseleave", "iris-fill")
    map.off("mousemove", "iris-fill")

    const indInfo = INDICATEUR_LABELS[ind] || { label: "Valeur", unit: "" }

    map.on("mouseenter", "iris-fill", e => {
      map.getCanvas().style.cursor = "pointer"
      const props = e.features[0].properties
      const val = props.prix_m2_median
      const fmtVal = val
        ? `${Math.round(val).toLocaleString("fr-FR")} €/m²`
        : "Pas de données"

      if (popupRef.current) popupRef.current.remove()
      popupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10 })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div style="background:white;color:#1e293b;padding:10px 14px;border-radius:10px;
            box-shadow:0 4px 20px rgba(0,0,0,0.12);font-family:system-ui,sans-serif;min-width:180px">
            <div style="font-weight:700;font-size:13px;margin-bottom:4px;color:#1e3a5f">
              ${props.nom_iris || props.code_iris}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-bottom:6px">${props.code_iris}</div>
            <div style="font-size:11px;color:#64748b;margin-bottom:2px">Prix médian au m²</div>
            <div style="font-size:16px;font-weight:700;color:#3b82f6">${fmtVal}</div>
            ${props.nb_transactions ? `<div style="font-size:11px;color:#94a3b8;margin-top:2px">${props.nb_transactions} transactions (2021-2025)</div>` : ""}
          </div>
        `)
        .addTo(map)
    })
    map.on("mouseleave", "iris-fill", () => {
      map.getCanvas().style.cursor = ""
      if (popupRef.current) { popupRef.current.remove(); popupRef.current = null }
    })
    map.on("mousemove", "iris-fill", e => {
      if (popupRef.current) popupRef.current.setLngLat(e.lngLat)
    })
  }

  const loadIris = (map) => {
    fetch("http://localhost:8000/api/iris/choropleth")
      .then(r => r.json())
      .then(irisData => {
        irisDataRef.current = irisData
        renderIrisLayer(map, irisData, indicateurRef.current || "prix_m2_median")
      })
      .catch(err => console.warn("IRIS non chargé:", err))
  }

  const renderMarkers = () => {
    markersRef.current.forEach(m => m.remove())
    markersRef.current = []

    Object.entries(ARR_CENTERS).forEach(([arr, coords]) => {
      const num = parseInt(arr)
      const isSelected = compareModeRef.current
        ? compareArrRef.current.includes(num)
        : selectedRef.current === num

      const el = document.createElement("div")
      el.style.width = "26px"
      el.style.height = "26px"
      el.style.borderRadius = "50%"
      el.style.background = isSelected ? "#3b82f6" : "white"
      el.style.color = isSelected ? "white" : "#1e3a5f"
      el.style.border = isSelected ? "2px solid #1d4ed8" : "2px solid #94a3b8"
      el.style.display = "flex"
      el.style.alignItems = "center"
      el.style.justifyContent = "center"
      el.style.fontSize = "11px"
      el.style.fontWeight = "800"
      el.style.cursor = "pointer"
      el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.15)"
      el.style.fontFamily = "system-ui, sans-serif"
      el.style.pointerEvents = "all"
      el.textContent = num

      el.addEventListener("click", e => {
        e.stopPropagation()
        onArrClickRef.current(num)
      })

      const marker = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat(coords)
        .addTo(mapInstance.current)
      markersRef.current.push(marker)
    })
  }

  useEffect(() => {
    if (mapInstance.current) return
    const map = new maplibregl.Map({
      container: mapRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap"
          }
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }]
      },
      center: [2.3488, 48.8534],
      zoom: 12.2,
      minZoom: 10.5,
    })

    map.on("load", () => {
      readyRef.current = true
      renderLayers(map)
      renderMarkers()
      loadIris(map)
    })

    mapInstance.current = map
  }, [])

  useEffect(() => {
    geoDataRef.current = geoData
    indicateurRef.current = indicateur
    if (!mapInstance.current || !readyRef.current) return
    renderLayers(mapInstance.current)
  }, [geoData, indicateur])

  useEffect(() => {
    if (!mapInstance.current || !readyRef.current) return
    renderMarkers()
    if (mapInstance.current.getLayer("arr-selected")) {
      mapInstance.current.setFilter("arr-selected", [
        "in", "arrondissement",
        ...(compareMode ? compareArr : selected ? [selected] : [-1])
      ])
    }
  }, [selected, compareArr, compareMode])

  return <div ref={mapRef} style={{ width: "100%", height: "100%" }} />
}