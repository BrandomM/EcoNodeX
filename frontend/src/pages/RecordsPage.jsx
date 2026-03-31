import React, { useState, useEffect, useCallback, useRef } from 'react'
import ReactDOM from 'react-dom'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import TaxonAvatar from '../components/TaxonAvatar'
import { useRecords } from '../context/RecordsContext'

function DescriptionTooltip({ text, anchorRef, visible }) {
  const [pos, setPos] = useState({ top: 0, left: 0 })

  useEffect(() => {
    if (visible && anchorRef.current) {
      const r = anchorRef.current.getBoundingClientRect()
      setPos({
        top: r.top + window.scrollY,
        left: r.left + r.width / 2 + window.scrollX,
      })
    }
  }, [visible, anchorRef])

  if (!visible) return null

  return ReactDOM.createPortal(
    <div
      style={{ top: pos.top, left: pos.left, transform: 'translate(-50%, calc(-100% - 10px))' }}
      className="fixed z-[9999] w-72 bg-slate-800 text-white text-xs rounded-lg px-3 py-2 shadow-xl
        whitespace-pre-wrap leading-relaxed pointer-events-none"
    >
      {text}
      <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
    </div>,
    document.body
  )
}

function TaxonSearch({ taxa, value, onChange }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [focused, setFocused] = useState(false)
  const containerRef = useRef(null)

  const selected = taxa.find((t) => String(t.id) === String(value)) || null

  const filtered = query.length === 0
    ? taxa.slice(0, 50)
    : taxa.filter((t) => {
        const q = query.toLowerCase()
        return (t.alias || '').toLowerCase().startsWith(q) ||
               t.scientific_name.toLowerCase().startsWith(q)
      })

  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false)
        setFocused(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const select = (taxon) => {
    onChange(taxon.id)
    setQuery('')
    setOpen(false)
    setFocused(false)
  }

  const inputValue = focused ? query : (selected ? (selected.alias || selected.scientific_name) : '')

  return (
    <div ref={containerRef} className="relative">
      <input
        className="input w-full"
        placeholder="Buscar taxón…"
        value={inputValue}
        onFocus={() => { setFocused(true); setOpen(true); setQuery('') }}
        onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
      />
      {selected && !focused && (
        <span className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 text-xs pointer-events-none">✓</span>
      )}
      {open && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-52 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="text-xs text-slate-400 px-3 py-2 italic">Sin resultados.</p>
          ) : filtered.map((t) => (
            <div
              key={t.id}
              className={`flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-primary-50
                ${String(t.id) === String(value) ? 'bg-primary-50' : ''}`}
              onMouseDown={(e) => { e.preventDefault(); select(t) }}
            >
              <TaxonAvatar mediaId={t.profile_media_id} name={t.alias || t.scientific_name} size="h-7 w-7" />
              <span className="text-sm flex-1 truncate">{t.alias || t.scientific_name}</span>
              {t.alias && <span className="text-xs text-slate-400 truncate max-w-24">{t.scientific_name}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function RecordForm({ initial = {}, projectId, taxa = [], methods = [], replicates = [], lockedReplicate = null, onSave, onClose }) {
  const [tooltipVisible, setTooltipVisible] = useState(false)
  const previewRef = useRef(null)
  const [form, setForm] = useState({
    replicate_id: lockedReplicate?.id || initial.replicate_id || '',
    taxon_id: initial.taxon_id || '',
    individual_count: initial.individual_count ?? 1,
    method_id: initial.method_id || '',
    date_time: initial.date_time || '',
    latitude: initial.latitude ?? '',
    longitude: initial.longitude ?? '',
    notes: initial.notes || '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.replicate_id || !form.taxon_id) { setError('Réplica y taxón son requeridos.'); return }
    setSaving(true)
    try {
      await onSave({
        ...form,
        replicate_id: Number(form.replicate_id),
        taxon_id: Number(form.taxon_id),
        individual_count: Number(form.individual_count),
        method_id: form.method_id ? Number(form.method_id) : null,
        latitude:  form.latitude  !== '' ? Number(form.latitude)  : null,
        longitude: form.longitude !== '' ? Number(form.longitude) : null,
      })
      onClose()
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }
  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Réplica *</label>
          {lockedReplicate ? (
            <div className="input bg-slate-50 text-slate-600 flex items-center gap-2">
              <span className="font-mono font-medium">{lockedReplicate.code}</span>
              <span className="text-xs text-slate-400">(fijada por contexto)</span>
            </div>
          ) : (
            <select className="input" value={form.replicate_id} onChange={(e) => setForm({ ...form, replicate_id: e.target.value })} required>
              <option value="">— Seleccionar —</option>
              {replicates.map((r) => <option key={r.id} value={r.id}>{r.code} (E{r.event_id})</option>)}
            </select>
          )}
        </div>
        <div>
          <label className="label">Taxón *</label>
          <TaxonSearch
            taxa={taxa}
            value={form.taxon_id}
            onChange={(id) => setForm({ ...form, taxon_id: id })}
          />
        </div>
      </div>
      {(() => {
        const t = taxa.find((t) => String(t.id) === String(form.taxon_id))
        if (!t) return null
        return (
          <div className="flex justify-center">
            <div
              ref={previewRef}
              className="relative"
              onMouseEnter={() => t.description && setTooltipVisible(true)}
              onMouseLeave={() => setTooltipVisible(false)}
            >
              <TaxonAvatar
                mediaId={t.profile_media_id}
                name={t.alias || t.scientific_name}
                size="h-48 w-48"
                square
              />
              {t.description && (
                <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-white/80 text-slate-500 text-xs flex items-center justify-center cursor-default shadow-sm select-none">
                  ⓘ
                </span>
              )}
              <DescriptionTooltip text={t.description} anchorRef={previewRef} visible={tooltipVisible} />
            </div>
          </div>
        )
      })()}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Conteo *</label>
          <input className="input" type="number" min="0" value={form.individual_count} onChange={(e) => setForm({ ...form, individual_count: e.target.value })} required />
        </div>
        <div>
          <label className="label">Método (override)</label>
          <select className="input" value={form.method_id} onChange={(e) => setForm({ ...form, method_id: e.target.value })}>
            <option value="">— Del replicate —</option>
            {methods.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Fecha/hora</label>
          <input className="input" type="datetime-local" value={form.date_time} onChange={(e) => setForm({ ...form, date_time: e.target.value })} />
        </div>
        <div></div>
        <div>
          <label className="label">Lat</label>
          <input className="input" type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} />
        </div>
        <div>
          <label className="label">Lon</label>
          <input className="input" type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} />
        </div>
        <div className="col-span-2">
          <label className="label">Notas</label>
          <textarea className="input h-16 resize-none" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </div>
    </form>
  )
}

export default function RecordsPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)

  const {
    contextEventId, changeEvent,
    contextReplicateId, setContextReplicateId,
    contextReplicates, loadingReps,
    filters, setFilters,
    clearContext: clearCtx,
    setProject,
  } = useRecords()

  // Sync project so context resets on project change
  useEffect(() => { setProject(pid) }, [pid, setProject])

  const [records, setRecords] = useState([])
  const [taxa, setTaxa] = useState([])
  const [methods, setMethods] = useState([])
  const [events, setEvents] = useState([])
  const [allReplicates, setAllReplicates] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editRecord, setEditRecord] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [page, setPage] = useState(0)
  const LIMIT = 100

  const activeEvent = events.find((e) => String(e.id) === String(contextEventId)) || null
  const activeReplicate = contextReplicates.find((r) => String(r.id) === String(contextReplicateId)) || null

  const buildQuery = useCallback(() => {
    const q = { ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
    if (contextEventId)     q.event_id     = contextEventId
    if (contextReplicateId) q.replicate_id = contextReplicateId
    return q
  }, [filters, contextEventId, contextReplicateId])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [recs, tx, meth, evs] = await Promise.all([
        api.getRecords(pid, { ...buildQuery(), skip: page * LIMIT, limit: LIMIT }),
        api.getTaxa(pid, { recordable: true }),
        api.getMethods(pid),
        api.getEvents(pid),
      ])
      setRecords(recs)
      setTaxa(tx)
      setMethods(meth)
      setEvents(evs)
    } finally { setLoading(false) }
  }, [pid, buildQuery, page])

  useEffect(() => { load() }, [load])

  const loadAllReplicates = async () => {
    const reps = []
    for (const ev of events) {
      const r = await api.getReplicates(ev.id)
      reps.push(...r)
    }
    setAllReplicates(reps)
  }

  const handleCreate = async (form) => { await api.createRecord(form); await load() }
  const handleEdit   = async (form) => { await api.updateRecord(editRecord.id, form); await load() }
  const handleDelete = async () => {
    setDeleting(true)
    try { await api.deleteRecord(deleteTarget.id); await load(); setDeleteTarget(null) }
    catch (e) { alert(e.message) } finally { setDeleting(false) }
  }

  const openCreate = async () => {
    if (!activeReplicate) await loadAllReplicates()
    setShowCreate(true)
  }
  const openEdit = async (r) => {
    if (!activeReplicate) await loadAllReplicates()
    setEditRecord(r)
  }

  const clearContext = () => { clearCtx(); setPage(0) }

  return (
    <div className="flex flex-col h-full">
      {/* Context selector bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 space-y-2">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="label">Evento de muestreo</label>
            <select
              className="input w-56"
              value={contextEventId}
              onChange={(e) => { changeEvent(e.target.value); setPage(0) }}
            >
              <option value="">Todos los eventos</option>
              {events.map((ev) => (
                <option key={ev.id} value={ev.id}>{ev.location_name} — {ev.start_date}</option>
              ))}
            </select>
          </div>

          {contextEventId && (
            <div>
              <label className="label">Réplica</label>
              <select
                className="input w-44"
                value={contextReplicateId}
                onChange={(e) => { setContextReplicateId(e.target.value); setPage(0) }}
                disabled={loadingReps}
              >
                <option value="">Todas las réplicas</option>
                {contextReplicates.map((r) => (
                  <option key={r.id} value={r.id}>{r.code}{r.method_label ? ` — ${r.method_label}` : ''}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="label">Desde</label>
            <input className="input w-36" type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
          </div>
          <div>
            <label className="label">Hasta</label>
            <input className="input w-36" type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
          </div>
          <div>
            <label className="label">Método</label>
            <select className="input w-40" value={filters.method_id} onChange={(e) => setFilters({ ...filters, method_id: e.target.value })}>
              <option value="">Todos</option>
              {methods.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          </div>
          {(contextEventId || filters.date_from || filters.date_to || filters.method_id) && (
            <button
              className="btn-secondary text-sm self-end"
              onClick={() => { clearContext(); setFilters({ date_from: '', date_to: '', method_id: '' }) }}
            >
              Limpiar
            </button>
          )}
          <div className="ml-auto self-end">
            <button className="btn-primary text-sm" onClick={openCreate}>+ Registro</button>
          </div>
        </div>

        {/* Active context banner */}
        {(activeEvent || activeReplicate) && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-primary-50 border border-primary-200 rounded-md text-sm">
            <span className="text-primary-600 font-medium">Contexto activo:</span>
            <span className="text-slate-700">{activeEvent?.location_name} — {activeEvent?.start_date}</span>
            {activeReplicate && (
              <>
                <span className="text-slate-400">›</span>
                <span className="font-mono font-semibold text-primary-700">Réplica {activeReplicate.code}</span>
                {activeReplicate.method_label && <span className="text-slate-500 text-xs">({activeReplicate.method_label})</span>}
              </>
            )}
            <button className="ml-auto text-slate-400 hover:text-slate-600 text-xs" onClick={clearContext}>✕ Quitar contexto</button>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <p className="text-slate-400 text-sm text-center py-12">Cargando…</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 sticky top-0">
              <tr>
                <th className="text-left px-4 py-2 font-medium text-slate-600">Taxón</th>
                <th className="text-left px-4 py-2 font-medium text-slate-600">Alias</th>
                <th className="text-right px-4 py-2 font-medium text-slate-600">Conteo</th>
                {!activeReplicate && <th className="text-left px-4 py-2 font-medium text-slate-600">Réplica</th>}
                <th className="text-left px-4 py-2 font-medium text-slate-600">Método</th>
                <th className="text-left px-4 py-2 font-medium text-slate-600">Fecha/hora</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr><td colSpan={activeReplicate ? 6 : 7} className="text-center text-slate-400 py-12 italic">Sin registros.</td></tr>
              ) : records.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 table-row-hover">
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      <TaxonAvatar mediaId={r.taxon_profile_media_id} name={r.taxon_name || ''} />
                      <span className="font-medium">{r.taxon_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2 text-slate-500 text-xs">{r.taxon_alias}</td>
                  <td className="px-4 py-2 text-right font-mono">{r.individual_count}</td>
                  {!activeReplicate && <td className="px-4 py-2 text-xs text-slate-500">Rep {r.replicate_id}</td>}
                  <td className="px-4 py-2 text-xs text-slate-500">{r.method_label || '—'}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">{r.date_time ? r.date_time.substring(0, 16) : '—'}</td>
                  <td className="px-4 py-2">
                    <div className="flex gap-1 justify-end">
                      <button className="btn-ghost text-xs" onClick={() => openEdit(r)}>✎</button>
                      <button className="btn-ghost text-xs text-red-500" onClick={() => setDeleteTarget(r)}>✕</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      <div className="bg-white border-t border-slate-200 px-6 py-2 flex items-center gap-3 text-sm text-slate-500">
        <button className="btn-ghost text-xs" disabled={page === 0} onClick={() => setPage(page - 1)}>← Anterior</button>
        <span>Página {page + 1}</span>
        <button className="btn-ghost text-xs" disabled={records.length < LIMIT} onClick={() => setPage(page + 1)}>Siguiente →</button>
        <span className="ml-4">{records.length} registros</span>
      </div>

      {/* Modals */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nuevo registro" size="lg">
        <RecordForm
          projectId={pid}
          taxa={taxa}
          methods={methods}
          replicates={allReplicates}
          lockedReplicate={activeReplicate}
          onSave={handleCreate}
          onClose={() => setShowCreate(false)}
        />
      </Modal>
      {editRecord && (
        <Modal isOpen={!!editRecord} onClose={() => setEditRecord(null)} title="Editar registro" size="lg">
          <RecordForm
            initial={editRecord}
            projectId={pid}
            taxa={taxa}
            methods={methods}
            replicates={allReplicates}
            lockedReplicate={activeReplicate}
            onSave={handleEdit}
            onClose={() => setEditRecord(null)}
          />
        </Modal>
      )}
      <ConfirmDialog isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDelete}
        title="Eliminar registro" message={`¿Eliminar el registro de "${deleteTarget?.taxon_name}"?`}
        confirmLabel="Eliminar" danger loading={deleting} />
    </div>
  )
}
