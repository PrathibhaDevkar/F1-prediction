import { useEffect, useRef, useState } from 'react';

const WS_URL = 'ws://localhost:8000/ws/live-timing';
const MAX_TRAIL_POINTS = 3000;

export default function TrackMap({ drivers }) {
  const [status, setStatus] = useState('idle');
  const [positions, setPositions] = useState({});
  const [bounds, setBounds] = useState(null);
  const trailRef = useRef([]);
  const boundsRef = useRef(null);
  const wsRef = useRef(null);

  const driverByNumber = {};
  drivers.forEach((d) => { driverByNumber[String(d.driverNumber)] = d; });

  useEffect(() => {
    let cancelled = false;
    let reconnectTimer = null;

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'status') {
          setStatus(msg.status);
          return;
        }
        if (msg.type !== 'telemetry' || !msg.positions?.length) return;

        for (const p of msg.positions) {
          trailRef.current.push({ x: p.x, y: p.y });
          if (!boundsRef.current) {
            boundsRef.current = { minX: p.x, maxX: p.x, minY: p.y, maxY: p.y };
          } else {
            const b = boundsRef.current;
            b.minX = Math.min(b.minX, p.x);
            b.maxX = Math.max(b.maxX, p.x);
            b.minY = Math.min(b.minY, p.y);
            b.maxY = Math.max(b.maxY, p.y);
          }
        }
        if (trailRef.current.length > MAX_TRAIL_POINTS) {
          trailRef.current = trailRef.current.slice(-MAX_TRAIL_POINTS);
        }

        setPositions((prev) => {
          const next = { ...prev };
          for (const p of msg.positions) next[p.driver_number] = { x: p.x, y: p.y };
          return next;
        });
        setBounds({ ...boundsRef.current });
      };

      ws.onclose = () => { if (!cancelled) reconnectTimer = setTimeout(connect, 3000); };
      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  if (status !== 'connected' || !bounds) return null;

  const padding = 500;
  const width = bounds.maxX - bounds.minX + padding * 2;
  const height = bounds.maxY - bounds.minY + padding * 2;
  const viewBox = `${bounds.minX - padding} ${-bounds.maxY - padding} ${width} ${height}`;

  return (
    <div className="dashboard-panel" style={{ maxWidth: '1200px', width: '100%', margin: '2rem auto 0' }}>
      <h2>Track Map</h2>
      <svg viewBox={viewBox} style={{ width: '100%', height: '420px', background: '#050505' }}>
        {trailRef.current.map((p, i) => (
          <circle key={i} cx={p.x} cy={-p.y} r={40} fill="#2a2a2a" />
        ))}
        {Object.entries(positions).map(([num, pos]) => {
          const driver = driverByNumber[num];
          return (
            <g key={num}>
              <circle cx={pos.x} cy={-pos.y} r={160} fill={driver?.teamColor || '#e10600'} stroke="#fff" strokeWidth={20} />
              <text x={pos.x} y={-pos.y - 220} fill="#fff" fontSize="280" textAnchor="middle" fontWeight="700">
                {driver?.abbreviation || num}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
