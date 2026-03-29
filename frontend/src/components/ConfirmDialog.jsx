import React, { useState } from 'react'
import Modal from './Modal'

/**
 * Generic confirm dialog. Optionally requires the user to type a specific string.
 */
export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = '¿Confirmar?',
  message,
  confirmText,       // if set, user must type this string
  confirmLabel = 'Confirmar',
  danger = false,
  loading = false,
}) {
  const [typed, setTyped] = useState('')

  const canConfirm = confirmText ? typed === confirmText : true

  const handleConfirm = () => {
    if (!canConfirm) return
    onConfirm(typed)
    setTyped('')
  }

  const handleClose = () => {
    setTyped('')
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={title} size="sm">
      {message && <p className="text-sm text-slate-600 mb-4">{message}</p>}
      {confirmText && (
        <div className="mb-4">
          <label className="label">
            Escribe <strong className="font-mono">{confirmText}</strong> para confirmar:
          </label>
          <input
            className="input"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            placeholder={confirmText}
            autoFocus
          />
        </div>
      )}
      <div className="flex gap-2 justify-end mt-2">
        <button className="btn-secondary" onClick={handleClose} disabled={loading}>
          Cancelar
        </button>
        <button
          className={danger ? 'btn-danger' : 'btn-primary'}
          onClick={handleConfirm}
          disabled={!canConfirm || loading}
        >
          {loading ? 'Procesando…' : confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
