import React from "react";
import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div style={{ fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif" }}>
      {/* Navigation Bar */}
      <nav
        style={{
          backgroundColor: "#005DAA", // United blue
          padding: "1rem 2rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "white",
          boxShadow: "0 2px 6px rgba(0,0,0,0.15)"
        }}
      >
        <h1 style={{ margin: 0, fontWeight: "700" }}>Lookup</h1>
        <div style={{ display: "flex", gap: "1rem", fontWeight: "600" }}>
          <Link to="/" style={navLinkStyle}>
            Home
          </Link>
          <Link to="/lookup" style={navLinkStyle}>
            Aircraft Lookup
          </Link>
        </div>
      </nav>

      {/* Main Landing Content */}
      <main
        style={{
          textAlign: "center",
          padding: "4rem 2rem",
          backgroundColor: "#F7F9FB", // light gray-blue background
          minHeight: "calc(100vh - 72px)" // full height minus nav height
        }}
      >
        <h2
          style={{
            color: "#005DAA",
            fontWeight: 700,
            fontSize: "2.5rem",
            marginBottom: "1rem"
          }}
        >
          Welcome to the Aviation Lookup Tool! A Personal project of Mine!
        </h2>
        <p
          style={{
            fontSize: "1.25rem",
            maxWidth: "600px",
            margin: "0 auto 2rem",
            color: "#333"
          }}
        >
          Experience aviation details with our interactive lookup tool.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: "2rem",marginBottom: "1rem" }}>
          <Link to="/lookup" style={buttonStyle}>
            Aircraft Lookup
          </Link>
        </div>
        <div style={{ display: "flex", justifyContent: "center", gap: "2rem",marginBottom: "1rem" }}>
          <Link to="/airport" style={buttonStyle}>
            Airport Lookup
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer
        style={{
          backgroundColor: "#00326B", // darker United blue
          color: "white",
          padding: "1rem 2rem",
          textAlign: "center",
          fontSize: "0.875rem"
        }}
      >
        <p style={{ margin: 0 }}>
          &copy; {new Date().getFullYear()} Aircraft Lookup. Data powered by{" "}
          <a
            href="https://www.adsbdb.com"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#70B5F9" }}
          >
            ADSBdb
          </a>
          . Made with 💙 for aviation enthusiasts.
        </p>
      </footer>
    </div>
  );
}

const navLinkStyle = {
  color: "white",
  textDecoration: "none",
  padding: "0.5rem 0.75rem",
  borderRadius: "4px",
  transition: "background-color 0.3s",
  cursor: "pointer"
};

const buttonStyle = {
  backgroundColor: "#005DAA", // United blue
  color: "white",
  padding: "0.75rem 1.5rem",
  borderRadius: "6px",
  textDecoration: "none",
  fontWeight: "600",
  fontSize: "1rem",
  boxShadow: "0 3px 8px rgba(0, 93, 170, 0.45)",
  transition: "background-color 0.3s",
  cursor: "pointer"
};
