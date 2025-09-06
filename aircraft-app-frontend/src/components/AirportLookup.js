import React, { useState } from "react";
import {
  Container,
  Typography,
  TextField,
  Button,
//   CircularProgress,
  Alert,
  Card,
  CardContent,
  Box,
} from "@mui/material";

export default function AirportLookup() {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!code) {
      setError("Please enter an airport ICAO or IATA code.");
      return;
    }
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const res = await fetch(`/api/airport_lookup?code=${encodeURIComponent(code.toUpperCase())}`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
      } else {
        setResult(data.response || data);
      }
    } catch {
      setError("Failed to fetch airport data.");
    }
    setLoading(false);
  };

  return (
    <Container sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Airport Lookup 🛫</Typography>
      <form onSubmit={handleSearch}>
        <TextField
          label="Enter Airport ICAO or IATA Code (e.g., KSFO, SFO)"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          fullWidth
          sx={{ mb: 2 }}
          autoFocus
        />
        <Button variant="contained" fullWidth type="submit" disabled={loading}>
          {loading ? "Loading..." : "Search"}
        </Button>
      </form>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      {result && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6">{result.name || result.airportName || "Airport Name"}</Typography>
            <Typography>Code: {result.iata || result.icao || code.toUpperCase()}</Typography>
            <Typography>Airport: {result.name || "N/A"}</Typography>
            <Typography>City: {result.location || "N/A"}</Typography>
            <Typography>Country: {result.country || "N/A"}</Typography>
            <Typography>Latitude: {result.latitude || "N/A"}</Typography>
            <Typography>Longitude: {result.longitude || "N/A"}</Typography>
            <Typography>Link: <a href={result.link} target="_blank" rel="noopener noreferrer">{result.link || "N/A"}</a></Typography>
            {/* Add more info as available */}
          </CardContent>
        </Card>
      )}
      <Box mt={2} fontSize="small" color="text.secondary" textAlign="center">
        Data courtesy <a href="https://airport-data.com/" target="_blank" rel="noopener noreferrer">airport-data.com</a>
      </Box>
    </Container>
  );
}
