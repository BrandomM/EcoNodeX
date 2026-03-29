import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProject } from '../context/ProjectContext'
import api from '../api/client'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'

function ProjectForm({ initial = {}, onSave, onClose }) {
  const [form, setForm] = useState({
    name: initial.name || '',
    description: initial.description || '',
    photos_root_path: initial.photos_root_path || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) { setError('El nombre es obligatorio.'); return }
    setSaving(true)
    try {
      await onSave(form)
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div>
        <label className="label">Nombre *</label>
        <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
      </div>
      <div>
        <label className="label">Descripción</label>
        <textarea className="input h-20 resize-none" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
      </div>
      <div>
        <label className="label">Carpeta de fotos (ruta local)</label>
        <input className="input font-mono text-xs" value={form.photos_root_path} onChange={(e) => setForm({ ...form, photos_root_path: e.target.value })} placeholder="C:\Fotos\MiProyecto" />
        <p className="text-xs text-slate-400 mt-1">También se puede cambiar en Ajustes.</p>
      </div>
      <div className="flex gap-2 justify-end pt-2">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancelar</button>
        <button type="submit" className="btn-primary" disabled={saving}>{saving ? 'Guardando…' : 'Guardar'}</button>
      </div>
    </form>
  )
}

export default function ProjectsPage() {
  const { projects, loadProjects, selectProject } = useProject()
  const navigate = useNavigate()
  const [showCreate, setShowCreate] = useState(false)
  const [editProject, setEditProject] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadProjects() }, [loadProjects])

  const open = (project) => {
    selectProject(project)
    navigate(`/projects/${project.id}/taxa`)
  }

  const handleCreate = async (form) => {
    await api.createProject(form)
    await loadProjects()
  }

  const handleEdit = async (form) => {
    await api.updateProject(editProject.id, form)
    await loadProjects()
  }

  const handleDelete = async () => {
    setLoading(true)
    try {
      await api.deleteProject(deleteTarget.id)
      await loadProjects()
      setDeleteTarget(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-slate-100 flex flex-col">
      {/* Header */}
      <header className="bg-slate-900 text-white px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🌿</span>
          <div>
            <h1 className="text-xl font-bold text-primary-300">EcoNodeX</h1>
            <p className="text-xs text-slate-400">Gestión local de datos ecológicos</p>
          </div>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>+ Nuevo proyecto</button>
      </header>

      <main className="flex-1 px-8 py-8">
        <h2 className="text-lg font-semibold text-slate-700 mb-4">Proyectos</h2>
        {projects.length === 0 ? (
          <div className="card p-12 text-center text-slate-400">
            <p className="text-5xl mb-4">🗂️</p>
            <p className="font-medium text-slate-600">No hay proyectos todavía.</p>
            <p className="text-sm mt-1">Crea tu primer proyecto para comenzar.</p>
            <button className="btn-primary mt-4" onClick={() => setShowCreate(true)}>Crear proyecto</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <div
                key={p.id}
                className="card p-5 cursor-pointer hover:shadow-md hover:border-primary-300 transition-all group"
                onClick={() => open(p)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-800 truncate group-hover:text-primary-700">{p.name}</h3>
                    {p.description && <p className="text-sm text-slate-500 mt-1 line-clamp-2">{p.description}</p>}
                    <p className="text-xs text-slate-400 mt-2">
                      Creado {new Date(p.created_at).toLocaleDateString('es')}
                    </p>
                  </div>
                  <span className="text-primary-400 text-2xl ml-2">▶</span>
                </div>
                <div className="flex gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    className="btn-secondary text-xs"
                    onClick={(e) => { e.stopPropagation(); setEditProject(p) }}
                  >✎ Editar</button>
                  <button
                    className="btn text-xs text-red-600 hover:bg-red-50 border border-red-200"
                    onClick={(e) => { e.stopPropagation(); setDeleteTarget(p) }}
                  >✕ Eliminar</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <footer className="px-8 py-3 text-xs text-slate-400 border-t border-slate-200">
        Solo LAN · Sin autenticación por diseño (MVP #1) · Los datos se almacenan localmente.
      </footer>

      {/* Create modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Nuevo proyecto">
        <ProjectForm onSave={handleCreate} onClose={() => setShowCreate(false)} />
      </Modal>

      {/* Edit modal */}
      {editProject && (
        <Modal isOpen={!!editProject} onClose={() => setEditProject(null)} title="Editar proyecto">
          <ProjectForm initial={editProject} onSave={handleEdit} onClose={() => setEditProject(null)} />
        </Modal>
      )}

      {/* Delete confirm */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Eliminar proyecto"
        message={`¿Eliminar "${deleteTarget?.name}"? Se borrarán todos los datos del proyecto (taxa, muestreos, registros). Esta acción no se puede deshacer.`}
        confirmLabel="Eliminar"
        danger
        loading={loading}
      />
    </div>
  )
}
