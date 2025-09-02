import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './components/Home';
import Arrivals from './components/Arrivals';
import Departures from './components/Departures';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/arrivals" element={<Arrivals />} />
        <Route path="/departures" element={<Departures />} />
      </Routes>
    </Router>
  );
}

export default App;

