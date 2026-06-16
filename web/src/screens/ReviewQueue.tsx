import React from 'react'
import type { ScreenProps } from '../types'

export function ReviewQueue(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>Review Queue</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — all-done empty state, filter bar, editable score/comment cards, sticky submit footer</p>
    </div>
  )
}

export default ReviewQueue
