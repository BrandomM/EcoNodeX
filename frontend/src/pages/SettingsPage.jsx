import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import { useProject } from '../context/ProjectContext'

export default function SettingsPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)
  const { loadProjects } = useProject()

  const [project, setProject] = useState(null)
  const [photosPath, setPhotosPath] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  // Methods catalog
  const [methods, setMethods] = useState([])
  const [newMethod, setNewMethod] = useState({ code: '', label: '', description: '' })
  const [editMethod, setEditMethod] = useState(null)
  const [savingMethod, setSavingMethod] = useState(false)

  useEffect(() => {
    api.getProjects().then((projs) => {
      const p = projs.find((p) => p.id === pid)
      if (p) { setProject(p); setPhotosPath(p.photos_root_path || '') }
    })
    api.getMethods(pid).then(setMethods)
  }, [pid])

  const handleSavePhotos = async () => {
    setSaving(true); setMsg('')
    try {
      await api.updateProject(pid, { photos_root_path: photosPath })
      await loadProjects()
      setMsg('Ruta de fotos guardada.')
    } catch (e) { setMsg(`Error: ${e.message}`) } finally { setSaving(false) }
  }

  const handleAddMethod = async () => {
    if (!newMethod.code || !newMethod.label) return
    setSavingMethod(true)
    try {
      await api.createMethod({ ...newMethod, project_id: pid })
      setNewMethod({ code: '', label: '', description: '' })
      setMethods(await api.getMethods(pid))
    } finally { setSavingMethod(false) }
  }

  const handleSaveMethod = async () => {
    setSavingMethod(true)
    try {
      await api.updateMethod(editMethod.id, { code: editMethod.code, label: editMethod.label, description: editMethod.description })
      setEditMethod(null)
      setMethods(await api.getMethods(pid))
    } finally { setSavingMethod(false) }
  }

  const handleDeleteMethod = async (id) => {
    if (!confirm('¿Eliminar método?')) return
    await api.deleteMethod(id)
    setMethods(await api.getMethods(pid))
  }

  return (
    <div className="p-6 max-w-2xl space-y-8">
      <h2 className="text-xl font-bold text-slate-800">Ajustes del proyecto</h2>

      {/* Photos folder */}
      <section className="card p-5 space-y-3">
        <h3 className="font-semibold text-slate-700">Carpeta de fotos</h3>
        <p className="text-sm text-slate-500">
          Ruta local donde se guardarán las fotos subidas desde el móvil y asociadas al proyecto.
        </p>
        <div className="flex gap-2">
          <input
            className="input flex-1 font-mono text-xs"
            value={photosPath}
            onChange={(e) => setPhotosPath(e.target.value)}
            placeholder="C:\Usuarios\...\Fotos\MiProyecto"
          />
          <button className="btn-primary" onClick={handleSavePhotos} disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar'}
          </button>
        </div>
        {msg && <p className={`text-xs ${msg.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>{msg}</p>}
      </section>

      {/* Methods catalog */}
      <section className="card p-5 space-y-3">
        <h3 className="font-semibold text-slate-700">Catálogo de métodos de colecta</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-1 font-medium text-slate-600">Código</th>
              <th className="text-left py-1 font-medium text-slate-600">Etiqueta</th>
              <th className="text-left py-1 font-medium text-slate-600">Descripción</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {methods.map((m) => (
              <tr key={m.id} className="border-b border-slate-100">
                {editMethod?.id === m.id ? (
                  <>
                    <td className="py-1"><input className="input text-xs" value={editMethod.code} onChange={(e) => setEditMethod({ ...editMethod, code: e.target.value })} /></td>
                    <td className="py-1"><input className="input text-xs" value={editMethod.label} onChange={(e) => setEditMethod({ ...editMethod, label: e.target.value })} /></td>
                    <td className="py-1"><input className="input text-xs" value={editMethod.description || ''} onChange={(e) => setEditMethod({ ...editMethod, description: e.target.value })} /></td>
                    <td className="py-1 flex gap-1">
                      <button className="btn-primary text-xs" onClick={handleSaveMethod} disabled={savingMethod}>✓</button>
                      <button className="btn-secondary text-xs" onClick={() => setEditMethod(null)}>✕</button>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="py-1 font-mono text-xs">{m.code}</td>
                    <td className="py-1">{m.label}</td>
                    <td className="py-1 text-slate-400 text-xs">{m.description}</td>
                    <td className="py-1">
                      <div className="flex gap-1">
                        <button className="btn-ghost text-xs" onClick={() => setEditMethod({ ...m })}>✎</button>
                        <button className="btn-ghost text-xs text-red-500" onClick={() => handleDeleteMethod(m.id)}>✕</button>
                      </div>
                    </td>
                  </>
                )}
              </tr>
            ))}
            {/* Add row */}
            <tr>
              <td className="py-2"><input className="input text-xs" placeholder="COD" value={newMethod.code} onChange={(e) => setNewMethod({ ...newMethod, code: e.target.value })} /></td>
              <td className="py-2"><input className="input text-xs" placeholder="Etiqueta" value={newMethod.label} onChange={(e) => setNewMethod({ ...newMethod, label: e.target.value })} /></td>
              <td className="py-2"><input className="input text-xs" placeholder="Descripción (opcional)" value={newMethod.description} onChange={(e) => setNewMethod({ ...newMethod, description: e.target.value })} /></td>
              <td className="py-2">
                <button className="btn-primary text-xs" onClick={handleAddMethod} disabled={savingMethod || !newMethod.code || !newMethod.label}>+ Añadir</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* App info */}
      <section className="card p-5 space-y-1">
        <h3 className="font-semibold text-slate-700 mb-2">Acerca de EcoNodeX</h3>
        <p className="text-sm text-slate-500">Versión MVP #1</p>
        <p className="text-sm text-slate-500">Aplicación local de escritorio — sin cloud, sin autenticación.</p>
        <p className="text-xs text-slate-400 mt-2">
          ⚠ La subida de fotos por QR está pensada para uso en red local (LAN). No expongas el servidor a Internet.
        </p>
      </section>
    </div>
  )
}
