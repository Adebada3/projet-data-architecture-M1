import { useState, useEffect } from "react"
import axios from "axios"
import Map from "./components/Map"
import Sidebar from "./components/Sidebar"
import Header from "./components/Header"
import ComparePanel from "./components/ComparePanel"

const API = "http://localhost:8000"

export default function App() {
  const [arrondissements, setArrondissements] = useState([])
  const [selected, setSelected] = useState(null)
  const [indicateur, setIndicateur] = useState("prix_m2_median")
  const [compareMode, setCompareMode] = useState(false)
  const [compareArr, setCompareArr] = useState([])
  const [compareData, setCompareData] = useState(null)
  const [geoData, setGeoData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API}/api/arrondissements`)
      .then(r => setArrondissements(r.data.data))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    axios.get(`${API}/api/arrondissements/geo/choropleth?indicateur=${indicateur}`)
      .then(r => setGeoData(r.data))
  }, [indicateur])

  useEffect(() => {
    if (compareMode && compareArr.length === 2) {
      axios.get(`${API}/api/compare?arr1=${compareArr[0]}&arr2=${compareArr[1]}`)
        .then(r => setCompareData(r.data))
    }
  }, [compareArr, compareMode])

  const handleArrClick = (arr) => {
    if (compareMode) {
      setCompareArr(prev => {
        if (prev.includes(arr)) return prev.filter(a => a !== arr)
        if (prev.length >= 2) return [prev[1], arr]
        return [...prev, arr]
      })
    } else {
      setSelected(arr)
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#0f1117", color: "#e8e6df", fontFamily: "system-ui, sans-serif" }}>
      <Header
        compareMode={compareMode}
        setCompareMode={setCompareMode}
        setCompareArr={setCompareArr}
        setCompareData={setCompareData}
      />
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <div style={{ flex: 1, position: "relative" }}>
          <Map
            geoData={geoData}
            indicateur={indicateur}
            onArrClick={handleArrClick}
            selected={selected}
            compareArr={compareArr}
            compareMode={compareMode}
          />
        </div>
        <div style={{ width: 380, background: "#161820", borderLeft: "1px solid #2a2d3a", overflowY: "auto" }}>
          {compareMode && compareArr.length > 0 ? (
            <ComparePanel
              compareArr={compareArr}
              compareData={compareData}
              arrondissements={arrondissements}
            />
          ) : (
            <Sidebar
              arrondissements={arrondissements}
              selected={selected}
              indicateur={indicateur}
              setIndicateur={setIndicateur}
              API={API}
            />
          )}
        </div>
      </div>
    </div>
  )
}