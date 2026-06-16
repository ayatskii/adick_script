import React, { useEffect } from 'react'
import type { ToastState } from '../types'

interface ToastProps extends ToastState {
  onDismiss: () => void
}

const TOAST_STYLE: Record<string, { bg: string; fg: string; icon: string }> = {
  ok: { bg: '#2f8f6b', fg: '#fff', icon: '🎉' },
  err: { bg: '#c62d1f', fg: '#fff', icon: '💥' },
  warn: { bg: '#cf9a36', fg: '#3a2600', icon: '⚠️' },
  info: { bg: 'var(--violet)', fg: '#fff', icon: '👻' },
}

export function Toast({ kind, message, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 3200)
    return () => clearTimeout(timer)
  }, [message, onDismiss])

  const style = TOAST_STYLE[kind] ?? TOAST_STYLE.info

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 60,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '10px',
        padding: '13px 20px',
        border: '1.5px solid var(--line)',
        borderRadius: '5px',
        boxShadow: '5px 5px 13px var(--shadowc)',
        background: style.bg,
        color: style.fg,
        fontFamily: "'Shippori Mincho B1', serif",
        fontWeight: 700,
        fontSize: '14px',
        animation: 'popin .3s ease both',
        cursor: 'pointer',
        maxWidth: '90vw',
      }}
      onClick={onDismiss}
    >
      <span>{style.icon}</span>
      <span>{message}</span>
    </div>
  )
}

export default Toast
