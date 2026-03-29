import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'

function EventForm({ initial = {}, projectId, locations = [], onSave, onClose }) {
  const [form, setForm] = useState({
    project_id: projectId,
    location_id: initial.location_id || '',
    start_date: initial.start_date || '',
    end_date: initial.end_date || '',
    description: initial.description || '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.location_id) { setError('Selecciona una localidad.'); return }
    if (!form.start_date) { setError('Fecha de inicio requerida.'); return }
    setSaving(true)
    try { await onSave({ ...form, location_id: Number(form.location_id) }); onClose() }
    catch (e) { setError(e.message) } finally { setSaving(false) }
  }
  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div>
        <label className="label">Localidad *</label>
        <select className="input" value={form.location_id} onChange={(e) => setForm({ ...form, location_id: e.target.value })} required>
          <option value="">— Seleccionar —</option>
          {locations.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Fecha inicio *</label>
          <input className="input" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} required />
        </div>
        <div>
          <label className="label">Fecha fin</label>
          <input className="input" type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
        </div>
      </div>
      <div>
        <label className="label">Descripción</label>
        <textarea className="input h-16 resize-none" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </div>
    </form>
  )
}

function ReplicateForm({ initial = {}, eventId, methods = [], onSave, onClose }) {
  const [form, setForm] = useState({
    event_id: eventId,
    code: initial.code || '',
    method_id: initial.method_id || '',
    notes: initial.notes || '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.code.trim()) { setError('Código requerido.'); return }
    setSaving(true)
    try { await onSave({ ...form, method_id: form.method_id ? Number(form.method_id) : null }); onClose() }
    catch (e) { setError(e.message) } finally { setSaving(false) }
  }
  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="label">Código *</label>
          <input className="input" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="R1, R2…" required />
        </div>
        <div>
          <label className="label">Método</label>
          <select className="input" value={form.method_id} onChange={(e) => setForm({ ...form, method_id: e.target.value })}>
            <option value="">— Ninguno —</option>
            {methods.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </div>
        <div className="col-span-2">
          <label className="label">Notas</label>
          <input className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </div>
    </form>
  )
}

export default function SamplingPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)

  const [events, setEvents] = useState([])
  const [locations, setLocations] = useState([])
  const [methods, setMethods] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState(null)
  const [replicates, setReplicates] = useState([])
  const [showCreateEvent, setShowCreateEvent] = useState(false)
  const [editEvent, setEditEvent] = useState(null)
  const [deleteEvent, setDeleteEvent] = useState(null)
  const [showCreateRep, setShowCreateRep] = useState(false)
  const [editRep, setEditRep] = useState(null)
  const [deleteRep, setDeleteRep] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const [evs, locs, meths] = await Promise.all([
      api.getEvents(pid),
      api.getLocations(pid),
      api.getMethods(pid),
    ])
    setEvents(evs)
    setLocations(locs)
    setMethods(meths)
    setLoading(false)
  }, [pid])

  useEffect(() => { load() }, [load])

  const loadReps = async (ev) => {
    setSelectedEvent(ev)
    const reps = await api.getReplicates(ev.id)
    setReplicates(reps)
  }

  const handleCreateEvent = async (form) => { await api.createEvent(form); await load() }
  const handleEditEvent   = async (form) => { await api.updateEvent(editEvent.id, form); await load() }
  const handleDeleteEvent = async () => {
    setDeleting(true)
    try { await api.deleteEvent(deleteEvent.id); await load(); setSelectedEvent(null); setDeleteEvent(null) }
    catch (e) { alert(e.message) } finally { setDeleting(false) }
  }

  const handleCreateRep = async (form) => { await api.createReplicate(form); await loadReps(selectedEvent) }
  const handleEditRep   = async (form) => { await api.updateReplicate(editRep.id, form); await loadReps(selectedEvent) }
  const handleDeleteRep = async () => {
    setDeleting(true)
    try { await api.deleteReplicate(deleteRep.id); await loadReps(selectedEvent); setDeleteRep(null) }
    catch (e) { alert(e.message) } finally { setDeleting(false) }
  }

  return (
    <div className="flex h-full">
      {/* Events list */}
      <div className="w-80 border-r border-slate-200 flex flex-col bg-white">
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
          <h2 className="font-semibold text-slate-700">Eventos de muestreo</h2>
          <button className="btn-primary text-xs" onClick={() => setShowCreateEvent(true)}>+ Evento</button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading ? <p className="text-sm text-slate-400 p-4">Cargando…</p> : events.length === 0 ? (
            <p className="text-sm text-slate-400 italic p-4">Sin eventos.</p>
          ) : events.map((ev) => (
            <div
              key={ev.id}
              className={`px-4 py-3 cursor-pointer border-b border-slate-100 hover:bg-slate-50 group
                ${selectedEvent?.id === ev.id ? 'bg-primary-50 border-l-2 border-primary-500' : ''}`}
              onClick={() => loadReps(ev)}
            >
              <p className="text-sm font-medium text-slate-800">{ev.location_name || `Localidad ${ev.location_id}`}</p>
              <p className="text-xs text-slate-500">{ev.start_date}{ev.end_date ? ` → ${ev.end_date}` : ''}</p>
              <div className="flex gap-2 items-center mt-1">
                <span className="badge-slate text-xs">{ev.replicate_count} réplica(s)</span>
                <span className="hidden group-hover:flex gap-1 ml-auto">
                  <button className="text-xs text-slate-400 hover:text-primary-600" onClick={(e) => { e.stopPropagation(); setEditEvent(ev) }}>✎</button>
                  <button className="text-xs text-slate-400 hover:text-red-600" onClick={(e) => { e.stopPropagation(); setDeleteEvent(ev) }}>✕</button>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Replicates */}
      <div className="flex-1 p-6 overflow-y-auto">
        {selectedEvent ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-800">
                  {selectedEvent.location_name} — {selectedEvent.start_date}
                </h2>
                {selectedEvent.description && <p className="text-sm text-slate-500 mt-1">{selectedEvent.description}</p>}
              </div>
              <button className="btn-primary text-sm" onClick={() => setShowCreateRep(true)}>+ Réplica</button>
            </div>
            {replicates.length === 0 ? (
              <div className="card p-8 text-center text-slate-400">
                <p>No hay réplicas. Agrega la primera con el botón + Réplica.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {replicates.map((rep) => (
                  <div key={rep.id} className="card p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-bold text-primary-700 text-lg">{rep.code}</span>
                      <div className="flex gap-1">
                        <button className="btn-ghost text-xs" onClick={() => setEditRep(rep)}>✎</button>
                        <button className="btn-ghost text-xs text-red-500" onClick={() => setDeleteRep(rep)}>✕</button>
                      </div>
                    </div>
                    {rep.method_label && <p className="text-xs text-slate-500 mb-1">Método: {rep.method_label}</p>}
                    {rep.notes && <p className="text-xs text-slate-500 mb-2 italic">{rep.notes}</p>}
                    <p className="text-xs text-slate-400">{rep.record_count} registro(s)</p>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <p className="text-5xl mb-4">🧪</p>
            <p className="text-lg font-medium">Selecciona un evento de muestreo</p>
          </div>
        )}
      </div>

      {/* Modals */}
      <Modal isOpen={showCreateEvent} onClose={() => setShowCreateEvent(false)} title="Nuevo evento">
        <EventForm projectId={pid} locations={locations} onSave={handleCreateEvent} onClose={() => setShowCreateEvent(false)} />
      </Modal>
      {editEvent && (
        <Modal isOpen={!!editEvent} onClose={() => setEditEvent(null)} title="Editar evento">
          <EventForm initial={editEvent} projectId={pid} locations={locations} onSave={handleEditEvent} onClose={() => setEditEvent(null)} />
        </Modal>
      )}
      {selectedEvent && (
        <>
          <Modal isOpen={showCreateRep} onClose={() => setShowCreateRep(false)} title="Nueva réplica">
            <ReplicateForm eventId={selectedEvent.id} methods={methods} onSave={handleCreateRep} onClose={() => setShowCreateRep(false)} />
          </Modal>
          {editRep && (
            <Modal isOpen={!!editRep} onClose={() => setEditRep(null)} title="Editar réplica">
              <ReplicateForm initial={editRep} eventId={selectedEvent.id} methods={methods} onSave={handleEditRep} onClose={() => setEditRep(null)} />
            </Modal>
          )}
        </>
      )}
      <ConfirmDialog isOpen={!!deleteEvent} onClose={() => setDeleteEvent(null)} onConfirm={handleDeleteEvent}
        title="Eliminar evento" message={`¿Eliminar el evento del ${deleteEvent?.start_date}? Se eliminarán sus réplicas y registros.`}
        confirmLabel="Eliminar" danger loading={deleting} />
      <ConfirmDialog isOpen={!!deleteRep} onClose={() => setDeleteRep(null)} onConfirm={handleDeleteRep}
        title="Eliminar réplica" message={`¿Eliminar la réplica "${deleteRep?.code}"? Se eliminarán sus registros.`}
        confirmLabel="Eliminar" danger loading={deleting} />
    </div>
  )
}
