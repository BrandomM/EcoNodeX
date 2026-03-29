import React, { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import TreeView from '../components/TreeView'
import PhotoGallery from '../components/PhotoGallery'

function LocationForm({ initial = {}, projectId, locations = [], onSave, onClose }) {
  const [form, setForm] = useState({
    project_id: projectId,
    name: initial.name || '',
    type: initial.type || '',
    latitude: initial.latitude ?? '',
    longitude: initial.longitude ?? '',
    altitude: initial.altitude ?? '',
    parent_location_id: initial.parent_location_id || '',
    description: initial.description || '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) { setError('El nombre es obligatorio.'); return }
    setSaving(true)
    try {
      const payload = {
        ...form,
        parent_location_id: form.parent_location_id ? Number(form.parent_location_id) : null,
        latitude:  form.latitude  !== '' ? Number(form.latitude)  : null,
        longitude: form.longitude !== '' ? Number(form.longitude) : null,
        altitude:  form.altitude  !== '' ? Number(form.altitude)  : null,
      }
      await onSave(payload)
      onClose()
    } catch (e) { setError(e.message) } finally { setSaving(false) }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="label">Nombre *</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </div>
        <div>
          <label className="label">Tipo / Nivel</label>
          <input className="input" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} placeholder="región, localidad, punto…" />
        </div>
        <div>
          <label className="label">Localidad padre</label>
          <select className="input" value={form.parent_location_id} onChange={(e) => setForm({ ...form, parent_location_id: e.target.value })}>
            <option value="">— Sin padre —</option>
            {locations.filter((l) => l.id !== initial.id).map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Latitud</label>
          <input className="input" type="number" step="any" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} />
        </div>
        <div>
          <label className="label">Longitud</label>
          <input className="input" type="number" step="any" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} />
        </div>
        <div>
          <label className="label">Altitud (m.s.n.m.)</label>
          <input className="input" type="number" step="any" value={form.altitude} onChange={(e) => setForm({ ...form, altitude: e.target.value })} />
        </div>
        <div className="col-span-2">
          <label className="label">Descripción</label>
          <textarea className="input h-16 resize-none" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </div>
    </form>
  )
}

export default function LocationsPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)

  const [treeData, setTreeData] = useState([])
  const [flatData, setFlatData] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editLoc, setEditLoc] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [media, setMedia] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [tree, flat] = await Promise.all([
        api.getLocations(pid, true),
        api.getLocations(pid, false),
      ])
      setTreeData(tree)
      setFlatData(flat)
    } finally { setLoading(false) }
  }, [pid])

  useEffect(() => { load() }, [load])

  const handleSelect = async (loc) => {
    setSelected(loc)
    const m = await api.getMedia(pid, 'location', loc.id)
    setMedia(m)
  }

  const handleCreate = async (form) => { await api.createLocation(form); await load() }
  const handleEdit   = async (form) => { await api.updateLocation(editLoc.id, form); await load() }
  const handleDelete = async () => {
    setDeleting(true)
    try { await api.deleteLocation(deleteTarget.id); await load(); setSelected(null); setDeleteTarget(null) }
    catch (e) { alert(e.message) } finally { setDeleting(false) }
  }

  const handleSetProfile = async (m) => {
    await api.updateMedia(m.id, { is_profile: true, linked_to_type: 'location', linked_to_id: selected.id })
    handleSelect(selected)
  }
  const handleDeleteMedia = async (m) => {
    if (!confirm(`¿Eliminar "${m.file_name}"?`)) return
    await api.deleteMedia(m.id)
    handleSelect(selected)
  }

  return (
    <div className="flex h-full">
      <div className="w-72 border-r border-slate-200 flex flex-col bg-white">
        <div className="px-4 py-3 border-b border-slate-200">
          <h2 className="font-semibold text-slate-700">Localidades</h2>
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          {loading ? <p className="text-sm text-slate-400 p-4 text-center">Cargando…</p> : (
            <TreeView
              nodes={treeData}
              labelKey="name"
              onSelect={handleSelect}
              onEdit={setEditLoc}
              onDelete={setDeleteTarget}
              selectedId={selected?.id}
            />
          )}
        </div>
        <div className="px-4 py-3 border-t border-slate-200">
          <button className="btn-primary w-full text-sm" onClick={() => setShowCreate(true)}>+ Localidad</button>
        </div>
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        {selected ? (
          <>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-slate-800">{selected.name}</h2>
                {selected.type && <span className="badge-blue mt-1">{selected.type}</span>}
                <div className="flex gap-4 mt-2 text-sm text-slate-500">
                  {selected.latitude  != null && <span>Lat: {selected.latitude.toFixed(5)}</span>}
                  {selected.longitude != null && <span>Lon: {selected.longitude.toFixed(5)}</span>}
                  {selected.altitude  != null && <span>Alt: {selected.altitude} m</span>}
                </div>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary text-sm" onClick={() => setEditLoc(selected)}>✎ Editar</button>
                <button className="btn text-sm text-red-600 hover:bg-red-50 border border-red-200" onClick={() => setDeleteTarget(selected)}>Eliminar</button>
              </div>
            </div>
            {selected.description && <p className="text-sm text-slate-600 mb-4 bg-slate-50 p-3 rounded">{selected.description}</p>}
            <h3 className="font-medium text-slate-700 mb-2">Fotos</h3>
            <PhotoGallery media={media} onSetProfile={handleSetProfile} onDelete={handleDeleteMedia} />
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <p className="text-5xl mb-4">📍</p>
            <p className="text-lg font-medium">Selecciona una localidad</p>
          </div>
        )}
      </div>

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nueva localidad">
        <LocationForm projectId={pid} locations={flatData} onSave={handleCreate} onClose={() => setShowCreate(false)} />
      </Modal>
      {editLoc && (
        <Modal isOpen={!!editLoc} onClose={() => setEditLoc(null)} title="Editar localidad">
          <LocationForm initial={editLoc} projectId={pid} locations={flatData} onSave={handleEdit} onClose={() => setEditLoc(null)} />
        </Modal>
      )}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Eliminar localidad"
        message={`¿Eliminar "${deleteTarget?.name}"?`}
        confirmLabel="Eliminar"
        danger
        loading={deleting}
      />
    </div>
  )
}
