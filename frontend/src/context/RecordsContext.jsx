import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/client'

const RecordsContext = createContext(null)

export function RecordsProvider({ children }) {
  const [contextEventId, setContextEventId] = useState('')
  const [contextReplicateId, setContextReplicateId] = useState('')
  const [contextReplicates, setContextReplicates] = useState([])
  const [filters, setFilters] = useState({ date_from: '', date_to: '', method_id: '' })
  const [loadingReps, setLoadingReps] = useState(false)

  // When the active project changes (URL), reset everything
  // RecordsPage passes projectId here via setProject
  const [projectId, setProject] = useState(null)

  useEffect(() => {
    setContextEventId('')
    setContextReplicateId('')
    setContextReplicates([])
    setFilters({ date_from: '', date_to: '', method_id: '' })
  }, [projectId])

  // When contextEventId changes, load its replicates
  useEffect(() => {
    if (!contextEventId) { setContextReplicates([]); setContextReplicateId(''); return }
    setLoadingReps(true)
    api.getReplicates(Number(contextEventId))
      .then((reps) => { setContextReplicates(reps); })
      .finally(() => setLoadingReps(false))
  }, [contextEventId])

  const changeEvent = (eventId) => {
    setContextEventId(eventId)
    setContextReplicateId('')
  }

  const clearContext = () => {
    setContextEventId('')
    setContextReplicateId('')
    setContextReplicates([])
  }

  return (
    <RecordsContext.Provider value={{
      contextEventId, changeEvent,
      contextReplicateId, setContextReplicateId,
      contextReplicates, loadingReps,
      filters, setFilters,
      clearContext,
      setProject,
    }}>
      {children}
    </RecordsContext.Provider>
  )
}

export function useRecords() {
  return useContext(RecordsContext)
}
