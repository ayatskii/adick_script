import type { RunMode } from '../types'

interface ModeBannerProps {
  mode: RunMode
}

export function ModeBanner({ mode }: ModeBannerProps) {
  if (mode === 'dryrun') {
    return (
      <div
        style={{
          padding: '8px 22px',
          borderBottom: '1.5px solid var(--line)',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '13px',
          color: '#fff',
          background: 'repeating-linear-gradient(45deg,#6a5a9e,#6a5a9e 10px,#4e4179 10px,#4e4179 20px)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span>👻</span>
        <span>DRY-RUN — evaluating only. Nothing is being submitted to Edvibe.</span>
      </div>
    )
  }

  if (mode === 'full') {
    return (
      <div
        style={{
          padding: '8px 22px',
          borderBottom: '1.5px solid var(--line)',
          fontFamily: "'Shippori Mincho B1', serif",
          fontWeight: 700,
          fontSize: '13px',
          color: '#3a2600',
          background: 'repeating-linear-gradient(45deg,#cf9a36,#cf9a36 16px,#e0b85e 16px,#e0b85e 32px)',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <span>⚠️</span>
        <span>FULL-AUTO — real grades are being submitted and lessons completed.</span>
      </div>
    )
  }

  return null
}

export default ModeBanner
