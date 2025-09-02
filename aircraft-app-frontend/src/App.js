import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './components/Home';
/*{import Arrivals from './components/Arrivals';
import Departures from './components/Departures'; */
import AircraftLookup from './components/AircraftLookup';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        {/*<Route path="/arrivals" element={<Arrivals />} />   NOT IN USE
        <Route path="/departures" element={<Departures />} />  NOT IN USE*/}
        <Route path="/lookup" element={<AircraftLookup />} />
      </Routes>
    </Router>
  );
}

export default App;

