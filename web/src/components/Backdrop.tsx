export function Backdrop() {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}
      aria-hidden="true"
    >
      {/* Rising sun disc (vermilion) */}
      <div
        style={{
          position: 'absolute',
          top: '-150px',
          right: '-90px',
          width: '560px',
          height: '560px',
          borderRadius: '50%',
          background: 'var(--sun)',
          opacity: 0.12,
        }}
      />
      {/* Sun ring */}
      <div
        style={{
          position: 'absolute',
          top: '-150px',
          right: '-90px',
          width: '560px',
          height: '560px',
          borderRadius: '50%',
          border: '6px solid var(--sun)',
          opacity: 0.07,
        }}
      />

      {/* Mountain silhouettes — two layered paths */}
      <svg
        viewBox="0 0 1440 380"
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          width: '100%',
          height: '40%',
        }}
        preserveAspectRatio="xMidYMax slice"
      >
        <path
          d="M0 380 L0 260 L120 200 L240 260 L360 140 L480 220 L600 120 L720 200 L840 100 L960 180 L1080 80 L1200 160 L1320 60 L1440 140 L1440 380 Z"
          fill="var(--ink)"
          opacity="0.05"
        />
        <path
          d="M0 380 L0 310 L160 270 L280 310 L400 230 L520 290 L640 200 L760 270 L880 180 L1000 250 L1140 170 L1280 240 L1440 200 L1440 380 Z"
          fill="var(--ink)"
          opacity="0.045"
        />
      </svg>
    </div>
  )
}

export default Backdrop
