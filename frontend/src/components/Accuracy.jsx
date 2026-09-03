import { useEffect, useState } from 'react';
import { API_BASE } from '../config';

function StatCard({ label, value, sub }) {
  return (
    <div className="dashboard-panel" style={{ padding: '1rem', textAlign: 'center' }}>
      <p style={{ fontSize: '1.6rem', fontWeight: 900, color: 'var(--accent-color)' }}>{value}</p>
      <p style={{ fontSize: '0.85rem', fontWeight: 600 }}>{label}</p>
      {sub && <p style={{ fontSize: '0.75rem', color: 'var(--f1-light-grey)' }}>{sub}</p>}
    </div>
  );
}

export default function Accuracy() {
  const [accuracy, setAccuracy] = useState(null);
  const [trackRecord, setTrackRecord] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/accuracy`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load accuracy data');
        return res.json();
      })
      .then(setAccuracy)
      .catch(err => setError(err.message));

    fetch(`${API_BASE}/api/track-record`)
      .then(res => res.json())
      .then(data => setTrackRecord(data.records || []))
      .catch(() => setTrackRecord([]));
  }, []);

  const metrics = accuracy?.metrics;
  const recentTests = accuracy?.testPredictions
    ? [...accuracy.testPredictions].sort((a, b) => (b.season - a.season) || (b.round - a.round)).slice(0, 15)
    : [];

  return (
    <div className="dashboard-panel" style={{ maxWidth: '1200px', width: '100%', margin: '2rem auto 0' }}>
      <h2>Model Accuracy</h2>
      <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
        These numbers come from races the model never saw during training — a fair test of how good
        the predictions really are, not just how well it memorized the past.
      </p>

      {error && <p style={{ color: '#ff3b30' }}>{error}</p>}
      {!accuracy && !error && <p>Loading accuracy data...</p>}

      {metrics && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
            <StatCard
              label="Avg. position miss"
              value={`${metrics.mae.toFixed(1)} places`}
              sub={`${(metrics.within_3_positions * 100).toFixed(0)}% within 3 places`}
            />
            <StatCard
              label="Win detection"
              value={metrics.win_auc.toFixed(2)}
              sub="1.00 = perfect, 0.50 = coin flip"
            />
            <StatCard
              label="Podium detection"
              value={metrics.podium_auc.toFixed(2)}
              sub="1.00 = perfect, 0.50 = coin flip"
            />
            <StatCard
              label="Points detection"
              value={metrics.points_auc.toFixed(2)}
              sub="1.00 = perfect, 0.50 = coin flip"
            />
          </div>

          <h3 style={{ fontSize: '0.95rem', color: 'var(--f1-light-grey)', marginBottom: '0.5rem' }}>
            Real forecasts vs. what happened
          </h3>
          {trackRecord === null && <p>Loading track record...</p>}
          {trackRecord && trackRecord.length === 0 && (
            <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem', marginBottom: '2rem' }}>
              No completed races yet since this feature shipped — a real forecast is logged before every
              race, then checked against the result once it's run. Check back after the next race weekend.
            </p>
          )}
          {trackRecord && trackRecord.length > 0 && (
            <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '2rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--f1-grey)' }}>
                    <th style={{ textAlign: 'left', padding: '0.4rem' }}>Race</th>
                    <th style={{ textAlign: 'left', padding: '0.4rem' }}>Driver</th>
                    <th style={{ textAlign: 'left', padding: '0.4rem' }}>We predicted</th>
                    <th style={{ textAlign: 'left', padding: '0.4rem' }}>Actual</th>
                  </tr>
                </thead>
                <tbody>
                  {trackRecord.map((r, i) => (
                    <tr key={`${r.season}-${r.round}-${r.driver}`} style={{ borderBottom: '1px solid var(--f1-dark)' }}>
                      <td style={{ padding: '0.4rem' }}>{r.season} {r.event}</td>
                      <td style={{ padding: '0.4rem' }}>{r.driver_name}</td>
                      <td style={{ padding: '0.4rem' }}>P{r.predicted_position}</td>
                      <td style={{ padding: '0.4rem', fontWeight: 700, color: r.actual_position <= r.predicted_position + 2 && r.actual_position >= r.predicted_position - 2 ? '#2ecc71' : 'inherit' }}>
                        P{r.actual_position}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h3 style={{ fontSize: '0.95rem', color: 'var(--f1-light-grey)', marginBottom: '0.5rem' }}>
            Sample of held-out test races ({recentTests.length} of {accuracy.testPredictions.length})
          </h3>
          <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--f1-grey)' }}>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>Race</th>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>Driver</th>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>Predicted</th>
                  <th style={{ textAlign: 'left', padding: '0.4rem' }}>Actual</th>
                </tr>
              </thead>
              <tbody>
                {recentTests.map((t, i) => (
                  <tr
                    key={`${t.season}-${t.round}-${t.driver}`}
                    className="stagger-row"
                    style={{ borderBottom: '1px solid var(--f1-dark)', animationDelay: `${i * 15}ms` }}
                  >
                    <td style={{ padding: '0.4rem' }}>{t.season} {t.event}</td>
                    <td style={{ padding: '0.4rem' }}>{t.driverName}</td>
                    <td style={{ padding: '0.4rem' }}>P{t.predictedPosition}</td>
                    <td style={{ padding: '0.4rem' }}>P{t.actualPosition}</td>
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
