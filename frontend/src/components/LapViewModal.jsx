import { useEffect, useState } from 'react';
import './LapViewModal.css';
import { API_BASE } from '../config';

const SEASON = 2026;

export default function LapViewModal({ race, onClose }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!race) {
      setDetail(null);
      setError(null);
      return;
    }
    if (race.status !== 'completed') return;

    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/races/${SEASON}/${race.round}`)
      .then(res => {
        if (!res.ok) throw new Error('Results not available for this race yet');
        return res.json();
      })
      .then(setDetail)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [race]);

  if (!race) return null;

  const winner = detail?.podium?.[0];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>&times;</button>
        <h2 className="modal-title">{race.name}</h2>
        <p className="modal-subtitle">{SEASON} Season — Round {race.round}</p>

        <div className="circuit-stats">
          <div className="stat-box">
            <span className="stat-label">Race Date</span>
            <span className="stat-value">
              {race.date ? new Date(race.date).toLocaleDateString('en-US', { month: 'short', day: '2-digit' }) : '--'}
            </span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Laps</span>
            <span className="stat-value">{detail?.laps ?? '--'}</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Location</span>
            <span className="stat-value">{detail?.location ?? race.location ?? '--'}</span>
          </div>
        </div>

        {race.status !== 'completed' && (
          <p style={{ color: 'var(--f1-light-grey)', marginTop: '1rem' }}>
            This race hasn't happened yet — results will appear here once it's complete.
          </p>
        )}

        {race.status === 'completed' && loading && (
          <p style={{ color: 'var(--f1-light-grey)', marginTop: '1rem' }}>Loading real results...</p>
        )}

        {race.status === 'completed' && error && (
          <p style={{ color: '#ff3b30', marginTop: '1rem' }}>{error}</p>
        )}

        {winner && (
          <div className="race-results-container" style={{ background: 'var(--f1-dark)', padding: '1.5rem', textAlign: 'center', border: '1px solid var(--f1-grey)', borderLeft: '4px solid var(--f1-red)', marginTop: '1rem' }}>
            <h3 style={{ textTransform: 'uppercase', color: 'var(--f1-light-grey)', marginBottom: '0.5rem', fontSize: '0.9rem', letterSpacing: '1px' }}>🏁 Official Result</h3>
            <p style={{ color: '#fff', fontSize: '2rem', fontWeight: 900, margin: '0' }}>🏆 {winner.driver}</p>
            <p style={{ color: 'var(--f1-red)', fontSize: '1.2rem', fontWeight: 700, margin: '0.5rem 0 0 0' }}>
              {winner.team} <span style={{ color: 'var(--f1-light-grey)' }}>| +{winner.points} PTS</span>
            </p>
          </div>
        )}

        {detail?.podium && detail.podium.length > 1 && (
          <div style={{ marginTop: '1rem', textAlign: 'left' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--f1-light-grey)', marginBottom: '0.5rem' }}>Podium</h3>
            {detail.podium.map(p => (
              <div key={p.position} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--f1-dark)' }}>
                <span>P{p.position} — {p.driver}</span>
                <span style={{ color: 'var(--f1-light-grey)' }}>{p.team}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
