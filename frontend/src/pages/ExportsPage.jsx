import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'

function ExportButton({ href, label, description, variant = 'secondary' }) {
  return (
    <div className="card p-4 flex items-center justify-between">
      <div>
        <p className="font-medium text-slate-700">{label}</p>
        <p className="text-xs text-slate-400 mt-0.5">{description}</p>
      </div>
      <a href={href} download className={`btn-${variant} text-sm shrink-0 ml-4`}>
        ↓ Descargar
      </a>
    </div>
  )
}

export default function ExportsPage() {
  const { projectId } = useParams()
  const pid = Number(projectId)
  const [includePhotos, setIncludePhotos] = useState(false)
  const [backing, setBacking] = useState(false)
  const [backupMsg, setBackupMsg] = useState('')

  const handleBackup = async () => {
    setBacking(true); setBackupMsg('')
    try {
      const res = await api.manualBackup(pid)
      setBackupMsg(`Respaldo creado: ${res.backup_path}`)
    } catch (e) { setBackupMsg(`Error: ${e.message}`) } finally { setBacking(false) }
  }

  const qs = (extra = {}) => {
    const p = new URLSearchParams({ project_id: pid, ...extra })
    return '?' + p.toString()
  }

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <h2 className="text-xl font-bold text-slate-800">Exportar / Importar</h2>

      {/* CSV exports */}
      <section>
        <h3 className="font-semibold text-slate-600 mb-3">CSV (compatible con R)</h3>
        <div className="space-y-2">
          <ExportButton href={`/api/exports/csv/taxa${qs()}`} label="Taxa" description="Todos los taxa con jerarquía y alias" />
          <ExportButton href={`/api/exports/csv/locations${qs()}`} label="Localidades" description="Árbol de localidades con coordenadas" />
          <ExportButton href={`/api/exports/csv/events${qs()}`} label="Eventos de muestreo" description="Fechas y localidades" />
          <ExportButton href={`/api/exports/csv/replicates${qs()}`} label="Réplicas" description="Réplicas con método" />
          <ExportButton href={`/api/exports/csv/records${qs()}`} label="Registros de ocurrencia" description="Todos los registros con conteos" />
          <ExportButton href={`/api/exports/csv/methods${qs()}`} label="Métodos de colecta" description="Catálogo de métodos" />
          <ExportButton href={`/api/exports/csv/media${qs()}`} label="Medios / Fotos" description="Metadatos de archivos de medios" />
        </div>
      </section>

      {/* Matrix exports */}
      <section>
        <h3 className="font-semibold text-slate-600 mb-3">Matrices</h3>
        <div className="space-y-2">
          <ExportButton href={`/api/exports/csv/abundance-matrix${qs()}`} label="Matriz de abundancia" description="Réplicas × Taxa con conteos totales" />
          <ExportButton href={`/api/exports/csv/presence-absence-matrix${qs()}`} label="Matriz de presencia-ausencia" description="Réplicas × Taxa (0/1)" />
        </div>
      </section>

      {/* Excel */}
      <section>
        <h3 className="font-semibold text-slate-600 mb-3">Excel (todas las hojas)</h3>
        <ExportButton href={`/api/exports/excel${qs()}`} label="Libro Excel completo" description="Taxa, Localidades, Eventos, Réplicas, Registros, Métodos, Medios" variant="primary" />
      </section>

      {/* DwC-A */}
      <section>
        <h3 className="font-semibold text-slate-600 mb-3">Darwin Core Archive (DwC-A)</h3>
        <ExportButton
          href={`/api/exports/dwca${qs()}`}
          label="DwC-A ZIP"
          description="event.csv + occurrence.csv + taxon.csv + multimedia.csv + meta.xml"
          variant="primary"
        />
      </section>

      {/* Project ZIP */}
      <section>
        <h3 className="font-semibold text-slate-600 mb-3">Exportar proyecto completo</h3>
        <div className="card p-4 space-y-3">
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input type="checkbox" checked={includePhotos} onChange={(e) => setIncludePhotos(e.target.checked)} className="rounded" />
            Incluir fotos
          </label>
          <a
            href={`/api/exports/project${qs({ include_photos: includePhotos })}`}
            download
            className="btn-primary text-sm inline-block"
          >
            ↓ Descargar ZIP del proyecto
          </a>
          <p className="text-xs text-slate-400">Incluye base de datos + CSVs + (opcionalmente) carpeta de fotos.</p>
        </div>
      </section>

      {/* Backup */}
      <section>
        <h3 className="font-semibold text-slate-600 mb-3">Respaldo manual</h3>
        <div className="card p-4 space-y-2">
          <p className="text-sm text-slate-600">Crea una copia de la base de datos en la carpeta de respaldos local.</p>
          <button className="btn-secondary text-sm" onClick={handleBackup} disabled={backing}>
            {backing ? 'Creando…' : '💾 Crear respaldo ahora'}
          </button>
          {backupMsg && <p className={`text-xs ${backupMsg.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>{backupMsg}</p>}
        </div>
      </section>
    </div>
  )
}
