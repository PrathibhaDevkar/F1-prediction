import { useEffect, useState } from 'react';
import { API_BASE } from '../config';

export default function Standings() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/standings`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load standings');
        return res.json();
      })
      .then(setData)
      .catch(err => setError(err.message));
  }, []);

  return (
    <div className="dashboard-panel" style={{ maxWidth: '1200px', width: '100%', margin: '2rem auto 0' }}>
      <h2>{data?.season ? `${data.season} Standings` : 'Standings'}</h2>

      {error && <p style={{ color: '#ff3b30' }}>{error}</p>}
      {!data && !error && <p>Loading standings...</p>}

      {data && data.drivers.length === 0 && (
        <p style={{ color: 'var(--f1-light-grey)' }}>No results yet this season.</p>
      )}

      {data && data.drivers.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '2rem', alignItems: 'start' }}>
          <div>
            <h3 style={{ marginBottom: '0.5rem', fontSize: '0.95rem', color: 'var(--f1-light-grey)' }}>Drivers</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                {data.drivers.map((d, i) => (
                  <tr
                    key={d.abbreviation}
                    className="stagger-row"
                    style={{ borderBottom: '1px solid var(--f1-dark)', animationDelay: `${i * 20}ms` }}
                  >
                    <td style={{ padding: '0.4rem', width: '2.5rem', color: 'var(--f1-light-grey)' }}>{d.position}</td>
                    <td style={{ padding: '0.4rem', fontWeight: 600 }}>{d.name}</td>
                    <td style={{ padding: '0.4rem', color: 'var(--f1-light-grey)' }}>{d.team}</td>
                    <td style={{ padding: '0.4rem', textAlign: 'right', fontWeight: 700 }}>{d.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h3 style={{ marginBottom: '0.5rem', fontSize: '0.95rem', color: 'var(--f1-light-grey)' }}>Constructors</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                {data.constructors.map((c, i) => (
                  <tr
                    key={c.team}
                    className="stagger-row"
                    style={{ borderBottom: '1px solid var(--f1-dark)', animationDelay: `${i * 20}ms` }}
                  >
                    <td style={{ padding: '0.4rem', width: '2.5rem', color: 'var(--f1-light-grey)' }}>{c.position}</td>
                    <td style={{ padding: '0.4rem', fontWeight: 600 }}>{c.team}</td>
                    <td style={{ padding: '0.4rem', textAlign: 'right', fontWeight: 700 }}>{c.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
