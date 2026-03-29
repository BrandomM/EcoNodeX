import React from 'react'

export default function LoadingSpinner({ message = 'Cargando…' }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-400 gap-3">
      <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      <span className="text-sm">{message}</span>
    </div>
  )
}

export function InlineSpinner() {
  return (
    <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
  )
}
