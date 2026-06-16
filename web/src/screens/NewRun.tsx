import type { ScreenProps } from '../types'

export function NewRun(_props: ScreenProps) {
  return (
    <div>
      <h2 style={{ fontFamily: "'Shippori Mincho B1', serif", fontWeight: 800, color: 'var(--ink)' }}>New Run</h2>
      <p style={{ color: 'var(--ink-soft)' }}>TODO: implement — mode segments, scope picker, safety caps, confidence slider, start button</p>
    </div>
  )
}

export default NewRun
