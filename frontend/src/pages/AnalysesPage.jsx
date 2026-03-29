import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  BarChart, Bar, ResponsiveContainer,
} from 'recharts'
import api from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'

const ANALYSES = [
  { id: 'richness',     label: 'Riqueza',                   icon: 'S' },
  { id: 'shannon',      label: 'Shannon-Wiener (H\')',       icon: 'H' },
  { id: 'simpson',      label: 'Simpson (D)',                icon: 'D' },
  { id: 'accumulation', label: 'Acumulación de especies',    icon: '~' },
  { id: 'bray-curtis',  label: 'Bray-Curtis (beta)',         icon: 'β' },
  { id: 'jaccard',      label: 'Jaccard (beta)',             icon: 'β' },
]

function ScopeSelector({ value, onChange, events, locations }) {
  return (
    <div className="flex flex-wrap gap-3 items-end">
      <div>
        <label className="label">Alcance</label>
        <select className="input w-36" value={value.type} onChange={(e) => onChange({ type: e.target.value, id: null })}>
          <option value="project">Proyecto completo</option>
          <option value="location">Por localidad</option>
          <option value="event">Por evento</option>
        </select>
      </div>
      {value.type === 'location' && (
        <div>
          <label className="label">Localidad</label>
          <select className="input w-48" value={value.id || ''} onChange={(e) => onChange({ ...value, id: Number(e.target.value) || null })}>
            <option value="">— Seleccionar —</option>
            {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
      )}
      {value.type === 'event' && (
        <div>
          <label className="label">Evento</label>
          <select className="input w-52" value={value.id || ''} onChange={(e) => onChange({ ...value, id: Number(e.target.value) || null })}>
            <option value="">— Seleccionar —</option>
            {events.map((ev) => <option key={ev.id} value={ev.id}>{ev.location_name} — {ev.start_date}</option>)}
          </select>
        </div>
      )}
    </div>
  )
}

function RichnessResult({ results }) {
  const data = results.per_replicate || []
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-primary-600">{results.S_total}</p>
          <p className="text-sm text-slate-500">Taxa totales (S)</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-3xl font-bold text-slate-600">{results.N_total}</p>
          <p className="text-sm text-slate-500">Individuos totales (N)</p>
        </div>
      </div>
      {data.length > 0 && (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="S" name="Riqueza (S)" fill="#16a34a" />
            <Bar dataKey="N" name="Abundancia (N)" fill="#64748b" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

function ShannonResult({ results }) {
  const data = results.per_replicate || []
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <Metric label="H' (Shannon)" value={results.H?.toFixed(4)} accent />
        <Metric label="Equitabilidad J'" value={results.J?.toFixed(4)} />
        <Metric label="S" value={results.S} />
      </div>
      {data.length > 0 && (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="H" name="H' Shannon" fill="#059669" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

function SimpsonResult({ results }) {
  const data = results.per_replicate || []
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <Metric label="D (Simpson 1-D)" value={results.D?.toFixed(4)} accent />
        <Metric label="Dominancia λ" value={results.lambda?.toFixed(4)} />
        <Metric label="S" value={results.S} />
      </div>
      {data.length > 0 && (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 1]} />
            <Tooltip />
            <Bar dataKey="D" name="D Simpson" fill="#7c3aed" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

function AccumulationResult({ results, plotB64 }) {
  const data = (results.x || []).map((x, i) => ({
    samples: x,
    mean: results.mean?.[i],
    upper: (results.mean?.[i] || 0) + (results.sd?.[i] || 0),
    lower: Math.max(0, (results.mean?.[i] || 0) - (results.sd?.[i] || 0)),
  }))
  return (
    <div className="space-y-4">
      {plotB64 ? (
        <img src={`data:image/png;base64,${plotB64}`} alt="Curva de acumulación" className="max-w-full rounded" />
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="samples" label={{ value: 'Muestras', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Taxa', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="mean" stroke="#059669" name="Media" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="upper" stroke="#a7f3d0" name="+1 DE" strokeDasharray="4 2" dot={false} />
            <Line type="monotone" dataKey="lower" stroke="#a7f3d0" name="-1 DE" strokeDasharray="4 2" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      )}
      <p className="text-xs text-slate-400">Riqueza máxima observada: {results.max?.[results.max.length - 1]} | Muestras: {results.x?.length}</p>
    </div>
  )
}

function BetaResult({ results, plotB64, title }) {
  return (
    <div className="space-y-4">
      <div className="card p-4 text-center inline-block">
        <p className="text-2xl font-bold text-primary-600">{results.mean_dissimilarity?.toFixed(4)}</p>
        <p className="text-sm text-slate-500">Disimilitud media</p>
      </div>
      {plotB64 ? (
        <img src={`data:image/png;base64,${plotB64}`} alt={title} className="max-w-full rounded" />
      ) : (
        <div className="overflow-x-auto">
          <table className="text-xs border-collapse">
            <thead>
              <tr>
                <th className="px-3 py-1 bg-slate-100"></th>
                {(results.samples || []).map((s, i) => (
                  <th key={i} className="px-3 py-1 bg-slate-100 text-left font-medium">{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(results.matrix || []).map((row, i) => (
                <tr key={i}>
                  <td className="px-3 py-1 bg-slate-50 font-medium">{results.samples[i]}</td>
                  {row.map((v, j) => (
                    <td key={j} className={`px-3 py-1 text-center ${i === j ? 'text-slate-300' : v > 0.7 ? 'text-red-600' : v > 0.4 ? 'text-orange-500' : 'text-green-600'}`}>
                      {v.toFixed(3)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Metric({ label, value, accent }) {
  return (
    <div className={`card p-4 text-center ${accent ? 'border-primary-200' : ''}`}>
      <p className={`text-3xl font-bold ${accent ? 'text-primary-600' : 'text-slate-700'}`}>{value ?? '—'}</p>
      <p className="text-xs text-slate-500 mt-1">{label}</p>
    </div>
  )
}

function downloadCsv(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
}

export default function AnalysesPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)

  const [selected, setSelected] = useState('richness')
  const [scope, setScope] = useState({ type: 'project', id: null })
  const [permutations, setPermutations] = useState(100)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [events, setEvents] = useState([])
  const [locations, setLocations] = useState([])

  useEffect(() => {
    Promise.all([api.getEvents(pid), api.getLocations(pid)]).then(([evs, locs]) => {
      setEvents(evs); setLocations(locs)
    })
  }, [pid])

  const run = async () => {
    setLoading(true); setError(''); setResult(null)
    try {
      const body = { project_id: pid, scope, permutations }
      const fn = {
        richness: api.runRichness, shannon: api.runShannon, simpson: api.runSimpson,
        accumulation: api.runAccumulation, 'bray-curtis': api.runBrayCurtis, jaccard: api.runJaccard,
      }[selected]
      const res = await fn(body)
      setResult(res)
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }

  return (
    <div className="flex h-full">
      {/* Sidebar: analysis picker */}
      <div className="w-56 border-r border-slate-200 bg-white flex flex-col">
        <div className="px-4 py-3 border-b border-slate-200">
          <h2 className="font-semibold text-slate-700">Análisis</h2>
        </div>
        <nav className="flex-1 py-2">
          {ANALYSES.map(({ id, label, icon }) => (
            <button
              key={id}
              className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 hover:bg-slate-50 transition-colors
                ${selected === id ? 'bg-primary-50 text-primary-700 font-medium' : 'text-slate-600'}`}
              onClick={() => { setSelected(id); setResult(null) }}
            >
              <span className="w-6 h-6 flex items-center justify-center rounded bg-slate-100 text-xs font-mono font-bold">{icon}</span>
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Main */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl">
          <h2 className="text-xl font-bold text-slate-800 mb-4">
            {ANALYSES.find((a) => a.id === selected)?.label}
          </h2>

          {/* Parameters */}
          <div className="card p-4 mb-4 space-y-3">
            <ScopeSelector value={scope} onChange={setScope} events={events} locations={locations} />
            {selected === 'accumulation' && (
              <div>
                <label className="label">Permutaciones</label>
                <input className="input w-28" type="number" min="10" max="999" value={permutations}
                  onChange={(e) => setPermutations(Number(e.target.value))} />
              </div>
            )}
            <div className="flex gap-3 items-center">
              <button className="btn-primary" onClick={run} disabled={loading}>
                {loading ? '⏳ Calculando…' : '▶ Ejecutar'}
              </button>
              {result && (
                <button className="btn-secondary text-xs" onClick={() => downloadCsv(result, `${selected}_${Date.now()}.json`)}>
                  💾 Exportar JSON
                </button>
              )}
            </div>
          </div>

          {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

          {loading && <LoadingSpinner message="Calculando análisis…" />}

          {result && !loading && (
            <div className="card p-5">
              <div className="flex items-center gap-2 text-xs text-slate-400 mb-4">
                <span>Alcance: {result.scope.type}{result.scope.id ? ` #${result.scope.id}` : ''}</span>
                <span>·</span>
                <span>{result.timestamp?.substring(0,19).replace('T',' ')} UTC</span>
                {result.parameters?.permutations && <><span>·</span><span>{result.parameters.permutations} permutaciones</span></>}
              </div>
              {selected === 'richness'     && <RichnessResult results={result.results} />}
              {selected === 'shannon'      && <ShannonResult  results={result.results} />}
              {selected === 'simpson'      && <SimpsonResult  results={result.results} />}
              {selected === 'accumulation' && <AccumulationResult results={result.results} plotB64={result.plot_b64} />}
              {selected === 'bray-curtis'  && <BetaResult results={result.results} plotB64={result.plot_b64} title="Bray-Curtis" />}
              {selected === 'jaccard'      && <BetaResult results={result.results} plotB64={result.plot_b64} title="Jaccard" />}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
