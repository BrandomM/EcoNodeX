import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useProject } from '../context/ProjectContext'

const NAV_ITEMS = [
  { to: 'taxa',      label: 'Taxa',         icon: '🦋' },
  { to: 'locations', label: 'Localidades',  icon: '📍' },
  { to: 'sampling',  label: 'Muestreos',    icon: '🧪' },
  { to: 'records',   label: 'Registros',    icon: '📋' },
  { to: 'analyses',  label: 'Análisis',     icon: '📊' },
  { to: 'exports',   label: 'Exportar',     icon: '💾' },
  { to: 'settings',  label: 'Ajustes',      icon: '⚙️' },
]

export default function Layout({ children }) {
  const { currentProject, projects, selectProject } = useProject()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-52' : 'w-14'} flex-shrink-0 bg-slate-900 text-white flex flex-col transition-all duration-200`}>
        {/* Logo / toggle */}
        <div className="flex items-center gap-2 px-3 py-4 border-b border-slate-700">
          <span className="text-primary-400 text-xl">🌿</span>
          {sidebarOpen && (
            <span className="font-bold text-sm tracking-wide text-primary-300">EcoNodeX</span>
          )}
          <button
            className="ml-auto text-slate-400 hover:text-white text-lg"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? '◂' : '▸'}
          </button>
        </div>

        {/* Project selector */}
        {sidebarOpen && (
          <div className="px-3 py-3 border-b border-slate-700">
            <p className="text-xs text-slate-400 mb-1">Proyecto</p>
            <select
              className="w-full bg-slate-800 text-white text-xs rounded px-2 py-1 border border-slate-600 focus:outline-none focus:border-primary-500"
              value={currentProject?.id ?? ''}
              onChange={(e) => {
                const p = projects.find((p) => p.id === Number(e.target.value))
                if (p) { selectProject(p); navigate(`/projects/${p.id}/taxa`) }
                else { navigate('/') }
              }}
            >
              <option value="">— Seleccionar —</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 py-3">
          {NAV_ITEMS.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={currentProject ? `/projects/${currentProject.id}/${to}` : '/'}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 text-sm transition-colors
                 ${isActive ? 'bg-primary-700 text-white' : 'text-slate-300 hover:bg-slate-700 hover:text-white'}`
              }
              title={label}
            >
              <span className="text-base">{icon}</span>
              {sidebarOpen && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-slate-700">
          <button
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-white w-full"
            onClick={() => navigate('/')}
            title="Cambiar proyecto"
          >
            <span>🔀</span>
            {sidebarOpen && <span>Cambiar proyecto</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
