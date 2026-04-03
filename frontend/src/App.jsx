import { useState } from 'react'
import './index.css'
import LapViewModal from './components/LapViewModal'

function App() {
  const [grid, setGrid] = useState(1);
  const [team, setTeam] = useState('Ferrari');
  const [predictionData, setPredictionData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedRace, setSelectedRace] = useState(null);

  const teams = [
    'Red Bull Racing', 'Ferrari', 'Mercedes', 'McLaren', 
    'Aston Martin', 'Alpine', 'Williams', 'AlphaTauri', 'Alfa Romeo', 'Haas F1 Team', 'Audi Sport (2026)'
  ];

  /* 2026 Official F1 24-Race Calendar */
  const calendarRaces = [
    { date: 'MAR 08', name: 'Australia (Melbourne)', status: 'completed', winner: 'Max Verstappen', team: 'Red Bull Racing', points: 26 },
    { date: 'MAR 15', name: 'China (Shanghai)', status: 'completed', winner: 'Kimi Antonelli', team: 'Mercedes', points: 25 },
    { date: 'MAR 29', name: 'Japan (Suzuka)', status: 'upcoming' },
    { date: 'APR 12', name: 'Bahrain (Sakhir)', status: 'upcoming' },
    { date: 'APR 19', name: 'Saudi Arabia (Jeddah)', status: 'upcoming' },
    { date: 'MAY 03', name: 'USA (Miami)', status: 'upcoming' },
    { date: 'MAY 24', name: 'Canada (Montreal)', status: 'upcoming' },
    { date: 'JUN 07', name: 'Monaco', status: 'upcoming' },
    { date: 'JUN 14', name: 'Spain (Barcelona)', status: 'upcoming' },
    { date: 'JUN 28', name: 'Austria (Spielberg)', status: 'upcoming' },
    { date: 'JUL 05', name: 'Great Britain (Silverstone)', status: 'upcoming' },
    { date: 'JUL 19', name: 'Belgium (Spa)', status: 'upcoming' },
    { date: 'JUL 26', name: 'Hungary (Budapest)', status: 'upcoming' },
    { date: 'AUG 23', name: 'Netherlands (Zandvoort)', status: 'upcoming' },
    { date: 'SEP 06', name: 'Italy (Monza)', status: 'upcoming' },
    { date: 'SEP 13', name: 'Spain (Madrid)', status: 'upcoming' },
    { date: 'SEP 26', name: 'Azerbaijan (Baku)', status: 'upcoming' },
    { date: 'OCT 11', name: 'Singapore', status: 'upcoming' },
    { date: 'OCT 25', name: 'USA (Austin)', status: 'upcoming' },
    { date: 'NOV 01', name: 'Mexico', status: 'upcoming' },
    { date: 'NOV 08', name: 'Brazil (Sao Paulo)', status: 'upcoming' },
    { date: 'NOV 21', name: 'USA (Las Vegas)', status: 'upcoming' },
    { date: 'NOV 29', name: 'Qatar (Lusail)', status: 'upcoming' },
    { date: 'DEC 06', name: 'Abu Dhabi (Yas Marina)', status: 'upcoming' }
  ];

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setPredictionData(null);
    
    try {
      // Temporarily use Alfa Romeo if the user selects the futuristic 2026 Audi team
      const backendTeam = team === 'Audi Sport (2026)' ? 'Alfa Romeo' : team;
      const response = await fetch('http://localhost:8000/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ grid: parseInt(grid), team: backendTeam })
      });
      
      if (!response.ok) {
        throw new Error('Prediction request failed from server');
      }
      
      const data = await response.json();
      
      setTimeout(() => {
        setPredictionData(data);
        setLoading(false);
      }, 1000);
      
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <>
      <h1 style={{ marginBottom: '1rem' }}>Apex F1 Predictor 2026</h1>
      
      <div className="dashboard-grid">
        {/* Left Column: Future Races (Scrollable if needed) */}
        <div className="dashboard-panel" style={{ maxHeight: '800px', overflowY: 'auto' }}>
          <h2>2026 Calendar</h2>
          <ul className="race-list">
            {calendarRaces.map((race, i) => (
              <li key={i} className={`race-item ${race.status}`} style={{ cursor: 'pointer' }} onClick={() => setSelectedRace(race)}>
                <span className="race-date">{race.date}</span>
                <div className="race-details">
                  <span className="race-name">{race.name}</span>
                  {race.status === 'completed' && (
                    <span className="race-winner">
                      🏆 {race.winner} ({race.team}) <strong style={{color: 'var(--f1-white)'}}>+{race.points} pts</strong>
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {/* Center Column: Engine */}
        <div className="dashboard-panel glass-panel" style={{ width: '100%', maxWidth: '100%', border: '1px solid var(--accent-color)' }}>
          <h2>Prediction Engine</h2>
          <form onSubmit={handlePredict}>
            <div className="form-group">
              <label>Starting Grid Position</label>
              <input 
                type="number" 
                min="1" 
                max="20" 
                value={grid}
                onChange={(e) => setGrid(e.target.value)}
                required 
              />
            </div>
            <div className="form-group">
              <label>Constructor Team</label>
              <select 
                value={team}
                onChange={(e) => setTeam(e.target.value)}
              >
                {teams.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Crunching Numbers...' : 'Predict 2026 Outcome'}
            </button>
          </form>

          {loading && <div className="loader"></div>}
          {error && <p style={{color: '#ff3b30', marginTop: '1rem', fontWeight: 600}}>{error}</p>}

          {predictionData && predictionData.probabilities && (
            <div style={{ marginTop: '2rem', textAlign: 'left', animation: 'slideUp 0.5s ease backwards' }}>
              <div className="prediction-item" style={{ marginBottom: '2rem' }}>
                <span className="position-badge" style={{ fontSize: '1.8rem', width: 'auto', marginRight: '1rem' }}>
                  P{predictionData.predicted_position}
                </span>
                <span className="team-name" style={{ fontSize: '1.3rem' }}>Predicted Finish</span>
              </div>
              
              <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Probabilities</h2>
              {predictionData.probabilities.map((prob, i) => (
                <div key={i} className="prob-row">
                  <div className="prob-label">
                    <span>Position {prob.position}</span>
                    <span style={{color: 'var(--accent-color)'}}>{(prob.probability * 100).toFixed(1)}%</span>
                  </div>
                  <div className="prob-bar-bg">
                    <div className="prob-bar-fill" style={{ width: `${prob.probability * 100}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
      
      {/* Lap View Modal Component */}
      <LapViewModal race={selectedRace} onClose={() => setSelectedRace(null)} />
    </>
  )
}

export default App
