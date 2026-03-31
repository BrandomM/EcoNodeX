import React, { useState } from 'react'
import api from '../api/client'

/**
 * Taxon avatar/preview.
 * Shows thumbnail if profile_media_id is set, otherwise initials.
 *
 * Props:
 *   mediaId   - profile_media_id (optional)
 *   name      - taxon name (used for initials fallback and alt text)
 *   size      - Tailwind size class (default "h-8 w-8")
 *   square    - use rounded-lg instead of rounded-full (for larger previews)
 */
export default function TaxonAvatar({ mediaId, name = '', size = 'h-8 w-8', square = false }) {
  const [imgError, setImgError] = useState(false)
  const shape = square ? 'rounded-lg' : 'rounded-full'

  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')

  if (mediaId && !imgError) {
    const src = square ? api.mediaFileUrl(mediaId) : api.mediaThumbnailUrl(mediaId)
    return (
      <img
        src={src}
        alt={name}
        onError={() => setImgError(true)}
        className={`${size} ${shape} object-cover flex-shrink-0 bg-slate-100`}
        loading="lazy"
      />
    )
  }

  return (
    <div
      className={`${size} ${shape} flex-shrink-0 bg-slate-200 flex items-center justify-center text-slate-500 font-medium select-none`}
      style={{ fontSize: square ? '1rem' : '0.6rem' }}
      title={name}
    >
      {initials || '?'}
    </div>
  )
}
