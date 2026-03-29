import React, { useEffect } from 'react'
import { Routes, Route, Navigate, useParams } from 'react-router-dom'
import { ProjectProvider, useProject } from './context/ProjectContext'
import Layout from './components/Layout'

import ProjectsPage  from './pages/ProjectsPage'
import TaxaPage      from './pages/TaxaPage'
import LocationsPage from './pages/LocationsPage'
import SamplingPage  from './pages/SamplingPage'
import RecordsPage   from './pages/RecordsPage'
import AnalysesPage  from './pages/AnalysesPage'
import ExportsPage   from './pages/ExportsPage'
import SettingsPage  from './pages/SettingsPage'
import UploadPage    from './pages/UploadPage'

function ProjectRoutes() {
  const { loadProjects } = useProject()

  useEffect(() => { loadProjects() }, [loadProjects])

  return (
    <Routes>
      <Route path="/" element={<ProjectsPage />} />
      <Route path="/upload" element={<UploadPage />} />
      <Route path="/projects/:projectId/*" element={
        <Layout>
          <ProjectInner />
        </Layout>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function ProjectInner() {
  const { currentProject, projects, selectProject } = useProject()
  const { projectId } = useParams()

  // Sync URL projectId → context when projects list is loaded
  useEffect(() => {
    if (!currentProject || currentProject.id !== Number(projectId)) {
      const p = projects.find((p) => p.id === Number(projectId))
      if (p) selectProject(p)
    }
  }, [projectId, projects, currentProject, selectProject])

  return (
    <Routes>
      <Route path="taxa"      element={<TaxaPage />} />
      <Route path="locations" element={<LocationsPage />} />
      <Route path="sampling"  element={<SamplingPage />} />
      <Route path="records"   element={<RecordsPage />} />
      <Route path="analyses"  element={<AnalysesPage />} />
      <Route path="exports"   element={<ExportsPage />} />
      <Route path="settings"  element={<SettingsPage />} />
      <Route path="*"         element={<Navigate to="taxa" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ProjectProvider>
      <ProjectRoutes />
    </ProjectProvider>
  )
}
