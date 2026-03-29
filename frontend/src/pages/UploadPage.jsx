/**
 * Mobile-friendly photo upload page.
 * Accessible at /upload?project=<id>
 * No authentication by design (LAN-only, MVP #1).
 */
import React, { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import api from '../api/client'

export default function UploadPage() {
  const [searchParams] = useSearchParams()
  const projectId = Number(searchParams.get('project'))

  const [destinations, setDestinations] = useState([])
  const [searchQ, setSearchQ] = useState('')
  const [selected, setSelected] = useState(null)
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')

  const searchDests = useCallback(async (q) => {
    if (!projectId) return
    const res = await api.searchDestinations(projectId, q)
    setDestinations(res)
  }, [projectId])

  useEffect(() => { searchDests('') }, [searchDests])

  const handleSearch = (e) => {
    setSearchQ(e.target.value)
    searchDests(e.target.value)
  }

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files || []))
    setResults(null)
  }

  const handleUpload = async () => {
    if (!selected || files.length === 0) return
    setUploading(true); setError(''); setResults(null)
    try {
      const form = new FormData()
      form.append('project_id', projectId)
      form.append('linked_to_type', selected.type)
      form.append('linked_to_id', selected.id)
      for (const f of files) form.append('files', f)
      const res = await api.uploadFiles(form)
      setResults(res)
      setFiles([])
    } catch (e) { setError(e.message) } finally { setUploading(false) }
  }

  const TYPE_LABEL = { taxon: '🦋 Taxa', location: '📍 Localidad', replicate: '🧪 Réplica', record: '📋 Registro' }

  if (!projectId) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-6">
        <p className="text-lg text-red-400">URL inválida: falta el parámetro <code>?project=ID</code></p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* LAN disclaimer banner */}
      <div className="bg-amber-600 text-white text-xs text-center px-4 py-2">
        ⚠ Esta página es accesible desde la red local (LAN). Sin autenticación por diseño. Solo usar en red privada.
      </div>

      <div className="max-w-md mx-auto p-5 pt-8 space-y-6">
        <div className="text-center">
          <span className="text-4xl">🌿</span>
          <h1 className="text-2xl font-bold text-primary-400 mt-2">EcoNodeX</h1>
          <p className="text-slate-400 text-sm">Subida de fotos desde móvil</p>
        </div>

        {/* Step 1: destination */}
        <div className="bg-slate-800 rounded-xl p-4 space-y-3">
          <h2 className="font-semibold text-primary-300">1. ¿A dónde vincular las fotos?</h2>
          <input
            className="w-full bg-slate-700 text-white px-3 py-2 rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Buscar taxón, localidad o réplica…"
            value={searchQ}
            onChange={handleSearch}
          />
          <div className="space-y-1 max-h-52 overflow-y-auto">
            {destinations.map((d) => (
              <button
                key={`${d.type}-${d.id}`}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors
                  ${selected?.type === d.type && selected?.id === d.id
                    ? 'bg-primary-700 text-white'
                    : 'bg-slate-700 hover:bg-slate-600 text-slate-200'}`}
                onClick={() => setSelected(d)}
              >
                <span className="text-xs text-slate-400">{TYPE_LABEL[d.type] || d.type}</span>
                <span className="flex-1 truncate">{d.label}</span>
                {selected?.type === d.type && selected?.id === d.id && <span>✓</span>}
              </button>
            ))}
            {destinations.length === 0 && (
              <p className="text-xs text-slate-500 italic px-2 py-3">Sin resultados.</p>
            )}
          </div>
          {selected && (
            <p className="text-xs text-primary-300">
              Seleccionado: <strong>{selected.label}</strong> ({selected.type})
            </p>
          )}
        </div>

        {/* Step 2: file selection */}
        <div className="bg-slate-800 rounded-xl p-4 space-y-3">
          <h2 className="font-semibold text-primary-300">2. Selecciona las fotos</h2>
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-slate-600 rounded-lg cursor-pointer hover:border-primary-500 transition-colors">
            <span className="text-3xl mb-1">📷</span>
            <span className="text-sm text-slate-400">Toca para elegir fotos</span>
            <input
              type="file"
              accept="image/*"
              multiple
              capture="environment"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>
          {files.length > 0 && (
            <div className="space-y-1">
              {files.map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-300 bg-slate-700 px-3 py-1.5 rounded">
                  <span>📄</span>
                  <span className="flex-1 truncate">{f.name}</span>
                  <span className="text-slate-400">{(f.size / 1024).toFixed(0)} KB</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upload button */}
        <button
          className={`w-full py-3 rounded-xl font-semibold text-lg transition-colors
            ${!selected || files.length === 0 || uploading
              ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
              : 'bg-primary-600 hover:bg-primary-700 text-white'}`}
          onClick={handleUpload}
          disabled={!selected || files.length === 0 || uploading}
        >
          {uploading ? '⏳ Subiendo…' : `📤 Subir ${files.length || ''} foto(s)`}
        </button>

        {error && <p className="text-sm text-red-400 text-center">{error}</p>}

        {results && (
          <div className="bg-slate-800 rounded-xl p-4 space-y-2">
            <p className="font-semibold text-primary-300">Resultado:</p>
            {results.saved.map((s) => (
              <p key={s.id} className="text-sm text-green-400">✓ {s.file_name}</p>
            ))}
            {results.errors.map((e, i) => (
              <p key={i} className="text-sm text-red-400">✕ {e.file_name}: {e.error}</p>
            ))}
            <button className="btn-ghost text-sm w-full mt-2 text-slate-300" onClick={() => { setResults(null); setSelected(null) }}>
              Subir más fotos
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
