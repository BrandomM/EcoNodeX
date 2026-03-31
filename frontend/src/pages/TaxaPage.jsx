import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import TreeView from '../components/TreeView'
import PhotoGallery from '../components/PhotoGallery'

const RANKS = ['reino','filo','clase','orden','familia','tribu','género','especie','subespecie','morfoespecie','morphospecies']

function TaxonForm({ initial = {}, projectId, taxa = [], onSave, onClose }) {
  const [form, setForm] = useState({
    project_id: projectId,
    scientific_name: initial.scientific_name || '',
    rank: initial.rank || 'especie',
    common_name: initial.common_name || '',
    alias: initial.alias || '',
    parent_taxon_id: initial.parent_taxon_id || '',
    description: initial.description || '',
    is_recordable: initial.is_recordable ?? false,
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.scientific_name.trim()) { setError('Nombre científico requerido.'); return }
    setSaving(true)
    try {
      const payload = {
        ...form,
        parent_taxon_id: form.parent_taxon_id ? Number(form.parent_taxon_id) : null,
      }
      if (!payload.alias) delete payload.alias  // backend will auto-generate
      await onSave(payload)
      onClose()
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="label">Nombre científico *</label>
          <input className="input" value={form.scientific_name} onChange={(e) => setForm({ ...form, scientific_name: e.target.value })} required />
        </div>
        <div>
          <label className="label">Rango taxonómico *</label>
          <select className="input" value={form.rank} onChange={(e) => setForm({ ...form, rank: e.target.value })}>
            {RANKS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Nombre común</label>
          <input className="input" value={form.common_name} onChange={(e) => setForm({ ...form, common_name: e.target.value })} />
        </div>
        <div>
          <label className="label">Alias (auto si vacío)</label>
          <input className="input" value={form.alias} onChange={(e) => setForm({ ...form, alias: e.target.value })} placeholder="Auto" />
        </div>
        <div>
          <label className="label">Taxón padre</label>
          <select className="input" value={form.parent_taxon_id} onChange={(e) => setForm({ ...form, parent_taxon_id: e.target.value })}>
            <option value="">— Sin padre —</option>
            {taxa.filter((t) => t.id !== initial.id).map((t) => (
              <option key={t.id} value={t.id}>{t.alias || t.scientific_name}</option>
            ))}
          </select>
        </div>
        <div className="col-span-2">
          <label className="label">Descripción / notas</label>
          <textarea className="input h-16 resize-none" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
        <div className="col-span-2">
          <label className="flex items-center gap-3 cursor-pointer select-none">
            <div
              className={`relative w-10 h-6 rounded-full transition-colors ${form.is_recordable ? 'bg-primary-500' : 'bg-slate-300'}`}
              onClick={() => setForm({ ...form, is_recordable: !form.is_recordable })}
            >
              <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.is_recordable ? 'translate-x-4' : ''}`} />
            </div>
            <span className="text-sm text-slate-700">
              Usar en registros de ocurrencia
              {form.is_recordable && <span className="ml-2 text-xs text-primary-600 font-medium">● activo</span>}
            </span>
          </label>
          <p className="text-xs text-slate-400 mt-1 ml-13">
            Solo los taxones marcados aquí aparecen al crear registros.
          </p>
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </div>
    </form>
  )
}

function MergeDialog({ projectId, taxa, onClose }) {
  const [sourceId, setSourceId] = useState('')
  const [targetId, setTargetId] = useState('')
  const [preview, setPreview] = useState(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  const [merging, setMerging] = useState(false)
  const [confirmText, setConfirmText] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handlePreview = async () => {
    if (!sourceId || !targetId) return
    setLoadingPreview(true)
    setError('')
    try {
      const p = await api.mergePreview({ source_taxon_id: Number(sourceId), target_taxon_id: Number(targetId) })
      setPreview(p)
    } catch (e) { setError(e.message) } finally { setLoadingPreview(false) }
  }

  const handleMerge = async () => {
    if (confirmText !== 'CONFIRMAR') return
    setMerging(true)
    setError('')
    try {
      await api.mergeExecute({
        source_taxon_id: Number(sourceId),
        target_taxon_id: Number(targetId),
        confirmation: confirmText,
      })
      setSuccess('Fusión completada. Se creó un respaldo automático antes de la operación.')
    } catch (e) { setError(e.message) } finally { setMerging(false) }
  }

  return (
    <div className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      {success ? (
        <div className="text-center py-4">
          <p className="text-green-600 font-medium">{success}</p>
          <button className="btn-primary mt-4" onClick={onClose}>Cerrar</button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Taxón origen (será eliminado)</label>
              <select className="input" value={sourceId} onChange={(e) => { setSourceId(e.target.value); setPreview(null) }}>
                <option value="">— Seleccionar —</option>
                {taxa.map((t) => <option key={t.id} value={t.id}>{t.alias || t.scientific_name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Taxón destino (permanece)</label>
              <select className="input" value={targetId} onChange={(e) => { setTargetId(e.target.value); setPreview(null) }}>
                <option value="">— Seleccionar —</option>
                {taxa.map((t) => <option key={t.id} value={t.id}>{t.alias || t.scientific_name}</option>)}
              </select>
            </div>
          </div>
          <button className="btn-secondary" onClick={handlePreview} disabled={!sourceId || !targetId || loadingPreview}>
            {loadingPreview ? 'Calculando…' : 'Ver impacto'}
          </button>
          {preview && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-2">
              <p className="font-medium text-amber-800">Impacto de la fusión:</p>
              <p className="text-sm text-amber-700">
                <strong>{preview.records_affected}</strong> registros y{' '}
                <strong>{preview.media_affected}</strong> fotos serán reasignados de
                {' '}<em>{preview.source_taxon_name}</em> a{' '}
                <em>{preview.target_taxon_name}</em>.
              </p>
              <p className="text-xs text-amber-600">⚠ Esta operación es irreversible. Se crea un respaldo automático antes de ejecutar.</p>
              <div className="mt-3">
                <label className="label text-amber-800">Escribe <strong className="font-mono">CONFIRMAR</strong> para proceder:</label>
                <input className="input" value={confirmText} onChange={(e) => setConfirmText(e.target.value)} />
              </div>
              <button
                className="btn-danger mt-2"
                onClick={handleMerge}
                disabled={confirmText !== 'CONFIRMAR' || merging}
              >
                {merging ? 'Fusionando…' : 'Ejecutar fusión'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default function TaxaPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)

  const [taxa, setTaxa] = useState([])
  const [taxaFlat, setTaxaFlat] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [viewMode, setViewMode] = useState('tree')  // tree | list
  const [selectedTaxon, setSelectedTaxon] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [editTaxon, setEditTaxon] = useState(null)
  const [showMerge, setShowMerge] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [mediaList, setMediaList] = useState([])
  const [deleting, setDeleting] = useState(false)
  const [showQR, setShowQR] = useState(false)
  const [qrData, setQrData] = useState(null)

  const loadTaxa = useCallback(async () => {
    setLoading(true)
    try {
      const [treeData, flatData] = await Promise.all([
        api.getTaxa(pid, { tree: true }),
        api.getTaxa(pid, {}),
      ])
      setTaxa(treeData)
      setTaxaFlat(flatData)
    } finally { setLoading(false) }
  }, [pid])

  useEffect(() => { loadTaxa() }, [loadTaxa])

  const loadMedia = async (taxon) => {
    const media = await api.getMedia(pid, 'taxon', taxon.id)
    setMediaList(media)
  }

  const handleSelect = (taxon) => {
    setSelectedTaxon(taxon)
    loadMedia(taxon)
  }

  const handleSearch = async (q) => {
    setSearch(q)
    if (q) {
      const results = await api.getTaxa(pid, { search: q })
      setTaxaFlat(results)
      setViewMode('list')
    } else {
      await loadTaxa()
      setViewMode('tree')
    }
  }

  const handleCreate = async (form) => {
    await api.createTaxon(form)
    await loadTaxa()
  }

  const handleEdit = async (form) => {
    await api.updateTaxon(editTaxon.id, form)
    await loadTaxa()
    if (selectedTaxon?.id === editTaxon.id) {
      const updated = await api.getTaxa(pid, { search: form.scientific_name })
      setSelectedTaxon(updated[0] || null)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await api.deleteTaxon(deleteTarget.id)
      await loadTaxa()
      if (selectedTaxon?.id === deleteTarget.id) setSelectedTaxon(null)
      setDeleteTarget(null)
    } catch (e) { alert(e.message) } finally { setDeleting(false) }
  }

  const handleSetProfile = async (media) => {
    await api.updateMedia(media.id, { is_profile: true, linked_to_type: 'taxon', linked_to_id: selectedTaxon.id })
    loadMedia(selectedTaxon)
  }

  const handleDeleteMedia = async (media) => {
    if (!confirm(`¿Eliminar "${media.file_name}"?`)) return
    await api.deleteMedia(media.id)
    loadMedia(selectedTaxon)
  }

  const openQR = async () => {
    const data = await api.getUploadQR(pid)
    setQrData(data)
    setShowQR(true)
  }

  const RANK_COLORS = {
    'orden': 'badge-blue', 'familia': 'badge-purple', 'género': 'badge-green',
    'especie': 'badge-green', 'morfoespecie': 'badge-orange', 'morphospecies': 'badge-orange',
  }

  const displayList = viewMode === 'tree' ? taxa : taxaFlat

  return (
    <div className="flex h-full">
      {/* Left panel: tree/list */}
      <div className="w-72 border-r border-slate-200 flex flex-col bg-white">
        <div className="px-4 py-3 border-b border-slate-200">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-slate-700">Taxa</h2>
            <div className="flex gap-1">
              <button className={`btn-ghost text-xs px-2 ${viewMode === 'tree' ? 'bg-slate-100' : ''}`} onClick={() => { setViewMode('tree'); setSearch('') }}>Árbol</button>
              <button className={`btn-ghost text-xs px-2 ${viewMode === 'list' ? 'bg-slate-100' : ''}`} onClick={() => setViewMode('list')}>Lista</button>
            </div>
          </div>
          <input
            className="input text-xs"
            placeholder="Buscar por nombre, alias…"
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-slate-400 p-4 text-center">Cargando…</p>
          ) : viewMode === 'tree' ? (
            <TreeView
              nodes={displayList}
              labelKey="scientific_name"
              renderLabel={(t) => (
                <span className="flex items-center gap-1.5">
                  <span className="truncate">{t.scientific_name}</span>
                  {t.is_recordable && <span className="text-primary-500 text-xs flex-shrink-0" title="Usar en registros">●</span>}
                </span>
              )}
              onSelect={handleSelect}
              onEdit={setEditTaxon}
              onDelete={setDeleteTarget}
              selectedId={selectedTaxon?.id}
            />
          ) : (
            <div>
              {displayList.map((t) => (
                <div
                  key={t.id}
                  className={`px-4 py-2 cursor-pointer hover:bg-slate-50 ${selectedTaxon?.id === t.id ? 'bg-primary-50' : ''}`}
                  onClick={() => handleSelect(t)}
                >
                  <div className="flex items-center gap-1.5">
                    <p className="text-sm font-medium text-slate-800 truncate">{t.scientific_name}</p>
                    {t.is_recordable && <span className="text-primary-500 text-xs flex-shrink-0" title="Usar en registros">●</span>}
                  </div>
                  <div className="flex gap-1 mt-0.5">
                    {t.alias && <span className="text-xs text-slate-400">{t.alias}</span>}
                    <span className={`${RANK_COLORS[t.rank] || 'badge-slate'} ml-auto`}>{t.rank}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="px-4 py-3 border-t border-slate-200 flex gap-2">
          <button className="btn-primary flex-1 text-xs" onClick={() => setShowCreate(true)}>+ Taxón</button>
          <button className="btn-secondary text-xs" onClick={() => setShowMerge(true)} title="Fusionar taxa">⇄ Fusionar</button>
          <button className="btn-ghost text-xs" onClick={openQR} title="Subir fotos desde móvil">📷</button>
        </div>
      </div>

      {/* Right panel: detail */}
      <div className="flex-1 p-6 overflow-y-auto">
        {selectedTaxon ? (
          <>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-800">{selectedTaxon.scientific_name}</h2>
                {selectedTaxon.common_name && (
                  <p className="text-slate-500 italic">{selectedTaxon.common_name}</p>
                )}
                <div className="flex gap-2 mt-1">
                  <span className={`${RANK_COLORS[selectedTaxon.rank] || 'badge-slate'}`}>{selectedTaxon.rank}</span>
                  {selectedTaxon.alias && <span className="badge-slate">{selectedTaxon.alias}</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary text-sm" onClick={() => setEditTaxon(selectedTaxon)}>✎ Editar</button>
                <button className="btn text-sm text-red-600 hover:bg-red-50 border border-red-200" onClick={() => setDeleteTarget(selectedTaxon)}>Eliminar</button>
              </div>
            </div>
            {selectedTaxon.description && (
              <p className="text-sm text-slate-600 mb-4 bg-slate-50 p-3 rounded whitespace-pre-wrap">{selectedTaxon.description}</p>
            )}
            <div className="mb-2 flex items-center justify-between">
              <h3 className="font-medium text-slate-700">Fotos</h3>
              <button className="btn-ghost text-xs" onClick={openQR}>📷 Subir desde móvil</button>
            </div>
            <PhotoGallery media={mediaList} onSetProfile={handleSetProfile} onDelete={handleDeleteMedia} />
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <p className="text-5xl mb-4">🦋</p>
            <p className="text-lg font-medium">Selecciona un taxón</p>
            <p className="text-sm">o crea uno nuevo con el botón + Taxón.</p>
          </div>
        )}
      </div>

      {/* Modals */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nuevo taxón">
        <TaxonForm projectId={pid} taxa={taxaFlat} onSave={handleCreate} onClose={() => setShowCreate(false)} />
      </Modal>
      {editTaxon && (
        <Modal isOpen={!!editTaxon} onClose={() => setEditTaxon(null)} title="Editar taxón">
          <TaxonForm initial={editTaxon} projectId={pid} taxa={taxaFlat} onSave={handleEdit} onClose={() => setEditTaxon(null)} />
        </Modal>
      )}
      <Modal isOpen={showMerge} onClose={() => setShowMerge(false)} title="Fusionar taxa" size="lg">
        <MergeDialog projectId={pid} taxa={taxaFlat} onClose={() => { setShowMerge(false); loadTaxa() }} />
      </Modal>
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Eliminar taxón"
        message={`¿Eliminar "${deleteTarget?.scientific_name}"? Solo se puede eliminar si no tiene registros de ocurrencia.`}
        confirmLabel="Eliminar"
        danger
        loading={deleting}
      />

      {/* QR Modal */}
      {showQR && qrData && (
        <Modal isOpen={showQR} onClose={() => setShowQR(false)} title="Subir fotos desde móvil" size="sm">
          <div className="text-center space-y-4">
            <div className="bg-amber-50 border border-amber-200 rounded p-3 text-xs text-amber-700">
              ⚠ Esta página es accesible en tu red local (LAN). Sin autenticación por diseño.
            </div>
            <p className="text-sm text-slate-600">Escanea el QR con tu móvil (misma red Wi-Fi):</p>
            <img src={`data:image/png;base64,${qrData.qr_b64}`} alt="QR" className="mx-auto w-48 h-48" />
            <p className="text-xs font-mono text-slate-500 break-all">{qrData.upload_url}</p>
          </div>
        </Modal>
      )}
    </div>
  )
}
