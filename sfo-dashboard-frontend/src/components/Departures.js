import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function Departures() {
  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/departures')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        setFlights(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading departures...</div>;
  if (error) return <div>Error loading departures: {error}</div>;

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>SFO Departures</h1>
      <nav style={{ marginBottom: '20px' }}>
        <Link to="/" style={{ marginRight: '15px' }}>Home</Link>
        <Link to="/arrivals">Arrivals</Link>
      </nav>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr style={{ backgroundColor: '#f2f2f2' }}>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Airline</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Flight</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Destination</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Status</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Scheduled</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Actual</th>
            <th style={{ border: '1px solid #ddd', padding: '8px' }}>Gate</th>
          </tr>
        </thead>
        <tbody>
          {flights.map(flight => (
            <tr key={flight.id}>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.airline}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.flight}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.origin}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.status}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.scheduled_time}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.actual_time}</td>
              <td style={{ border: '1px solid #ddd', padding: '8px' }}>{flight.gate}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
