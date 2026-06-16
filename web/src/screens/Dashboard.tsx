import React from 'react'
import type { ScreenProps } from '../types'

export function Dashboard(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Dashboard</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — stat tiles, advisory banner, hero, recent runs table</p>
    </div>
  )
}

export default Dashboard
