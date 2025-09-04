import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Container,
  Typography,
  Card,
  CardContent,
  CardMedia,
  CircularProgress,
  Alert,
  Box,
  AppBar,
  Toolbar,
  ImageList,
  ImageListItem
} from '@mui/material';

export default function AircraftLookup() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('registration');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const addToHistory = (queryTerm, searchMode) => {
    setHistory((prev) => {
      // Don't duplicate same search/mode combo
      if (prev.find(item => item.value === queryTerm && item.mode === searchMode)) return prev;
      return [{ value: queryTerm, mode: searchMode }, ...prev].slice(0, 5);
    });
  };


  const handleSearch = async (e, customQuery, customMode) => {
    if (e) e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);

    try {
      const activeQuery = customQuery !== undefined ? customQuery : query;
      const activeMode = customMode !== undefined ? customMode : mode;
      const url = `/api/aircraft_lookup?${activeMode}=${encodeURIComponent(activeQuery)}`;
      const res = await fetch(url);
      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setResult(data.response || data);
        addToHistory(activeQuery, activeMode);
      }
    } catch {
      setError('Lookup failed. Please try again.');
    }
    setLoading(false);
  };



  return (
    <>
      <AppBar position="static" sx={{ mb: 3 }}>
        <Toolbar>
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{ flexGrow: 1, color: 'inherit', textDecoration: 'none' }}
          >
            Aircraft Lookup Tool
          </Typography>
          <Button color="inherit" component={Link} to="/">
            Home
          </Button>
          {/* Add future links here */}
        </Toolbar>
      </AppBar>

      <Container maxWidth="sm">
        <Typography variant="h4" gutterBottom align="center">
          ✈️ Aircraft Lookup
        </Typography>

        <Box component="form" onSubmit={handleSearch} sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <FormControl fullWidth>
            <InputLabel id="mode-select-label">Search Mode</InputLabel>
            <Select
              labelId="mode-select-label"
              value={mode}
              label="Search Mode"
              onChange={(e) => setMode(e.target.value)}
            >
              <MenuItem value="registration">Registration / Mode-S</MenuItem>
              <MenuItem value="callsign">Callsign</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            required
            label={mode === 'registration' ? 'Enter Registration or Hex' : 'Enter Callsign'}
            value={query}
            onChange={(e) => setQuery(e.target.value.toUpperCase())}
            autoFocus
          />

          <Button variant="contained" type="submit" disabled={loading}>
            Search
          </Button>

        </Box>

        {/*Displays recent searches */}
        {history.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1">Recent Searches:</Typography>
            {history.map((item, idx) => (
              <Button
                key={item.value + item.mode + idx}
                variant="outlined"
                sx={{ m: '0.25rem' }}
                onClick={async () => {
                  setQuery(item.value);
                  setMode(item.mode);
                  setTimeout(() => handleSearch(null, item.value, item.mode), 0);
                }}
              >
                {item.mode === "registration" ? "Reg:" : "Call:"} {item.value}
              </Button>
            ))}
          </Box>
        )}


        {/*Loading spinner */}
        {loading && (
          <Box textAlign="center" mb={2}>
            <CircularProgress />
          </Box>
        )}

        {/*Error Handler*/}
        {error && <Alert severity="error">{error}</Alert>}

        {result && (
          <Card sx={{ mt: 2 }}>
            <CardContent>
              {result.aircraft && (
                <>
                  <Typography variant="h6">Aircraft Info:</Typography>
                  <Typography>Registration: {result.aircraft.registration}</Typography>
                  <Typography>ICAO Type: {result.aircraft.icao_type}</Typography>
                  <Typography>Manufacturer: {result.aircraft.manufacturer}</Typography>
                  <Typography>Country: {result.aircraft.registered_owner_country}</Typography>
                  <Typography>Owner: {result.aircraft.registered_owner}</Typography>
                </>
              )}
              {result.flightroute && (
                <>
                  <Typography variant="h6" mt={2}>
                    Recent Route:
                  </Typography>
                  <Typography>Callsign: {result.flightroute.callsign}</Typography>
                  <Typography>
                    From: {result.flightroute.origin?.name} ({result.flightroute.origin?.iata_code})
                  </Typography>
                  <Typography>
                    To: {result.flightroute.destination?.name} ({result.flightroute.destination?.iata_code})
                  </Typography>
                  <Typography>Airline: {result.flightroute.airline?.name}</Typography>
                </>
              )}
            </CardContent>
            {result.aircraft?.url_photo && (
              <CardMedia
                component="img"
                sx={{ maxHeight: 200, objectFit: 'contain', my: 1 }}
                image={result.aircraft.url_photo}
                alt="Aircraft"
              />
            )}
            {result.aircraft && result.aircraft.photos && result.aircraft.photos.length > 0 ? (
              <ImageList rowHeight={160} cols={3}>
                {result.aircraft.photos.map((photoUrl, index) => (
                  <ImageListItem key={index}>
                    <img
                      src={photoUrl}
                      alt={`Aircraft tail number ${result.aircraft.registration} - view ${index + 1}`}
                      loading="lazy"
                      style={{ borderRadius: 8 }}
                    />
                  </ImageListItem>
                ))}
              </ImageList>
            ) : result.aircraft && result.aircraft.url_photo ? (
              <img
                src={result.aircraft.url_photo}
                alt="Aircraft"
                style={{ maxWidth: '100%', maxHeight: 200, borderRadius: 8, marginTop: 10 }}
              />
            ) : null}
          </Card>
        )}
        <Typography variant="caption" display="block" mt={3} textAlign="center" color="text.secondary">
          Data courtesy{' '}
          <a href="https://www.adsbdb.com" target="_blank" rel="noopener noreferrer">
            adsbdb.com
          </a>
        </Typography>
      </Container>
    </>
  );
}
