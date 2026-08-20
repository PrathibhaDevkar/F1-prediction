import { useState } from 'react';

const API_BASE = 'http://localhost:8000';

export default function HeadToHead({ drivers }) {
  const [driverA, setDriverA] = useState('');
  const [driverB, setDriverB] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCompare = async () => {
    if (!driverA || !driverB || driverA === driverB) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/head-to-head?driver_a=${driverA}&driver_b=${driverB}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Comparison failed');
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-panel" style={{ maxWidth: '1200px', width: '100%', margin: '2rem auto 0' }}>
      <h2>Head-to-Head</h2>

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
          <label>Driver A</label>
          <select value={driverA} onChange={(e) => setDriverA(e.target.value)}>
            <option value="">Select a driver</option>
            {drivers.map(d => (
              <option key={d.abbreviation} value={d.abbreviation}>{d.fullName}</option>
            ))}
          </select>
        </div>
        <div className="form-group" style={{ flex: 1, minWidth: '200px' }}>
          <label>Driver B</label>
          <select value={driverB} onChange={(e) => setDriverB(e.target.value)}>
            <option value="">Select a driver</option>
            {drivers.map(d => (
              <option key={d.abbreviation} value={d.abbreviation}>{d.fullName}</option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="btn-primary"
          style={{ height: '48px' }}
          disabled={!driverA || !driverB || driverA === driverB || loading}
          onClick={handleCompare}
        >
          {loading ? 'Comparing...' : 'Compare'}
        </button>
      </div>

      {error && <p style={{ color: '#ff3b30' }}>{error}</p>}

      {result && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            {[result.driverA, result.driverB].map((d, i) => (
              <div key={d.abbreviation} className="dashboard-panel" style={{ padding: '1rem', textAlign: i === 0 ? 'left' : 'right' }}>
                <h3 style={{ marginBottom: '0.5rem' }}>{d.name}</h3>
                <p style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--f1-red)' }}>{d.wins} wins</p>
                <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem' }}>
                  Avg finish P{d.avgFinish} · {d.totalPoints} pts
                </p>
              </div>
            ))}
          </div>

          <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
            {result.racesCompared} shared races
          </p>
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--f1-grey)' }}>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>Race</th>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>{result.driverA.abbreviation}</th>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>{result.driverB.abbreviation}</th>
                </tr>
              </thead>
              <tbody>
                {result.races.map((r) => (
                  <tr key={`${r.season}-${r.round}`} style={{ borderBottom: '1px solid var(--f1-dark)' }}>
                    <td style={{ padding: '0.4rem' }}>{r.season} {r.event}</td>
                    <td style={{ padding: '0.4rem' }}>{r.driverAPosition ? `P${r.driverAPosition}` : '--'}</td>
                    <td style={{ padding: '0.4rem' }}>{r.driverBPosition ? `P${r.driverBPosition}` : '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
