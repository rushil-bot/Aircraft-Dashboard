import React, { useState } from 'react';
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
} from '@mui/material';

export default function AircraftLookup() {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('registration');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);

    try {
      const url = `/api/aircraft_lookup?${mode}=${encodeURIComponent(query)}`;
      const res = await fetch(url);
      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setResult(data.response || data);
      }
    } catch {
      setError('Lookup failed. Please try again.');
    }
    setLoading(false);
  };

  return (
    
    <Container maxWidth="sm" sx={{ mt: 4 }}>
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
            onChange={(e) => setMode(e.target.value)}>
            <MenuItem value="registration">Registration / Mode-S</MenuItem>
            <MenuItem value="callsign">Callsign</MenuItem>
          </Select>
        </FormControl>

        <TextField
          fullWidth
          required
          value={query}
          onChange={(e) => setQuery(e.target.value.toUpperCase())}
          label={mode === 'registration' ? 'Enter Registration or Hex' : 'Enter Callsign'}
          autoFocus
        />

        <Button variant="contained" type="submit" disabled={loading}>
          Search
        </Button>
      </Box>

      {loading && (
        <Box textAlign="center" mb={2}>
          <CircularProgress />
        </Box>
      )}

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
        </Card>
      )}

      <Typography variant="caption" display="block" mt={3} textAlign="center" color="text.secondary">
        Data courtesy{' '}
        <a href="https://www.adsbdb.com" target="_blank" rel="noopener noreferrer">
          adsbdb.com
        </a>
      </Typography>
    </Container>
  );
}
