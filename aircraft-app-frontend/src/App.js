import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './components/Home';
/*{import Arrivals from './components/Arrivals';
import Departures from './components/Departures'; */
import AircraftLookup from './components/AircraftLookup';
import AirportLookup from './components/AirportLookup';
import DelayPredictor from './components/DelayPredictor';
import AIAgentChat from './components/AIAgentChat';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        {/*<Route path="/arrivals" element={<Arrivals />} />   NOT IN USE
        <Route path="/departures" element={<Departures />} />  NOT IN USE*/}
        <Route path="/lookup" element={<AircraftLookup />} />
        <Route path="/airport" element={<AirportLookup />} />
        <Route path="/delay" element={<DelayPredictor />} />
        <Route path="/chat" element={<AIAgentChat />} />
        
      </Routes>
    </Router>
  );
}

export default App;

