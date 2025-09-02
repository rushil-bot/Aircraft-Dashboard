import React from 'react';
import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>San Francisco International Airport Flight Dashboard</h1>
      <nav style={{ marginBottom: '20px' }}>
        <Link to="/arrivals" style={{ marginRight: '15px' }}>Arrivals</Link>
        <Link to="/departures">Departures</Link>
      </nav>
      <p>
        Welcome to the flight dashboard. Select Arrivals or Departures to view current flight information.
      </p>
    </div>
  );
}
