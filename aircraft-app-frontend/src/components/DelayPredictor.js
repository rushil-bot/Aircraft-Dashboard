import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  Box,
  AppBar,
  Toolbar,
  Grid,
  MenuItem,
  CircularProgress
} from "@mui/material";

export default function DelayPredictor() {
  const [formData, setFormData] = useState({
    month: new Date().getMonth() + 1,
    day_of_week: new Date().getDay() || 7, // 1-7 (Mon-Sun)
    dep_hour: new Date().getHours(),
    reporting_airline: "",
    origin: "",
    dest: "",
    distance: ""
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    // Basic validation
    if (!formData.reporting_airline || !formData.origin || !formData.dest || !formData.distance) {
      setError("Please fill out all fields.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/agents/delay-predictor/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          month: parseInt(formData.month),
          day_of_week: parseInt(formData.day_of_week),
          dep_hour: parseInt(formData.dep_hour),
          reporting_airline: formData.reporting_airline.trim().toUpperCase(),
          origin:  formData.origin.trim().toUpperCase(),
          dest: formData.dest.trim().toUpperCase(),
          distance: parseInt(formData.distance)
        })
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Failed to predict delay. The AI model Service may be down.");
      } else {
        setResult(data);
      }
    } catch (err) {
      setError("Network error. Could not connect to the Prediction Agent.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AppBar position="static" sx={{ mb: 3, backgroundColor: "#005DAA" }}>
        <Toolbar>
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{ flexGrow: 1, color: "inherit", textDecoration: "none", fontWeight: "700" }}
          >
            Flight Delay AI Predictor
          </Typography>
          <Button color="inherit" component={Link} to="/">
            Home
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md">
        <Box textAlign="center" mb={4}>
          <Typography variant="h3" fontWeight="700" color="#005DAA" gutterBottom>
            🤖 AI Delay Predictor
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Predict the probability of a 15+ minute delay using our cutting-edge Machine Learning model trained on millions of flights.
          </Typography>
        </Box>

        <Card sx={{ boxShadow: "0 8px 24px rgba(0,0,0,0.12)", borderRadius: "12px", mb: 4 }}>
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    select
                    fullWidth
                    label="Month"
                    name="month"
                    value={formData.month}
                    onChange={handleChange}
                  >
                    {[...Array(12)].map((_, i) => (
                      <MenuItem key={i + 1} value={i + 1}>
                        {new Date(0, i).toLocaleString('default', { month: 'long' })}
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    select
                    fullWidth
                    label="Day of Week"
                    name="day_of_week"
                    value={formData.day_of_week}
                    onChange={handleChange}
                  >
                    <MenuItem value={1}>Monday</MenuItem>
                    <MenuItem value={2}>Tuesday</MenuItem>
                    <MenuItem value={3}>Wednesday</MenuItem>
                    <MenuItem value={4}>Thursday</MenuItem>
                    <MenuItem value={5}>Friday</MenuItem>
                    <MenuItem value={6}>Saturday</MenuItem>
                    <MenuItem value={7}>Sunday</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    select
                    fullWidth
                    label="Departure Hour"
                    name="dep_hour"
                    value={formData.dep_hour}
                    onChange={handleChange}
                  >
                    {[...Array(24)].map((_, i) => (
                      <MenuItem key={i} value={i}>
                        {i}:00 - {i}:59
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Airline Code (e.g. UA, AA, WN)"
                    name="reporting_airline"
                    value={formData.reporting_airline}
                    onChange={handleChange}
                    placeholder="UA"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Flight Distance (miles)"
                    name="distance"
                    type="number"
                    value={formData.distance}
                    onChange={handleChange}
                    placeholder="2586"
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Origin Airport (e.g. SFO)"
                    name="origin"
                    value={formData.origin}
                    onChange={handleChange}
                    placeholder="SFO"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Destination Airport (e.g. JFK)"
                    name="dest"
                    value={formData.dest}
                    onChange={handleChange}
                    placeholder="JFK"
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button 
                    type="submit" 
                    variant="contained" 
                    size="large" 
                    fullWidth 
                    disabled={loading}
                    sx={{ py: 1.5, fontSize: "1.2rem", fontWeight: "bold", backgroundColor: "#005DAA" }}
                  >
                    {loading ? <CircularProgress size={28} color="inherit" /> : "Analyze Flight Risk"}
                  </Button>
                </Grid>
              </Grid>
            </form>
          </CardContent>
        </Card>

        {error && <Alert severity="error" sx={{ mb: 4, borderRadius: "8px" }}>{error}</Alert>}

        {result && (
          <Box 
            sx={{ 
              p: 4, 
              borderRadius: "12px", 
              textAlign: "center",
              backgroundColor: result.is_delayed ? "#ffebee" : "#e8f5e9",
              border: `2px solid ${result.is_delayed ? "#f44336" : "#4caf50"}`,
              boxShadow: "0 4px 12px rgba(0,0,0,0.05)"
            }}
          >
            <Typography variant="h4" fontWeight="bold" color={result.is_delayed ? "#d32f2f" : "#2e7d32"} gutterBottom>
              {result.is_delayed ? "High Risk of Delay ⚠️" : "Likely On-Time ✅"}
            </Typography>
            
            <Box sx={{ my: 3 }}>
              <Typography variant="h2" fontWeight="900" color={result.is_delayed ? "#d32f2f" : "#2e7d32"}>
                {(result.delay_probability * 100).toFixed(1)}%
              </Typography>
              <Typography variant="subtitle1" color="text.secondary">
                Probability of a 15+ minute delay
              </Typography>
            </Box>

            <Typography variant="body2" color="text.secondary">
              {result.feature_importance_note}
            </Typography>
          </Box>
        )}
      </Container>
    </>
  );
}
