import React, { createContext, useContext, useState, useCallback } from 'react'
import api from '../api/client'

const ProjectContext = createContext(null)

export function ProjectProvider({ children }) {
  const [currentProject, setCurrentProject] = useState(null)
  const [projects, setProjects] = useState([])

  const loadProjects = useCallback(async () => {
    const list = await api.getProjects()
    setProjects(list)
    return list
  }, [])

  const selectProject = useCallback((project) => {
    setCurrentProject(project)
  }, [])

  return (
    <ProjectContext.Provider value={{ currentProject, projects, loadProjects, selectProject, setProjects }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  const ctx = useContext(ProjectContext)
  if (!ctx) throw new Error('useProject must be inside ProjectProvider')
  return ctx
}
