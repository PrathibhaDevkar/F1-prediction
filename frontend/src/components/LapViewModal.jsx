import './LapViewModal.css';

export default function LapViewModal({ race, onClose }) {
  if (!race) return null;
  
  // Generic placeholder data for futuristic projection
  const laps = Math.floor(Math.random() * (78 - 50 + 1) + 50);
  const length = (Math.random() * (7 - 4) + 4).toFixed(3);
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>&times;</button>
        <h2 className="modal-title">{race.name}</h2>
        <p className="modal-subtitle">Official 2026 Calendar Event</p>
        
        <div className="circuit-stats">
          <div className="stat-box">
            <span className="stat-label">Race Date</span>
            <span className="stat-value">{race.date}</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Laps</span>
            <span className="stat-value">{laps}</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Circuit Length</span>
            <span className="stat-value">{length} km</span>
          </div>
        </div>

        {race.status === 'completed' && (
          <div className="race-results-container" style={{ background: 'var(--f1-dark)', padding: '1.5rem', textAlign: 'center', border: '1px solid var(--f1-grey)', borderLeft: '4px solid var(--f1-red)', marginTop: '1rem' }}>
            <h3 style={{ textTransform: 'uppercase', color: 'var(--f1-light-grey)', marginBottom: '0.5rem', fontSize: '0.9rem', letterSpacing: '1px' }}>🏁 Official Result</h3>
            <p style={{ color: '#fff', fontSize: '2rem', fontWeight: 900, margin: '0' }}>🏆 {race.winner}</p>
            <p style={{ color: 'var(--f1-red)', fontSize: '1.2rem', fontWeight: 700, margin: '0.5rem 0 0 0' }}>{race.team} <span style={{ color: 'var(--f1-light-grey)' }}>| +{race.points} PTS</span></p>
          </div>
        )}
      </div>
    </div>
  );
}
