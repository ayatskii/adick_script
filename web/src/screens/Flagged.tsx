import React from 'react'
import type { ScreenProps } from '../types'

export function Flagged(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Flagged</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — 5 amber notice cards with reason/severity/detail + Resolve/Retry</p>
    </div>
  )
}

export default Flagged
