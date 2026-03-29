import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'

function RecordForm({ initial = {}, projectId, taxa = [], methods = [], replicates = [], onSave, onClose }) {
  const [form, setForm] = useState({
    replicate_id: initial.replicate_id || '',
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
          <select className="input" value={form.replicate_id} onChange={(e) => setForm({ ...form, replicate_id: e.target.value })} required>
            <option value="">— Seleccionar —</option>
            {replicates.map((r) => <option key={r.id} value={r.id}>{r.code} (E{r.event_id})</option>)}
          </select>
        </div>
        <div>
          <label className="label">Taxón *</label>
          <select className="input" value={form.taxon_id} onChange={(e) => setForm({ ...form, taxon_id: e.target.value })} required>
            <option value="">— Seleccionar —</option>
            {taxa.map((t) => <option key={t.id} value={t.id}>{t.alias || t.scientific_name}</option>)}
          </select>
        </div>
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

  const [records, setRecords] = useState([])
  const [taxa, setTaxa] = useState([])
  const [methods, setMethods] = useState([])
  const [events, setEvents] = useState([])
  const [allReplicates, setAllReplicates] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ date_from: '', date_to: '', method_id: '', event_id: '' })
  const [showCreate, setShowCreate] = useState(false)
  const [editRecord, setEditRecord] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [page, setPage] = useState(0)
  const LIMIT = 100

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [recs, tx, meth, evs] = await Promise.all([
        api.getRecords(pid, { ...Object.fromEntries(Object.entries(filters).filter(([,v]) => v)), skip: page * LIMIT, limit: LIMIT }),
        api.getTaxa(pid),
        api.getMethods(pid),
        api.getEvents(pid),
      ])
      setRecords(recs)
      setTaxa(tx)
      setMethods(meth)
      setEvents(evs)
    } finally { setLoading(false) }
  }, [pid, filters, page])

  useEffect(() => { load() }, [load])

  // Load all replicates for the form (across all events)
  const loadReplicates = async () => {
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

  const openCreate = async () => { await loadReplicates(); setShowCreate(true) }
  const openEdit   = async (r)  => { await loadReplicates(); setEditRecord(r) }

  return (
    <div className="flex flex-col h-full">
      {/* Filters bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap gap-3 items-end">
        <div>
          <label className="label">Desde</label>
          <input className="input w-36" type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
        </div>
        <div>
          <label className="label">Hasta</label>
          <input className="input w-36" type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
        </div>
        <div>
          <label className="label">Evento</label>
          <select className="input w-48" value={filters.event_id} onChange={(e) => setFilters({ ...filters, event_id: e.target.value })}>
            <option value="">Todos</option>
            {events.map((ev) => <option key={ev.id} value={ev.id}>{ev.location_name} {ev.start_date}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Método</label>
          <select className="input w-40" value={filters.method_id} onChange={(e) => setFilters({ ...filters, method_id: e.target.value })}>
            <option value="">Todos</option>
            {methods.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </div>
        <button className="btn-secondary text-sm" onClick={() => setFilters({ date_from: '', date_to: '', method_id: '', event_id: '' })}>
          Limpiar
        </button>
        <div className="ml-auto">
          <button className="btn-primary text-sm" onClick={openCreate}>+ Registro</button>
        </div>
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
                <th className="text-left px-4 py-2 font-medium text-slate-600">Réplica</th>
                <th className="text-left px-4 py-2 font-medium text-slate-600">Método</th>
                <th className="text-left px-4 py-2 font-medium text-slate-600">Fecha/hora</th>
                <th className="px-4 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr><td colSpan={7} className="text-center text-slate-400 py-12 italic">Sin registros.</td></tr>
              ) : records.map((r) => (
                <tr key={r.id} className="border-b border-slate-100 table-row-hover">
                  <td className="px-4 py-2 font-medium">{r.taxon_name}</td>
                  <td className="px-4 py-2 text-slate-500 text-xs">{r.taxon_alias}</td>
                  <td className="px-4 py-2 text-right font-mono">{r.individual_count}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">Rep {r.replicate_id}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">{r.method_label || '—'}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">{r.date_time ? r.date_time.substring(0,16) : '—'}</td>
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
        <RecordForm projectId={pid} taxa={taxa} methods={methods} replicates={allReplicates} onSave={handleCreate} onClose={() => setShowCreate(false)} />
      </Modal>
      {editRecord && (
        <Modal isOpen={!!editRecord} onClose={() => setEditRecord(null)} title="Editar registro" size="lg">
          <RecordForm initial={editRecord} projectId={pid} taxa={taxa} methods={methods} replicates={allReplicates} onSave={handleEdit} onClose={() => setEditRecord(null)} />
        </Modal>
      )}
      <ConfirmDialog isOpen={!!deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={handleDelete}
        title="Eliminar registro" message={`¿Eliminar el registro de "${deleteTarget?.taxon_name}"?`}
        confirmLabel="Eliminar" danger loading={deleting} />
    </div>
  )
}
