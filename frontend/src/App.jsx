import { useEffect, useState } from 'react'
import './index.css'
import LapViewModal from './components/LapViewModal'
import LiveTelemetry from './components/LiveTelemetry'

const API_BASE = 'http://localhost:8000'

function App() {
  const [grid, setGrid] = useState(1)
  const [team, setTeam] = useState('')
  const [driver, setDriver] = useState('')
  const [circuit, setCircuit] = useState('')
  const [predictionData, setPredictionData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedRace, setSelectedRace] = useState(null)

  const [calendarRaces, setCalendarRaces] = useState([])
  const [calendarLoading, setCalendarLoading] = useState(true)
  const [calendarError, setCalendarError] = useState(null)

  const [drivers, setDrivers] = useState([])
  const [teams, setTeams] = useState([])

  const [nextRace, setNextRace] = useState(null)
  const [nextRaceLoading, setNextRaceLoading] = useState(true)
  const [nextRaceError, setNextRaceError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/calendar`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load the race calendar')
        return res.json()
      })
      .then(data => setCalendarRaces(data.races || []))
      .catch(err => setCalendarError(err.message))
      .finally(() => setCalendarLoading(false))

    fetch(`${API_BASE}/api/drivers`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load drivers')
        return res.json()
      })
      .then(data => {
        setDrivers(data.drivers || [])
        setTeams(data.teams || [])
        if (data.teams && data.teams.length > 0) setTeam(data.teams[0])
      })
      .catch(() => {
        // Non-fatal: the predict form just falls back to an empty team list
      })

    fetch(`${API_BASE}/api/next-race`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load the next-race forecast')
        return res.json()
      })
      .then(data => setNextRace(data))
      .catch(err => setNextRaceError(err.message))
      .finally(() => setNextRaceLoading(false))
  }, [])

  const uniqueCircuits = [...new Set(calendarRaces.map(r => r.location).filter(Boolean))]

  const handlePredict = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setPredictionData(null)

    try {
      const response = await fetch(`${API_BASE}/api/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          grid: parseInt(grid),
          team,
          driver: driver || null,
          circuit: circuit || null,
        }),
      })

      if (!response.ok) {
        throw new Error('Prediction request failed from server')
      }

      const data = await response.json()

      setTimeout(() => {
        setPredictionData(data)
        setLoading(false)
      }, 1000)

    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  return (
    <>
      <h1 style={{ marginBottom: '1rem' }}>Apex F1 Predictor 2026</h1>

      <div className="dashboard-grid">
        {/* Left Column: Real Calendar */}
        <div className="dashboard-panel" style={{ maxHeight: '800px', overflowY: 'auto' }}>
          <h2>2026 Calendar</h2>
          {calendarLoading && <p>Loading real calendar...</p>}
          {calendarError && <p style={{ color: '#ff3b30' }}>{calendarError}</p>}
          <ul className="race-list">
            {calendarRaces.map((race) => (
              <li
                key={race.round}
                className={`race-item ${race.status}`}
                style={{ cursor: 'pointer' }}
                onClick={() => setSelectedRace(race)}
              >
                <span className="race-date">
                  {race.date ? new Date(race.date).toLocaleDateString('en-US', { month: 'short', day: '2-digit' }).toUpperCase() : '--'}
                </span>
                <div className="race-details">
                  <span className="race-name">{race.name}</span>
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
              <select value={team} onChange={(e) => setTeam(e.target.value)}>
                {teams.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Driver (optional)</label>
              <select value={driver} onChange={(e) => setDriver(e.target.value)}>
                <option value="">Average driver</option>
                {drivers.map(d => (
                  <option key={d.abbreviation} value={d.abbreviation}>{d.fullName}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Circuit (optional)</label>
              <select value={circuit} onChange={(e) => setCircuit(e.target.value)}>
                <option value="">Average circuit</option>
                {uniqueCircuits.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <button type="submit" className="btn-primary" disabled={loading || !team}>
              {loading ? 'Crunching Numbers...' : 'Predict Outcome'}
            </button>
          </form>

          {loading && <div className="loader"></div>}
          {error && <p style={{ color: '#ff3b30', marginTop: '1rem', fontWeight: 600 }}>{error}</p>}

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
                    <span style={{ color: 'var(--accent-color)' }}>{(prob.probability * 100).toFixed(1)}%</span>
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

      {/* Next Race Prediction — auto-generated by the training pipeline,
          separate from the manual what-if form above. */}
      <div className="dashboard-panel" style={{ maxWidth: '1200px', width: '100%', margin: '2rem auto 0' }}>
        <h2>Next Race Prediction</h2>
        {nextRaceLoading && <p>Loading next-race forecast...</p>}
        {nextRaceError && <p style={{ color: '#ff3b30' }}>{nextRaceError}</p>}
        {nextRace && nextRace.event && (
          <>
            <p style={{ marginBottom: '1rem' }}>
              <strong>{nextRace.event.name}</strong> — {nextRace.event.location}, {nextRace.event.country}
              {nextRace.event.date && (
                <> · {new Date(nextRace.event.date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</>
              )}
            </p>
            {!nextRace.forecast && (
              <p style={{ color: 'var(--f1-light-grey)' }}>
                No forecast cached yet — run the training pipeline to generate one.
              </p>
            )}
            {nextRace.forecast && (
              <>
                <p style={{ color: 'var(--f1-light-grey)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                  Grid positions are assumed from each driver's most recent race (real grid isn't
                  known until qualifying) — {nextRace.lastUpdated ? `forecast generated ${new Date(nextRace.lastUpdated).toLocaleString()}` : ''}
                </p>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--f1-grey)' }}>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Predicted</th>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Driver</th>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Team</th>
                      <th style={{ textAlign: 'left', padding: '0.5rem' }}>Assumed Grid</th>
                    </tr>
                  </thead>
                  <tbody>
                    {nextRace.forecast.map((f) => (
                      <tr key={f.abbreviation} style={{ borderBottom: '1px solid var(--f1-dark)' }}>
                        <td style={{ padding: '0.5rem' }}>P{f.predictedPosition}</td>
                        <td style={{ padding: '0.5rem' }}>{f.driver}</td>
                        <td style={{ padding: '0.5rem' }}>{f.team}</td>
                        <td style={{ padding: '0.5rem' }}>P{f.assumedGrid}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </>
        )}
        {nextRace && !nextRace.event && (
          <p style={{ color: 'var(--f1-light-grey)' }}>No upcoming race found on the calendar.</p>
        )}
      </div>

      <LiveTelemetry />

      {/* Lap View Modal Component */}
      <LapViewModal race={selectedRace} onClose={() => setSelectedRace(null)} />
    </>
  )
}

export default App
