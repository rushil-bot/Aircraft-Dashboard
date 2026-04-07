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
  CircularProgress,
  LinearProgress,
  Chip
} from "@mui/material";

const AIRLINE_NAMES = {
  AA: "American Airlines",
  DL: "Delta Air Lines",
  UA: "United Airlines",
  WN: "Southwest Airlines",
  B6: "JetBlue Airways",
  AS: "Alaska Airlines",
  NK: "Spirit Airlines",
  F9: "Frontier Airlines",
  G4: "Allegiant Air",
  HA: "Hawaiian Airlines",
  SY: "Sun Country Airlines",
  VX: "Virgin America",
  OO: "SkyWest Airlines",
  YX: "Republic Airways",
  MQ: "Envoy Air",
  OH: "PSA Airlines",
  YV: "Mesa Airlines",
  "9E": "Endeavor Air",
  PT: "Piedmont Airlines",
  CP: "Compass Airlines"
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const DAYS = [
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
  { value: 7, label: "Sunday" }
];

function getRiskColor(prob) {
  if (prob < 0.30) return { bg: "#e8f5e9", border: "#4caf50", text: "#2e7d32", bar: "#4caf50" };
  if (prob < 0.60) return { bg: "#fff8e1", border: "#ff9800", text: "#e65100", bar: "#ff9800" };
  return { bg: "#ffebee", border: "#f44336", text: "#c62828", bar: "#f44336" };
}

export default function RouteRecommender() {
  const today = new Date();
  const [formData, setFormData] = useState({
    origin: "",
    dest: "",
    month: today.getMonth() + 1,
    day_of_week: today.getDay() || 7,
    top_n: 5
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    if (!formData.origin || !formData.dest) {
      setError("Please enter both an origin and destination airport code.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/agents/route-recommender/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin: formData.origin.trim().toUpperCase(),
          dest: formData.dest.trim().toUpperCase(),
          month: parseInt(formData.month),
          day_of_week: parseInt(formData.day_of_week),
          top_n: parseInt(formData.top_n)
        })
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "Failed to retrieve recommendations. The service may be unavailable.");
      } else {
        setResult(data);
      }
    } catch (err) {
      setError("Network error. Could not connect to the Route Recommender service.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AppBar position="static" sx={{ mb: 3, backgroundColor: "#6d28d9" }}>
        <Toolbar>
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{ flexGrow: 1, color: "inherit", textDecoration: "none", fontWeight: "700" }}
          >
            AI Route Recommender
          </Typography>
          <Button color="inherit" component={Link} to="/">
            Home
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="md">
        <Box textAlign="center" mb={4}>
          <Typography variant="h3" fontWeight="700" color="#6d28d9" gutterBottom>
            Route Recommender
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Find the best airline and departure time for your route. Rankings are powered by a
            LightGBM model trained on millions of BTS flight records.
          </Typography>
        </Box>

        <Card sx={{ boxShadow: "0 8px 24px rgba(0,0,0,0.12)", borderRadius: "12px", mb: 4 }}>
          <CardContent sx={{ p: 4 }}>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Origin Airport (e.g. SFO)"
                    name="origin"
                    value={formData.origin}
                    onChange={handleChange}
                    placeholder="SFO"
                    inputProps={{ maxLength: 4 }}
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
                    inputProps={{ maxLength: 4 }}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    select
                    fullWidth
                    label="Month"
                    name="month"
                    value={formData.month}
                    onChange={handleChange}
                  >
                    {MONTHS.map((name, i) => (
                      <MenuItem key={i + 1} value={i + 1}>{name}</MenuItem>
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
                    {DAYS.map((d) => (
                      <MenuItem key={d.value} value={d.value}>{d.label}</MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    select
                    fullWidth
                    label="Results to Show"
                    name="top_n"
                    value={formData.top_n}
                    onChange={handleChange}
                  >
                    {[3, 5, 7, 10].map((n) => (
                      <MenuItem key={n} value={n}>Top {n}</MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12}>
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={loading}
                    sx={{ py: 1.5, fontSize: "1.2rem", fontWeight: "bold", backgroundColor: "#6d28d9",
                      "&:hover": { backgroundColor: "#5b21b6" } }}
                  >
                    {loading ? <CircularProgress size={28} color="inherit" /> : "Find Best Routes"}
                  </Button>
                </Grid>
              </Grid>
            </form>
          </CardContent>
        </Card>

        {error && (
          <Alert severity="error" sx={{ mb: 4, borderRadius: "8px" }}>{error}</Alert>
        )}

        {result && (
          <Box>
            <Typography variant="h5" fontWeight="700" color="#6d28d9" gutterBottom>
              {result.origin} to {result.dest} — Top Recommendations
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              {result.model_note}
            </Typography>

            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {result.recommendations.map((rec) => {
                const colors = getRiskColor(rec.delay_probability);
                return (
                  <Card
                    key={rec.rank}
                    sx={{
                      borderRadius: "10px",
                      border: `2px solid ${colors.border}`,
                      backgroundColor: colors.bg,
                      boxShadow: "0 2px 8px rgba(0,0,0,0.07)"
                    }}
                  >
                    <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1.5 }}>
                        <Chip
                          label={`#${rec.rank}`}
                          size="small"
                          sx={{ backgroundColor: colors.border, color: "white", fontWeight: "700" }}
                        />
                        <Box>
                          <Typography variant="h6" fontWeight="700" color={colors.text} lineHeight={1.2}>
                            {AIRLINE_NAMES[rec.airline] || rec.airline}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {rec.airline}
                          </Typography>
                        </Box>
                        <Typography variant="body1" color="text.secondary" sx={{ ml: "auto" }}>
                          {rec.label}
                        </Typography>
                      </Box>

                      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={rec.delay_probability * 100}
                          sx={{
                            flexGrow: 1,
                            height: 8,
                            borderRadius: 4,
                            backgroundColor: "#e0e0e0",
                            "& .MuiLinearProgress-bar": { backgroundColor: colors.bar }
                          }}
                        />
                        <Typography variant="body2" fontWeight="700" color={colors.text} sx={{ minWidth: 48 }}>
                          {(rec.delay_probability * 100).toFixed(1)}%
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                );
              })}
            </Box>
          </Box>
        )}
      </Container>
    </>
  );
}
