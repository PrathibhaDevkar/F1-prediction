import { useEffect, useState } from 'react';

const LIGHT_STEP_MS = 400;
const HOLD_MS = 600;
const FADE_MS = 500;

export default function StartLights({ onDone }) {
  const [litCount, setLitCount] = useState(0);
  const [goSignal, setGoSignal] = useState(false);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const timers = [];
    for (let i = 1; i <= 5; i++) {
      timers.push(setTimeout(() => setLitCount(i), i * LIGHT_STEP_MS));
    }
    timers.push(setTimeout(() => setGoSignal(true), 5 * LIGHT_STEP_MS + HOLD_MS));
    timers.push(setTimeout(() => setFading(true), 5 * LIGHT_STEP_MS + HOLD_MS + 200));
    timers.push(setTimeout(() => onDone?.(), 5 * LIGHT_STEP_MS + HOLD_MS + 200 + FADE_MS));
    return () => timers.forEach(clearTimeout);
  }, [onDone]);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: '#000',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '2rem',
        zIndex: 1000,
        opacity: fading ? 0 : 1,
        transition: `opacity ${FADE_MS}ms ease`,
        pointerEvents: fading ? 'none' : 'auto',
      }}
    >
      <div style={{ display: 'flex', gap: '1.5rem' }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              background: goSignal ? '#1a1a1a' : (litCount >= i ? 'var(--f1-red)' : '#1a1a1a'),
              boxShadow: !goSignal && litCount >= i ? '0 0 30px var(--f1-red)' : 'none',
              border: '2px solid #333',
              transition: 'background 0.15s ease, box-shadow 0.15s ease',
            }}
          />
        ))}
      </div>
      {goSignal && (
        <div
          style={{
            fontSize: '2rem',
            fontWeight: 900,
            letterSpacing: '0.3em',
            color: '#4ade80',
            textShadow: '0 0 20px rgba(74, 222, 128, 0.6)',
            animation: 'goFlash 0.3s ease',
          }}
        >
          GO
        </div>
      )}
    </div>
  );
}
