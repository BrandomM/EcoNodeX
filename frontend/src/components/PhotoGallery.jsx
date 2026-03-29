import React, { useState } from 'react'
import api from '../api/client'

function PhotoCard({ media, onSetProfile, onDelete }) {
  return (
    <div className="relative group rounded-lg overflow-hidden border border-slate-200 bg-slate-50">
      <img
        src={api.mediaThumbnailUrl(media.id)}
        alt={media.file_name}
        className="w-full h-32 object-cover"
        loading="lazy"
        onError={(e) => { e.target.src = '/placeholder.svg' }}
      />
      {media.is_profile && (
        <span className="absolute top-1 left-1 badge-green text-xs">★ Perfil</span>
      )}
      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
        {!media.is_profile && onSetProfile && (
          <button
            className="bg-white text-slate-800 text-xs px-2 py-1 rounded hover:bg-primary-100"
            onClick={() => onSetProfile(media)}
            title="Usar como foto de perfil"
          >★ Perfil</button>
        )}
        <a
          href={api.mediaFileUrl(media.id)}
          target="_blank"
          rel="noreferrer"
          className="bg-white text-slate-800 text-xs px-2 py-1 rounded hover:bg-blue-100"
          title="Ver original"
        >↗</a>
        {onDelete && (
          <button
            className="bg-white text-red-600 text-xs px-2 py-1 rounded hover:bg-red-100"
            onClick={() => onDelete(media)}
            title="Eliminar"
          >✕</button>
        )}
      </div>
      <p className="text-xs text-slate-500 truncate px-2 py-1">{media.file_name}</p>
    </div>
  )
}

export default function PhotoGallery({ media = [], onSetProfile, onDelete }) {
  if (!media.length) {
    return (
      <div className="text-center py-8 text-slate-400">
        <p className="text-4xl mb-2">📷</p>
        <p className="text-sm">Sin fotos. Usa el flujo QR para subir desde el móvil.</p>
      </div>
    )
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {media.map((m) => (
        <PhotoCard key={m.id} media={m} onSetProfile={onSetProfile} onDelete={onDelete} />
      ))}
    </div>
  )
}
