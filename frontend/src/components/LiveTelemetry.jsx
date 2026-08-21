import { useEffect, useRef, useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { WS_URL } from '../config';

const MAX_HISTORY_POINTS = 60;

const STATUS_COPY = {
  idle: 'Connecting to the live telemetry service...',
  connecting: 'A session is in its scheduled window — connecting to live data...',
  no_data: 'Session window is open, but no telemetry has arrived yet. This can happen between sessions or if data is delayed.',
  error: 'Live telemetry service hit an error — retrying automatically.',
};

export default function LiveTelemetry() {
  const [status, setStatus] = useState('idle');
  const [detail, setDetail] = useState(null);
  const [session, setSession] = useState(null);
  const [driverReadings, setDriverReadings] = useState({});
  const historyRef = useRef({});
  const wsRef = useRef(null);

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
          setDetail(msg.detail);
          setSession(msg.session);
        } else if (msg.type === 'telemetry') {
          setDriverReadings((prev) => {
            const next = { ...prev };
            for (const reading of msg.readings) {
              next[reading.driver_number] = reading;

              const hist = historyRef.current[reading.driver_number] || [];
              hist.push({ time: new Date(reading.date).toLocaleTimeString(), speed: reading.speed });
              historyRef.current[reading.driver_number] = hist.slice(-MAX_HISTORY_POINTS);
            }
            return next;
          });
        }
      };

      ws.onclose = () => {
        if (!cancelled) reconnectTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, []);

  const driverNumbers = Object.keys(driverReadings);
  const firstDriver = driverNumbers[0];
  const chartData = firstDriver ? historyRef.current[firstDriver] || [] : [];

  return (
    <div className="dashboard-panel" style={{ maxWidth: '1200px', width: '100%', margin: '2rem auto 0' }}>
      <h2>Live Telemetry</h2>

      {status === 'no_session' && (
        <div>
          <p style={{ color: 'var(--f1-light-grey)', marginBottom: '0.5rem' }}>
            No F1 session is currently active. Live telemetry will appear here automatically once a
            session goes live.
          </p>
          {session && (
            <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem' }}>
              Most recent session: {session.session_name} — {session.location}, {session.country_name}
              {session.date_end && <> (ended {new Date(session.date_end).toLocaleString()})</>}
            </p>
          )}
        </div>
      )}

      {(status === 'idle' || status === 'connecting' || status === 'no_data' || status === 'error') && (
        <p style={{ color: status === 'error' ? '#ff3b30' : 'var(--f1-light-grey)' }}>
          {STATUS_COPY[status]}
          {detail && <span> ({detail})</span>}
        </p>
      )}

      {status === 'connected' && (
        <>
          <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            <span className="live-dot"></span>LIVE — {session?.session_name} · {session?.location}, {session?.country_name}
          </p>

          <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '1.5rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--f1-grey)' }}>
                <th style={{ textAlign: 'left', padding: '0.4rem' }}>Driver #</th>
                <th style={{ textAlign: 'left', padding: '0.4rem' }}>Speed</th>
                <th style={{ textAlign: 'left', padding: '0.4rem' }}>Gear</th>
                <th style={{ textAlign: 'left', padding: '0.4rem' }}>Throttle</th>
                <th style={{ textAlign: 'left', padding: '0.4rem' }}>Brake</th>
                <th style={{ textAlign: 'left', padding: '0.4rem' }}>DRS</th>
              </tr>
            </thead>
            <tbody>
              {driverNumbers.map((num) => {
                const r = driverReadings[num];
                return (
                  <tr key={num} style={{ borderBottom: '1px solid var(--f1-dark)' }}>
                    <td style={{ padding: '0.4rem' }}>#{num}</td>
                    <td style={{ padding: '0.4rem' }}>{r.speed} km/h</td>
                    <td style={{ padding: '0.4rem' }}>{r.n_gear}</td>
                    <td style={{ padding: '0.4rem' }}>{r.throttle}%</td>
                    <td style={{ padding: '0.4rem' }}>{r.brake}%</td>
                    <td style={{ padding: '0.4rem' }}>{r.drs ? 'Open' : 'Closed'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {firstDriver && chartData.length > 1 && (
            <div style={{ height: 250 }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--f1-light-grey)', marginBottom: '0.5rem' }}>
                Speed trace — Driver #{firstDriver}
              </p>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="time" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="speed" stroke="#e10600" dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
}
